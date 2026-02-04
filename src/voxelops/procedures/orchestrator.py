"""Procedure orchestration with validation and audit logging."""

import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from voxelops.audit import AuditEventType, AuditLogger
from voxelops.procedures.result import ProcedureResult
from voxelops.runners import run_heudiconv, run_qsiparc, run_qsiprep, run_qsirecon
from voxelops.validation.context import ValidationContext
from voxelops.validation.validators import (
    HeudiConvValidator,
    QSIParcValidator,
    QSIPrepValidator,
    QSIReconValidator,
)

# Registry of validators by procedure name
VALIDATORS = {
    "heudiconv": HeudiConvValidator(),
    "qsiprep": QSIPrepValidator(),
    "qsirecon": QSIReconValidator(),
    "qsiparc": QSIParcValidator(),
}

# Registry of runners by procedure name
RUNNERS = {
    "heudiconv": run_heudiconv,
    "qsiprep": run_qsiprep,
    "qsirecon": run_qsirecon,
    "qsiparc": run_qsiparc,
}


def run_procedure(
    procedure: str,
    inputs,  # Procedure-specific inputs
    config=None,  # Procedure-specific config
    log_dir: Optional[Path] = None,
    skip_pre_validation: bool = False,
    skip_post_validation: bool = False,
    **overrides,
) -> ProcedureResult:
    """Run a procedure with full validation and audit logging.

    This wraps the existing run_* functions with:
    1. Pre-validation checks
    2. Comprehensive audit logging
    3. Post-validation checks

    Important Notes
    ---------------
    - Post-validation runs even when execution is skipped (force=False and
      outputs exist). This validates the integrity of existing outputs, which
      is beneficial for detecting corruption or incomplete runs.
    - If you want to skip validation entirely for existing outputs, set
      skip_post_validation=True explicitly.

    Parameters
    ----------
    procedure : str
        Procedure name: "heudiconv", "qsiprep", "qsirecon", "qsiparc"
    inputs : procedure-specific inputs schema
        The inputs for the procedure.
    config : procedure-specific config schema, optional
        Configuration/defaults for the procedure.
    log_dir : Path, optional
        Directory for audit logs. Defaults to inputs.output_dir/logs.
    skip_pre_validation : bool, optional
        Skip pre-validation (use with caution).
    skip_post_validation : bool, optional
        Skip post-validation.
    **overrides
        Override config parameters.

    Returns
    -------
    ProcedureResult
        Complete result with validation reports and audit trail.

    Raises
    ------
    ValueError
        If procedure is not recognized.
    """
    run_id = str(uuid.uuid4())
    start_time = datetime.now()

    # Setup
    validator = VALIDATORS.get(procedure)
    runner = RUNNERS.get(procedure)

    if not validator or not runner:
        raise ValueError(f"Unknown procedure: {procedure}")

    # Determine participant/session from inputs
    participant = inputs.participant
    session = getattr(inputs, "session", None)

    # Setup audit logger
    if log_dir is None:
        log_dir = _get_default_log_dir(inputs)

    audit = AuditLogger(
        log_dir=log_dir,
        procedure=procedure,
        participant=participant,
        session=session,
    )
    audit.log(
        AuditEventType.PROCEDURE_START,
        {
            "inputs": _inputs_to_dict(inputs),
            "config": _config_to_dict(config),
            "overrides": _serialize_for_json(overrides),
        },
    )

    # Build validation context
    context = ValidationContext(
        procedure_name=procedure,
        participant=participant,
        session=session,
        inputs=inputs,
        config=config,
    )

    # === PRE-VALIDATION ===
    pre_report = None
    if not skip_pre_validation:
        pre_report = validator.validate_pre(context)
        audit.log_validation_report(pre_report)

        if not pre_report.passed:
            return ProcedureResult(
                procedure=procedure,
                participant=participant,
                session=session,
                run_id=run_id,
                status="pre_validation_failed",
                start_time=start_time,
                end_time=datetime.now(),
                pre_validation=pre_report,
                audit_log_file=str(audit._get_log_file()),
            )

    # === EXECUTION ===
    audit.log(AuditEventType.EXECUTION_START)

    try:
        execution_result = runner(inputs, config, **overrides)
        audit.log(
            AuditEventType.EXECUTION_SUCCESS,
            {
                "duration_seconds": execution_result.get("duration_seconds"),
                "exit_code": execution_result.get("exit_code"),
            },
        )
    except Exception as e:
        audit.log(AuditEventType.EXECUTION_FAILED, {"error": str(e)})
        return ProcedureResult(
            procedure=procedure,
            participant=participant,
            session=session,
            run_id=run_id,
            status="execution_failed",
            start_time=start_time,
            end_time=datetime.now(),
            pre_validation=pre_report,
            execution={"error": str(e), "success": False},
            audit_log_file=str(audit._get_log_file()),
        )

    # === POST-VALIDATION ===
    post_report = None
    if not skip_post_validation:
        # Update context with execution result
        context.execution_result = execution_result
        context.expected_outputs = execution_result.get("expected_outputs")

        post_report = validator.validate_post(context)
        audit.log_validation_report(post_report)

        if not post_report.passed:
            return ProcedureResult(
                procedure=procedure,
                participant=participant,
                session=session,
                run_id=run_id,
                status="post_validation_failed",
                start_time=start_time,
                end_time=datetime.now(),
                pre_validation=pre_report,
                post_validation=post_report,
                execution=execution_result,
                audit_log_file=str(audit._get_log_file()),
            )

    # === SUCCESS ===
    audit.log(AuditEventType.PROCEDURE_COMPLETE)

    return ProcedureResult(
        procedure=procedure,
        participant=participant,
        session=session,
        run_id=run_id,
        status="success",
        start_time=start_time,
        end_time=datetime.now(),
        pre_validation=pre_report,
        post_validation=post_report,
        execution=execution_result,
        audit_log_file=str(audit._get_log_file()),
    )


def _serialize_for_json(obj: Any) -> Any:
    """Recursively convert non-JSON-serializable objects to strings.

    Parameters
    ----------
    obj : Any
        Object to serialize.

    Returns
    -------
    Any
        JSON-serializable version of the object.
    """
    if isinstance(obj, Path):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: _serialize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_serialize_for_json(item) for item in obj]
    else:
        return obj


def _get_default_log_dir(inputs) -> Path:
    """Get default log directory from inputs.

    Parameters
    ----------
    inputs
        Procedure inputs with output_dir attribute.

    Returns
    -------
    Path
        Log directory path.
    """
    if hasattr(inputs, "output_dir") and inputs.output_dir:
        return Path(inputs.output_dir) / "logs"
    # Fallback to current directory
    return Path.cwd() / "logs"


def _inputs_to_dict(inputs) -> Dict[str, Any]:
    """Convert inputs to dictionary for logging.

    Parameters
    ----------
    inputs
        Procedure inputs object.

    Returns
    -------
    Dict[str, Any]
        Dictionary representation.
    """
    if inputs is None:
        return {}
    if hasattr(inputs, "model_dump"):
        return inputs.model_dump(mode="json")
    if hasattr(inputs, "__dict__"):
        return {k: str(v) for k, v in inputs.__dict__.items()}
    return {"inputs": str(inputs)}


def _config_to_dict(config) -> Dict[str, Any]:
    """Convert config to dictionary for logging.

    Parameters
    ----------
    config
        Procedure config object.

    Returns
    -------
    Dict[str, Any]
        Dictionary representation.
    """
    if config is None:
        return {}
    if hasattr(config, "model_dump"):
        return config.model_dump(mode="json")
    if hasattr(config, "__dict__"):
        return {k: str(v) for k, v in config.__dict__.items()}
    return {"config": str(config)}
