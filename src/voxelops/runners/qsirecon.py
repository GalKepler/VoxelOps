"""QSIRecon diffusion reconstruction runner."""

from pathlib import Path
from typing import Dict, Optional, Any

from voxelops.runners._base import (
    run_docker,
    validate_input_dir,
    validate_participant,
)
from voxelops.schemas.qsirecon import (
    QSIReconInputs,
    QSIReconOutputs,
    QSIReconDefaults,
)


def run_qsirecon(
    inputs: QSIReconInputs,
    config: Optional[QSIReconDefaults] = None,
    **overrides
) -> Dict[str, Any]:
    """Run QSIRecon diffusion reconstruction and connectivity.

    Args:
        inputs: Required inputs (qsiprep_dir, participant, etc.)
        config: Configuration (uses brain bank defaults if not provided)
        **overrides: Override any config parameter

    Returns:
        Execution record with:
            - tool: "qsirecon"
            - participant: Participant label
            - command: Full Docker command executed
            - exit_code: Process exit code
            - start_time, end_time: ISO format timestamps
            - duration_seconds, duration_human: Execution duration
            - success: Boolean success status
            - log_file: Path to JSON log
            - inputs: QSIReconInputs instance
            - config: QSIReconDefaults instance
            - expected_outputs: QSIReconOutputs instance

    Raises:
        InputValidationError: If inputs are invalid
        ProcedureExecutionError: If reconstruction fails

    Example:
        >>> inputs = QSIReconInputs(
        ...     qsiprep_dir=Path("/data/derivatives/qsiprep"),
        ...     participant="01",
        ... )
        >>> result = run_qsirecon(inputs, atlases=["schaefer100"])
        >>> print(result['expected_outputs'].qsirecon_dir)
    """
    # Use brain bank defaults if config not provided
    config = config or QSIReconDefaults()

    # Apply overrides
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)

    # Validate inputs
    validate_input_dir(inputs.qsiprep_dir, "QSIPrep")
    validate_participant(inputs.qsiprep_dir, inputs.participant)

    # Setup directories
    output_dir = inputs.output_dir or (inputs.qsiprep_dir.parent)
    work_dir = inputs.work_dir or (output_dir.parent / "work" / "qsirecon")
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    # Generate expected outputs
    expected_outputs = QSIReconOutputs.from_inputs(inputs, output_dir, work_dir)

    # Build Docker command
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{inputs.qsiprep_dir}:/data:ro",
        "-v", f"{output_dir}:/out",
        "-v", f"{work_dir}:/work",
    ]

    # Add optional mounts
    if config.fs_license and config.fs_license.exists():
        cmd.extend(["-v", f"{config.fs_license}:/license.txt:ro"])

    if config.fs_subjects_dir and config.fs_subjects_dir.exists():
        cmd.extend(["-v", f"{config.fs_subjects_dir}:/subjects"])

    if config.recon_spec and config.recon_spec.exists():
        cmd.extend(["-v", f"{config.recon_spec}:/recon_spec.yaml:ro"])

    # Container image
    cmd.append(config.docker_image)

    # QSIRecon arguments
    cmd.extend([
        "/data", "/out", "participant",
        f"--participant-label={inputs.participant}",
        f"--nprocs={config.nprocs}",
        f"--mem-gb={config.mem_gb}",
        "--work-dir=/work",
    ])

    # Atlases
    for atlas in config.atlases:
        cmd.append(f"--atlas={atlas}")

    # Optional arguments
    if config.recon_spec and config.recon_spec.exists():
        cmd.append("--recon-spec=/recon_spec.yaml")

    if config.fs_subjects_dir and config.fs_subjects_dir.exists():
        cmd.append("--freesurfer-input=/subjects")

    if config.fs_license and config.fs_license.exists():
        cmd.append("--fs-license-file=/license.txt")

    # Execute
    log_dir = output_dir.parent / "logs"
    result = run_docker(
        cmd=cmd,
        tool_name="qsirecon",
        participant=inputs.participant,
        log_dir=log_dir,
    )

    # Add inputs, config, and expected outputs to result
    result['inputs'] = inputs
    result['config'] = config
    result['expected_outputs'] = expected_outputs

    return result
