"""QSIRecon diffusion reconstruction runner."""

import os
from pathlib import Path
from typing import Any

from voxelops.runners._base import (
    _get_default_log_dir,
    run_docker,
    validate_input_dir,
    validate_participant,
)
from voxelops.schemas.qsirecon import (
    QSIReconDefaults,
    QSIReconInputs,
    QSIReconOutputs,
)


def run_qsirecon(
    inputs: QSIReconInputs,
    config: QSIReconDefaults | None = None,
    log_dir: Path | None = None,
    **overrides,
) -> dict[str, Any]:
    """Run QSIRecon diffusion reconstruction and connectivity.

    Parameters
    ----------
    inputs : QSIReconInputs
        Required inputs (qsiprep_dir, participant, etc.).
    config : Optional[QSIReconDefaults], optional
        Configuration (uses brain bank defaults if not provided), by default None.
    log_dir : Path, optional
        Directory for audit logs. Defaults to inputs.output_dir/logs.
    **overrides
        Override any config parameter.

    Returns
    -------
    Dict[str, Any]
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

    Raises
    ------
    InputValidationError
        If inputs are invalid.
    ProcedureExecutionError
        If reconstruction fails.

    Examples
    --------
    >>> inputs = QSIReconInputs(
    ...     qsiprep_dir=Path("/data/derivatives/qsiprep"),
    ...     participant="01",
    ... )
    >>> result = run_qsirecon(inputs, atlases=["schaefer100"])
    >>> print(result['expected_outputs'].qsirecon_dir)
    """
    log_dir = log_dir or _get_default_log_dir(inputs)

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

    # Check if outputs already exist and skip if not forcing
    if expected_outputs.exist() and not config.force:
        print("\n" + "=" * 80)
        print(f"✓ QSIRecon outputs already exist for participant {inputs.participant}")
        print(f"  QSIRecon dir: {expected_outputs.qsirecon_dir}")
        print("  Workflow reports:")
        for workflow, sessions in expected_outputs.workflow_reports.items():
            for session, path in sessions.items():
                session_label = f"ses-{session}" if session else "no-session"
                print(f"    - {workflow}/{session_label}: {path}")
        print("  Use force=True to re-run")
        print("=" * 80 + "\n")

        return {
            "tool": "qsirecon",
            "participant": inputs.participant,
            "skipped": True,
            "reason": "outputs_exist",
            "success": True,
            "inputs": inputs,
            "config": config,
            "expected_outputs": expected_outputs,
        }

    # Get current user/group IDs for Docker
    uid = os.getuid()
    gid = os.getgid()

    # Build Docker command
    cmd = [
        "docker",
        "run",
        "-it",
        "--rm",
        "--user",
        f"{uid}:{gid}",
        "-v",
        f"{inputs.qsiprep_dir}:/data:ro",
        "-v",
        f"{output_dir}:/out",
        "-v",
        f"{work_dir}:/work",
    ]

    # Mount recon spec only when provided
    if inputs.recon_spec and inputs.recon_spec.exists():
        cmd.extend(["-v", f"{inputs.recon_spec}:/recon_spec.yaml:ro"])

    # Add optional mounts
    if config.fs_license and config.fs_license.exists():
        cmd.extend(["-v", f"{config.fs_license}:/license.txt:ro"])

    # Aux files: use the directory basename as the container mount point
    # so that e.g. a local ".../responses" dir becomes "/responses" in-container
    if inputs.recon_spec_aux_files and inputs.recon_spec_aux_files.exists():
        aux_name = inputs.recon_spec_aux_files.name
        cmd.extend(["-v", f"{inputs.recon_spec_aux_files}:/{aux_name}:ro"])

    # FreeSurfer subjects directory
    if config.fs_subjects_dir and config.fs_subjects_dir.exists():
        cmd.extend(["-v", f"{config.fs_subjects_dir}:/fs_subjects_dir:ro"])

    if inputs.datasets:
        for name, path in inputs.datasets.items():
            cmd.extend(["-v", f"{path}:/datasets/{name}:ro"])

    # Container image
    cmd.append(config.docker_image)

    # QSIRecon positional arguments
    cmd.extend(
        [
            "/data",
            "/out",
            "participant",
            "--participant-label",
            inputs.participant,
        ]
    )

    # Per-session reconstruction
    if inputs.session:
        cmd.extend(["--session-id", inputs.session])

    cmd.extend(
        [
            "--nprocs",
            str(config.nprocs),
            "--mem-mb",
            str(config.mem_mb),
            "--work-dir",
            "/work",
        ]
    )

    # Datasets
    if inputs.datasets:
        cmd.extend(["--datasets"])
        for name in inputs.datasets.keys():
            cmd.extend([f"{name}=/datasets/{name}"])

    # Atlases (optional - some recon specs may not require them)
    if inputs.atlases:
        cmd.extend(["--atlases", *inputs.atlases])

    # Recon spec and aux files
    if inputs.recon_spec and inputs.recon_spec.exists():
        cmd.extend(["--recon-spec", "/recon_spec.yaml"])

    if inputs.recon_spec_aux_files and inputs.recon_spec_aux_files.exists():
        aux_name = inputs.recon_spec_aux_files.name
        cmd.extend(["--recon-spec-aux-files", f"/{aux_name}"])

    # FreeSurfer integration
    if config.fs_subjects_dir and config.fs_subjects_dir.exists():
        cmd.extend(["--fs-subjects-dir", "/fs_subjects_dir"])

    if config.fs_license and config.fs_license.exists():
        cmd.extend(["--fs-license-file", "/license.txt"])

    # Execute
    result = run_docker(
        cmd=cmd,
        tool_name="qsirecon",
        participant=inputs.participant,
        session=inputs.session,
        log_dir=log_dir,
    )

    # Add inputs, config, and expected outputs to result
    result["inputs"] = inputs
    result["config"] = config
    result["expected_outputs"] = expected_outputs
    result["skipped"] = False

    return result
