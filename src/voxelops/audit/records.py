"""Audit records for procedure execution tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class AuditEventType(Enum):
    """Types of audit events that can be logged."""

    PROCEDURE_START = "procedure_start"
    PRE_VALIDATION = "pre_validation"
    PRE_VALIDATION_FAILED = "pre_validation_failed"
    EXECUTION_START = "execution_start"
    EXECUTION_SUCCESS = "execution_success"
    EXECUTION_FAILED = "execution_failed"
    POST_VALIDATION = "post_validation"
    POST_VALIDATION_FAILED = "post_validation_failed"
    PROCEDURE_COMPLETE = "procedure_complete"
    PROCEDURE_FAILED = "procedure_failed"


@dataclass
class AuditRecord:
    """A single audit event.

    This is the atomic unit of audit logging - one event, one record.
    Designed to be easily serializable for database storage and log files.
    """

    event_type: AuditEventType
    procedure: str
    participant: str
    session: str | None
    timestamp: datetime = field(default_factory=datetime.now)

    # Event-specific data
    data: dict[str, Any] = field(default_factory=dict)

    # For linking related events
    run_id: str | None = None  # UUID for this procedure run

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_type": self.event_type.value,
            "procedure": self.procedure,
            "participant": self.participant,
            "session": self.session,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "run_id": self.run_id,
        }
