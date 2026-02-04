"""QSIParc parcellation runner using parcellate package."""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from parcellate.interfaces.qsirecon.models import QSIReconConfig
from parcellate.interfaces.qsirecon.qsirecon import run_parcellations

from voxelops.exceptions import ProcedureExecutionError
from voxelops.runners._base import (
    validate_input_dir,
    validate_participant,
)
from voxelops.schemas.qsiparc import (
    QSIParcDefaults,
    QSIParcInputs,
    QSIParcOutputs,
)


def run_qsiparc(
    inputs: QSIParcInputs, config: Optional[QSIParcDefaults] = None, **overrides
) -> Dict[str, Any]:
    """Run parcellation on QSIRecon outputs using parcellate.

    Atlases are auto-discovered from the QSIRecon derivatives directory
    (BIDS dseg files). No manual atlas list is needed.

    Parameters
    ----------
    inputs : QSIParcInputs
        Required inputs (qsirecon_dir, participant, etc.).
    config : Optional[QSIParcDefaults], optional
        Configuration (uses brain bank defaults if not provided), by default None.
    **overrides
        Override any config parameter.

    Returns
    -------
    Dict[str, Any]
        Execution record with:
            - tool: "qsiparc"
            - participant: Participant label
            - start_time, end_time: ISO format timestamps
            - duration_seconds, duration_human: Execution duration
            - success: Boolean success status
            - output_files: List of output TSV paths
            - inputs: QSIParcInputs instance
            - config: QSIParcDefaults instance
            - expected_outputs: QSIParcOutputs instance

    Raises
    ------
    InputValidationError
        If inputs are invalid.
    ProcedureExecutionError
        If parcellation fails.

    Examples
    --------
    >>> inputs = QSIParcInputs(
    ...     qsirecon_dir=Path("/data/derivatives/qsirecon"),
    ...     participant="01",
    ... )
    >>> result = run_qsiparc(inputs)
    >>> print(result['output_files'])
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

    # Build parcellate config
    log_level = getattr(logging, config.log_level.upper(), logging.INFO)
    parcellate_config = QSIReconConfig(
        input_root=inputs.qsirecon_dir,
        output_dir=output_dir,
        subjects=[inputs.participant],
        sessions=[inputs.session] if inputs.session else None,
        mask=config.mask,
        background_label=config.background_label,
        resampling_target=config.resampling_target,
        force=config.force,
        log_level=log_level,
        atlases=inputs.atlases or [],
        n_jobs=inputs.n_jobs or config.n_jobs,
        n_procs=inputs.n_procs or config.n_procs,
    )

    print(f"\n{'='*80}")
    print(f"Running qsiparc for participant {inputs.participant}")
    print(f"{'='*80}")
    print(f"Input: {inputs.qsirecon_dir}")
    print(f"Output: {output_dir}")
    print(f"{'='*80}\n")

    start_time = datetime.now()

    try:
        output_files = run_parcellations(parcellate_config)

        end_time = datetime.now()
        duration = end_time - start_time

        record = {
            "tool": "qsiparc",
            "participant": inputs.participant,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "duration_human": str(duration),
            "success": True,
            "output_files": output_files,
            "inputs": inputs,
            "config": config,
            "expected_outputs": expected_outputs,
        }

        print(f"\n{'='*80}")
        print("qsiparc completed successfully")
        print(f"Duration: {duration}")
        print(f"Output files: {len(output_files)}")
        print(f"{'='*80}\n")

        return record

    except Exception as e:
        if isinstance(e, ProcedureExecutionError):
            raise
        raise ProcedureExecutionError(
            procedure_name="qsiparc",
            message=str(e),
            original_error=e,
        ) from e
