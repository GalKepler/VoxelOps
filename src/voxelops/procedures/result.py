"""Procedure execution result."""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Literal, Optional

if TYPE_CHECKING:
    from voxelops.validation.base import ValidationReport


@dataclass
class ProcedureResult:
    """Complete result of a procedure run including validation and audit.

    This is the unified result object returned by run_procedure().
    It contains:
    - Overall success/failure status
    - Pre and post validation reports
    - Execution details
    - Audit log reference
    - Timing information

    Designed to be easily serializable for database storage.
    """

    # Identification
    procedure: str
    participant: str
    session: Optional[str]
    run_id: str

    # Overall status
    status: Literal[
        "success",  # Everything passed
        "pre_validation_failed",  # Stopped before execution
        "execution_failed",  # Procedure itself failed
        "post_validation_failed",  # Outputs don't meet requirements
    ]

    # Timestamps
    start_time: datetime
    end_time: Optional[datetime] = None

    # Validation reports
    pre_validation: Optional["ValidationReport"] = None
    post_validation: Optional["ValidationReport"] = None

    # Execution details (from existing runner)
    execution: Optional[Dict[str, Any]] = None

    # Audit trail
    audit_log_file: Optional[str] = None

    @property
    def duration_seconds(self) -> Optional[float]:
        """Get the total duration in seconds."""
        if self.end_time and self.start_time:
            return (self.end_time - self.start_time).total_seconds()
        return None

    @property
    def success(self) -> bool:
        """True if status is success."""
        return self.status == "success"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for database storage."""
        return {
            "procedure": self.procedure,
            "participant": self.participant,
            "session": self.session,
            "run_id": self.run_id,
            "status": self.status,
            "success": self.success,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds,
            "pre_validation": (
                self.pre_validation.to_dict() if self.pre_validation else None
            ),
            "post_validation": (
                self.post_validation.to_dict() if self.post_validation else None
            ),
            "execution": self.execution,
            "audit_log_file": self.audit_log_file,
        }

    def get_failure_reason(self) -> Optional[str]:
        """Get a human-readable failure reason.

        Returns
        -------
        Optional[str]
            Failure reason or None if successful.
        """
        if self.status == "success":
            return None

        if self.status == "pre_validation_failed" and self.pre_validation:
            errors = self.pre_validation.errors
            if errors:
                return f"Pre-validation failed: {errors[0].message}"

        if self.status == "execution_failed" and self.execution:
            return f"Execution failed: {self.execution.get('error', 'Unknown error')}"

        if self.status == "post_validation_failed" and self.post_validation:
            errors = self.post_validation.errors
            if errors:
                return f"Post-validation failed: {errors[0].message}"

        return f"Failed with status: {self.status}"
