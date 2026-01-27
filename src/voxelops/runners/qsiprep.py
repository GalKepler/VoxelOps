"""QSIPrep diffusion preprocessing runner."""

from pathlib import Path
from typing import Dict, Optional, Any

from voxelops.runners._base import (
    run_docker,
    validate_input_dir,
    validate_participant,
)
from voxelops.schemas.qsiprep import (
    QSIPrepInputs,
    QSIPrepOutputs,
    QSIPrepDefaults,
)


def run_qsiprep(
    inputs: QSIPrepInputs,
    config: Optional[QSIPrepDefaults] = None,
    **overrides
) -> Dict[str, Any]:
    """Run QSIPrep diffusion MRI preprocessing.

    Args:
        inputs: Required inputs (bids_dir, participant, etc.)
        config: Configuration (uses brain bank defaults if not provided)
        **overrides: Override any config parameter (e.g., nprocs=16)

    Returns:
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

    Raises:
        InputValidationError: If inputs are invalid
        ProcedureExecutionError: If preprocessing fails

    Example:
        >>> inputs = QSIPrepInputs(
        ...     bids_dir=Path("/data/bids"),
        ...     participant="01",
        ... )
        >>> result = run_qsiprep(inputs, nprocs=16)  # Override default nprocs
        >>> print(f"Completed in {result['duration_human']}")
        >>> print(f"Outputs in: {result['expected_outputs'].qsiprep_dir}")
    """
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

    # Build Docker command
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{inputs.bids_dir}:/data:ro",
        "-v", f"{output_dir}:/out",
        "-v", f"{work_dir}:/work",
    ]

    # Add FreeSurfer license if provided
    if config.fs_license and config.fs_license.exists():
        cmd.extend(["-v", f"{config.fs_license}:/license.txt:ro"])

    # Container image
    cmd.append(config.docker_image)

    # QSIPrep arguments
    cmd.extend([
        "/data", "/out", "participant",
        f"--participant-label={inputs.participant}",
        f"--nprocs={config.nprocs}",
        f"--mem-gb={config.mem_gb}",
        f"--output-resolution={config.output_resolution}",
        "--work-dir=/work",
    ])

    # Output spaces
    for space in config.output_spaces:
        cmd.append(f"--output-space={space}")

    # Optional flags
    if config.longitudinal:
        cmd.append("--longitudinal")

    if config.skip_bids_validation:
        cmd.append("--skip-bids-validation")

    if config.fs_license and config.fs_license.exists():
        cmd.append("--fs-license-file=/license.txt")

    # Execute
    log_dir = output_dir.parent / "logs"
    result = run_docker(
        cmd=cmd,
        tool_name="qsiprep",
        participant=inputs.participant,
        log_dir=log_dir,
    )

    # Add inputs, config, and expected outputs to result
    result['inputs'] = inputs
    result['config'] = config
    result['expected_outputs'] = expected_outputs

    return result
