"""Audit logger for structured procedure execution tracking."""

import json
import uuid
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from voxelops.audit.records import AuditEventType, AuditRecord

if TYPE_CHECKING:
    from voxelops.validation.base import ValidationReport


class AuditLogger:
    """Structured audit logging for procedure runs.

    Creates a JSONL log file with one event per line for easy parsing.
    Each event is timestamped and linked via a unique run_id.
    """

    def __init__(
        self,
        log_dir: Path,
        procedure: str,
        participant: str,
        session: Optional[str] = None,
    ):
        """Initialize audit logger.

        Parameters
        ----------
        log_dir : Path
            Directory where log files will be written.
        procedure : str
            Name of the procedure being logged.
        participant : str
            Participant identifier.
        session : Optional[str]
            Session identifier, if applicable.
        """
        self.log_dir = Path(log_dir)
        self.procedure = procedure
        self.participant = participant
        self.session = session
        self.run_id = str(uuid.uuid4())
        self.records: List[AuditRecord] = []

        # Ensure log directory exists
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log(self, event_type: AuditEventType, data: Optional[Dict[str, Any]] = None):
        """Log an audit event.

        Parameters
        ----------
        event_type : AuditEventType
            Type of event being logged.
        data : Optional[Dict[str, Any]]
            Event-specific data to include.
        """
        record = AuditRecord(
            event_type=event_type,
            procedure=self.procedure,
            participant=self.participant,
            session=self.session,
            data=data or {},
            run_id=self.run_id,
        )
        self.records.append(record)
        self._write_record(record)

    def log_validation_report(self, report: "ValidationReport"):
        """Log a complete validation report.

        Parameters
        ----------
        report : ValidationReport
            The validation report to log.
        """
        event_type = (
            AuditEventType.PRE_VALIDATION
            if report.phase == "pre"
            else AuditEventType.POST_VALIDATION
        )

        # If validation failed, use the failed event type
        if not report.passed:
            event_type = (
                AuditEventType.PRE_VALIDATION_FAILED
                if report.phase == "pre"
                else AuditEventType.POST_VALIDATION_FAILED
            )

        self.log(event_type, report.to_dict())

    def _write_record(self, record: AuditRecord):
        """Write a single record to the log file.

        Parameters
        ----------
        record : AuditRecord
            The record to write.
        """
        log_file = self._get_log_file()
        with open(log_file, "a") as f:
            f.write(json.dumps(record.to_dict()) + "\n")

    def _get_log_file(self) -> Path:
        """Get the log file path for this run.

        Returns
        -------
        Path
            Path to the log file.
        """
        session_part = f"_ses-{self.session}" if self.session else ""
        filename = (
            f"sub-{self.participant}{session_part}_{self.procedure}_{self.run_id}.jsonl"
        )
        return self.log_dir / filename

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of all logged events.

        Returns
        -------
        Dict[str, Any]
            Summary containing run_id, procedure info, and all events.
        """
        return {
            "run_id": self.run_id,
            "procedure": self.procedure,
            "participant": self.participant,
            "session": self.session,
            "event_count": len(self.records),
            "events": [r.to_dict() for r in self.records],
            "log_file": str(self._get_log_file()),
        }
