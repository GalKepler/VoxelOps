"""HeudiConv DICOM to BIDS converter runner."""

from pathlib import Path
from typing import Dict, Optional, Any

from voxelops.runners._base import run_docker, validate_input_dir
from voxelops.schemas.heudiconv import (
    HeudiconvInputs,
    HeudiconvOutputs,
    HeudiconvDefaults,
)
from voxelops.exceptions import InputValidationError


def run_heudiconv(
    inputs: HeudiconvInputs,
    config: Optional[HeudiconvDefaults] = None,
    **overrides
) -> Dict[str, Any]:
    """Convert DICOM to BIDS using HeudiConv.

    Args:
        inputs: Required inputs (dicom_dir, participant, etc.)
        config: Configuration (uses defaults if not provided)
        **overrides: Override any config parameter

    Returns:
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

    Raises:
        InputValidationError: If inputs are invalid
        ProcedureExecutionError: If conversion fails

    Example:
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
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{inputs.dicom_dir}:/dicom:ro",
        "-v", f"{output_dir}:/output",
        "-v", f"{config.heuristic}:/heuristic.py:ro",
        config.docker_image,
        "--files", "/dicom",
        "--outdir", "/output",
        "--subjs", inputs.participant,
        "--converter", config.converter,
        "--heuristic", "/heuristic.py",
    ]

    if inputs.session:
        cmd.extend(["--ses", inputs.session])

    if config.overwrite:
        cmd.append("--overwrite")

    if config.bids_validator:
        cmd.append("--bids")

    # Execute
    log_dir = output_dir.parent / "logs"
    result = run_docker(
        cmd=cmd,
        tool_name="heudiconv",
        participant=inputs.participant,
        log_dir=log_dir,
    )

    # Add inputs, config, and expected outputs to result
    result['inputs'] = inputs
    result['config'] = config
    result['expected_outputs'] = expected_outputs

    return result
