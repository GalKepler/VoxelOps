"""QSIPrep diffusion preprocessing runner."""

import os
from pathlib import Path
from typing import Any

from voxelops.runners._base import (
    _get_default_log_dir,
    run_docker,
    validate_input_dir,
    validate_participant,
)
from voxelops.schemas.qsiprep import (
    QSIPrepDefaults,
    QSIPrepInputs,
    QSIPrepOutputs,
)


def _build_qsiprep_docker_command(
    inputs: QSIPrepInputs,
    config: QSIPrepDefaults,
    output_dir: Path,
    work_dir: Path,
) -> list[str]:
    """Builds the Docker command for QSIPrep."""
    uid = os.getuid()
    gid = os.getgid()

    cmd = [
        "docker",
        "run",
        "--rm",
        "--user",
        f"{uid}:{gid}",
        "-v",
        f"{inputs.bids_dir}:/data:ro",
        "-v",
        f"{output_dir}:/out",
        "-v",
        f"{work_dir}:/work",
    ]

    # Add FreeSurfer license if provided
    if config.fs_license and config.fs_license.exists():
        cmd.extend(["-v", f"{config.fs_license}:/license.txt:ro"])
    # Add BIDS filters if provided
    if inputs.bids_filters and inputs.bids_filters.exists():
        cmd.extend(["-v", f"{inputs.bids_filters}:/bids_filters.json:ro"])

    # Container image
    cmd.append(config.docker_image)

    # QSIPrep arguments
    cmd.extend(
        [
            "/data",
            "/out",
            "participant",
            "--participant-label",
            inputs.participant,
            "--output-resolution",
            str(config.output_resolution),
            "--nprocs",
            str(config.nprocs),
            "--mem-mb",
            str(config.mem_mb),
            "--work-dir",
            "/work",
        ]
    )

    # Output spaces
    for space in config.anatomical_template:
        cmd.extend(["--anatomical-template", space])

    # Optional flags
    if config.longitudinal:
        cmd.append("--longitudinal")

    # Optional subject anatomical reference
    if (
        hasattr(config, "subject_anatomical_reference")
        and config.subject_anatomical_reference
    ):
        cmd.extend(
            ["--subject-anatomical-reference", config.subject_anatomical_reference]
        )

    if config.skip_bids_validation:
        cmd.append("--skip-bids-validation")

    if config.fs_license and config.fs_license.exists():
        cmd.extend(["--fs-license-file", "/license.txt"])

    if inputs.bids_filters and inputs.bids_filters.exists():
        cmd.extend(["--bids-filter-file", "/bids_filters.json"])

    return cmd


def run_qsiprep(
    inputs: QSIPrepInputs,
    config: QSIPrepDefaults | None = None,
    log_dir: Path | None = None,
    **overrides,
) -> dict[str, Any]:
    """Run QSIPrep diffusion MRI preprocessing.

    Parameters
    ----------
    inputs : QSIPrepInputs
        Required inputs (bids_dir, participant, etc.).
    config : Optional[QSIPrepDefaults], optional
        Configuration (uses brain bank defaults if not provided), by default None.
    log_dir : Path, optional
        Directory for audit logs. Defaults to inputs.output_dir/logs.
    **overrides
        Override any config parameter (e.g., nprocs=16).

    Returns
    -------
    Dict[str, Any]
        Execution record with:
            - tool: "qsiprep"
            - participant: Participant label
            - command: Full Docker command executed
            - exit_code: Process exit code
            - start_time, end_time: ISO format timestamps
            - duration_seconds, duration_human: Execution duration
            - success: Boolean success status
            - log_file: Path to JSON log
            - inputs: QSIPrepInputs instance
            - config: QSIPrepDefaults instance
            - expected_outputs: QSIPrepOutputs instance

    Raises
    ------
    InputValidationError
        If inputs are invalid.
    ProcedureExecutionError
        If preprocessing fails.

    Examples
    --------
    >>> inputs = QSIPrepInputs(
    ...     bids_dir=Path("/data/bids"),
    ...     participant="01",
    ... )
    >>> result = run_qsiprep(inputs, nprocs=16)  # Override default nprocs
    >>> print(f"Completed in {result['duration_human']}")
    >>> print(f"Outputs in: {result['expected_outputs'].qsiprep_dir}")
    """
    log_dir = log_dir or _get_default_log_dir(inputs)

    # Use brain bank defaults if config not provided
    config = config or QSIPrepDefaults()

    # Apply overrides
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)

    # Validate inputs
    validate_input_dir(inputs.bids_dir, "BIDS")
    validate_participant(inputs.bids_dir, inputs.participant)

    # Setup directories
    output_dir = inputs.output_dir or (inputs.bids_dir.parent / "derivatives")
    work_dir = inputs.work_dir or (output_dir.parent / "work" / "qsiprep")
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    # Generate expected outputs
    expected_outputs = QSIPrepOutputs.from_inputs(inputs, output_dir, work_dir)

    # Check if outputs already exist and skip if not forcing
    if expected_outputs.exist() and not config.force:
        print("\n" + "=" * 80)
        print(f"✓ QSIPrep outputs already exist for participant {inputs.participant}")
        print(f"  Participant dir: {expected_outputs.participant_dir}")
        print(f"  HTML report: {expected_outputs.html_report}")
        print("  Use force=True to re-run")
        print("=" * 80 + "\n")

        return {
            "tool": "qsiprep",
            "participant": inputs.participant,
            "skipped": True,
            "reason": "outputs_exist",
            "success": True,
            "inputs": inputs,
            "config": config,
            "expected_outputs": expected_outputs,
        }

    # Build Docker command
    cmd = _build_qsiprep_docker_command(inputs, config, output_dir, work_dir)

    # Execute

    result = run_docker(
        cmd=cmd,
        tool_name="qsiprep",
        participant=inputs.participant,
        log_dir=log_dir,
    )

    # Add inputs, config, and expected outputs to result
    result["inputs"] = inputs
    result["config"] = config
    result["expected_outputs"] = expected_outputs
    result["skipped"] = False

    return result
