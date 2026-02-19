"""HeudiConv DICOM to BIDS converter runner."""

import os
from pathlib import Path
from typing import Any

from voxelops.exceptions import InputValidationError
from voxelops.runners._base import run_docker, validate_input_dir
from voxelops.schemas.heudiconv import (
    HeudiconvDefaults,
    HeudiconvInputs,
    HeudiconvOutputs,
)
from voxelops.utils.bids import post_process_heudiconv_output


def _build_heudiconv_docker_command(
    inputs: HeudiconvInputs, config: HeudiconvDefaults, output_dir: Path
) -> list[str]:
    """Builds the Docker command for HeudiConv."""
    uid = os.getuid()
    gid = os.getgid()

    cmd = [
        "docker",
        "run",
        "--rm",
        "--user",
        f"{uid}:{gid}",
        "-v",
        f"{inputs.dicom_dir}:/dicom:ro",
        "-v",
        f"{output_dir}:/output",
        "-v",
        f"{config.heuristic}:/heuristic.py:ro",
        config.docker_image,
        "--files",
        "/dicom",
        "--outdir",
        "/output",
        "--subjects",
        inputs.participant,
        "--converter",
        config.converter,
        "--heuristic",
        "/heuristic.py",
    ]

    if inputs.session:
        cmd.extend(["--ses", inputs.session])

    if config.overwrite:
        cmd.append("--overwrite")

    if config.bids_validator:
        cmd.append("--bids")

    if inputs.bids:
        cmd.extend(["--bids", inputs.bids])

    if inputs.grouping:
        cmd.extend(["--grouping", inputs.grouping])
    return cmd


def _handle_heudiconv_post_processing(
    result: dict[str, Any],
    config: HeudiconvDefaults,
    output_dir: Path,
    inputs: HeudiconvInputs,
) -> dict[str, Any]:
    """Handles post-processing steps for HeudiConv."""
    if result["success"] and config.post_process:
        print(f"\n{'='*80}")
        print(f"Running post-HeudiConv processing for participant {inputs.participant}")
        print(f"{'='*80}\n")

        try:
            post_result = post_process_heudiconv_output(
                bids_dir=output_dir,
                participant=inputs.participant,
                session=inputs.session,
                dry_run=config.post_process_dry_run,
            )
            result["post_processing"] = post_result

            if not post_result["success"]:
                print("\n⚠ Post-processing completed with warnings:")
                for error in post_result.get("errors", []):
                    print(f"  - {error}")
            else:
                print("\n✓ Post-processing completed successfully")

        except Exception as e:
            print(f"\n⚠ Post-processing failed: {e}")
            result["post_processing"] = {"success": False, "error": str(e)}
            # Don't fail the entire conversion if post-processing fails
    return result


def run_heudiconv(
    inputs: HeudiconvInputs, config: HeudiconvDefaults | None = None, **overrides
) -> dict[str, Any]:
    """Convert DICOM to BIDS using HeudiConv.

    Parameters
    ----------
    inputs : HeudiconvInputs
        Required inputs (dicom_dir, participant, etc.).
    config : Optional[HeudiconvDefaults], optional
        Configuration (uses defaults if not provided), by default None.
    **overrides
        Override any config parameter.

    Returns
    -------
    Dict[str, Any]
        Execution record with:
            - tool: "heudiconv"
            - participant: Participant label
            - command: Full Docker command executed
            - exit_code: Process exit code
            - start_time, end_time: ISO format timestamps
            - duration_seconds, duration_human: Execution duration
            - success: Boolean success status
            - log_file: Path to JSON log
            - inputs: HeudiconvInputs instance
            - config: HeudiconvDefaults instance
            - expected_outputs: HeudiconvOutputs instance

    Raises
    ------
    InputValidationError
        If inputs are invalid.
    ProcedureExecutionError
        If conversion fails.

    Examples
    --------
    >>> inputs = HeudiconvInputs(
    ...     dicom_dir=Path("/data/dicoms"),
    ...     participant="01",
    ... )
    >>> config = HeudiconvDefaults(
    ...     heuristic=Path("/code/heuristic.py"),
    ... )
    >>> result = run_heudiconv(inputs, config)
    >>> print(result['expected_outputs'].bids_dir)
    PosixPath('/data/bids')
    """
    # Use defaults if config not provided
    config = config or HeudiconvDefaults()

    # Apply overrides
    for key, value in overrides.items():
        if hasattr(config, key):
            print(f"Overriding config.{key} with value: {value}")
            setattr(config, key, value)

    # Validate inputs
    validate_input_dir(inputs.dicom_dir, "DICOM")

    if not config.heuristic:
        raise InputValidationError(
            "Heuristic file is required for HeudiConv. "
            "Provide it via config.heuristic or heuristic= keyword argument."
        )

    if not config.heuristic.exists():
        raise InputValidationError(f"Heuristic file not found: {config.heuristic}")

    # Setup output directory
    output_dir = inputs.output_dir or (inputs.dicom_dir.parent / "bids")
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate expected outputs
    expected_outputs = HeudiconvOutputs.from_inputs(inputs, output_dir)

    # Build Docker command
    cmd = _build_heudiconv_docker_command(inputs, config, output_dir)

    # Execute
    log_dir = output_dir.parent / "logs"
    result = run_docker(
        cmd=cmd,
        tool_name="heudiconv",
        participant=inputs.participant,
        log_dir=log_dir,
    )

    # Post-processing steps
    result = _handle_heudiconv_post_processing(result, config, output_dir, inputs)

    # Add inputs, config, and expected outputs to result
    result["inputs"] = inputs
    result["config"] = config
    result["expected_outputs"] = expected_outputs

    return result
