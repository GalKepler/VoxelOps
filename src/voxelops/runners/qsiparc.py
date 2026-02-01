"""QSIParc parcellation runner using parcellate package."""

from pathlib import Path
from typing import Dict, Optional, Any

from voxelops.runners._base import (
    run_docker,
    validate_input_dir,
    validate_participant,
)
from voxelops.schemas.qsiparc import (
    QSIParcInputs,
    QSIParcOutputs,
    QSIParcDefaults,
)


def run_qsiparc(
    inputs: QSIParcInputs, config: Optional[QSIParcDefaults] = None, **overrides
) -> Dict[str, Any]:
    """Run parcellation on QSIRecon outputs using parcellate.

    Args:
        inputs: Required inputs (qsirecon_dir, participant, etc.)
        config: Configuration (uses brain bank defaults if not provided)
        **overrides: Override any config parameter

    Returns:
        Execution record with:
            - tool: "qsiparc"
            - participant: Participant label
            - command: Full Docker command executed
            - exit_code: Process exit code
            - start_time, end_time: ISO format timestamps
            - duration_seconds, duration_human: Execution duration
            - success: Boolean success status
            - log_file: Path to JSON log
            - inputs: QSIParcInputs instance
            - config: QSIParcDefaults instance
            - expected_outputs: QSIParcOutputs instance

    Raises:
        InputValidationError: If inputs are invalid
        ProcedureExecutionError: If parcellation fails

    Example:
        >>> inputs = QSIParcInputs(
        ...     qsirecon_dir=Path("/data/derivatives/qsirecon"),
        ...     participant="01",
        ... )
        >>> result = run_qsiparc(inputs)
        >>> print(result['expected_outputs'].connectivity_dir)
    """
    # Use brain bank defaults if config not provided
    config = config or QSIParcDefaults()

    # Apply overrides
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)

    # Validate inputs
    validate_input_dir(inputs.qsirecon_dir, "QSIRecon")
    validate_participant(inputs.qsirecon_dir, inputs.participant)

    # Setup output directory
    output_dir = inputs.output_dir or inputs.qsirecon_dir.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate expected outputs
    expected_outputs = QSIParcOutputs.from_inputs(inputs, output_dir)

    # Build Docker command
    cmd = [
        "docker",
        "run",
        "--rm",
        "-v",
        f"{inputs.qsirecon_dir}:/input:ro",
        "-v",
        f"{output_dir}:/output",
        config.docker_image,
        "/input",
        "/output",
        f"--participant-label={inputs.participant}",
    ]

    # Atlases
    for atlas in config.atlases:
        cmd.extend(["--atlas", atlas])

    # Execute
    log_dir = output_dir.parent / "logs"
    result = run_docker(
        cmd=cmd,
        tool_name="qsiparc",
        participant=inputs.participant,
        log_dir=log_dir,
    )

    # Add inputs, config, and expected outputs to result
    result["inputs"] = inputs
    result["config"] = config
    result["expected_outputs"] = expected_outputs

    return result
