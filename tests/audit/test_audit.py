"""Tests for audit records and logger."""

import json
from datetime import datetime

from voxelops.audit import AuditEventType, AuditLogger, AuditRecord
from voxelops.validation.base import ValidationReport, ValidationResult


class TestAuditEventType:
    """Tests for AuditEventType enum."""

    def test_all_event_types_defined(self):
        """Test that all expected event types exist."""
        expected_events = {
            "PROCEDURE_START",
            "PRE_VALIDATION",
            "PRE_VALIDATION_FAILED",
            "EXECUTION_START",
            "EXECUTION_SUCCESS",
            "EXECUTION_FAILED",
            "POST_VALIDATION",
            "POST_VALIDATION_FAILED",
            "PROCEDURE_COMPLETE",
            "PROCEDURE_FAILED",
        }
        actual_events = {e.name for e in AuditEventType}
        assert expected_events == actual_events

    def test_event_type_values(self):
        """Test that event type values match expected strings."""
        assert AuditEventType.PROCEDURE_START.value == "procedure_start"
        assert AuditEventType.PRE_VALIDATION.value == "pre_validation"
        assert AuditEventType.PRE_VALIDATION_FAILED.value == "pre_validation_failed"
        assert AuditEventType.EXECUTION_START.value == "execution_start"
        assert AuditEventType.EXECUTION_SUCCESS.value == "execution_success"
        assert AuditEventType.EXECUTION_FAILED.value == "execution_failed"
        assert AuditEventType.POST_VALIDATION.value == "post_validation"
        assert AuditEventType.POST_VALIDATION_FAILED.value == "post_validation_failed"
        assert AuditEventType.PROCEDURE_COMPLETE.value == "procedure_complete"
        assert AuditEventType.PROCEDURE_FAILED.value == "procedure_failed"


class TestAuditRecord:
    """Tests for AuditRecord."""

    def test_init_minimal(self):
        """Test AuditRecord initialization with minimal params."""
        record = AuditRecord(
            event_type=AuditEventType.PROCEDURE_START,
            procedure="qsiprep",
            participant="01",
            session=None,
        )

        assert record.event_type == AuditEventType.PROCEDURE_START
        assert record.procedure == "qsiprep"
        assert record.participant == "01"
        assert record.session is None
        assert isinstance(record.timestamp, datetime)
        assert record.data == {}
        assert record.run_id is None

    def test_init_with_all_fields(self):
        """Test AuditRecord initialization with all fields."""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        data = {"key": "value", "count": 42}
        run_id = "test-run-id"

        record = AuditRecord(
            event_type=AuditEventType.EXECUTION_SUCCESS,
            procedure="heudiconv",
            participant="02",
            session="01",
            timestamp=timestamp,
            data=data,
            run_id=run_id,
        )

        assert record.event_type == AuditEventType.EXECUTION_SUCCESS
        assert record.procedure == "heudiconv"
        assert record.participant == "02"
        assert record.session == "01"
        assert record.timestamp == timestamp
        assert record.data == data
        assert record.run_id == run_id

    def test_to_dict(self):
        """Test AuditRecord serialization to dict."""
        timestamp = datetime(2024, 1, 15, 10, 30, 0)
        data = {"result": "success", "duration": 123.45}
        run_id = "abc-123"

        record = AuditRecord(
            event_type=AuditEventType.POST_VALIDATION,
            procedure="qsirecon",
            participant="03",
            session="02",
            timestamp=timestamp,
            data=data,
            run_id=run_id,
        )

        result = record.to_dict()

        assert result["event_type"] == "post_validation"
        assert result["procedure"] == "qsirecon"
        assert result["participant"] == "03"
        assert result["session"] == "02"
        assert result["timestamp"] == "2024-01-15T10:30:00"
        assert result["data"] == data
        assert result["run_id"] == run_id


class TestAuditLogger:
    """Tests for AuditLogger."""

    def test_init(self, tmp_path):
        """Test AuditLogger initialization."""
        log_dir = tmp_path / "logs"

        logger = AuditLogger(
            log_dir=log_dir,
            procedure="qsiprep",
            participant="01",
            session="01",
        )

        assert logger.log_dir == log_dir
        assert logger.procedure == "qsiprep"
        assert logger.participant == "01"
        assert logger.session == "01"
        assert logger.run_id is not None
        assert isinstance(logger.run_id, str)
        assert logger.records == []
        assert log_dir.exists()

    def test_init_creates_log_dir(self, tmp_path):
        """Test that initialization creates the log directory."""
        log_dir = tmp_path / "nested" / "logs"
        assert not log_dir.exists()

        AuditLogger(
            log_dir=log_dir,
            procedure="heudiconv",
            participant="01",
        )

        assert log_dir.exists()

    def test_log_event(self, tmp_path):
        """Test logging a simple event."""
        log_dir = tmp_path / "logs"
        logger = AuditLogger(
            log_dir=log_dir,
            procedure="qsiprep",
            participant="01",
        )

        logger.log(AuditEventType.PROCEDURE_START, {"input": "/data/bids"})

        assert len(logger.records) == 1
        record = logger.records[0]
        assert record.event_type == AuditEventType.PROCEDURE_START
        assert record.procedure == "qsiprep"
        assert record.participant == "01"
        assert record.data == {"input": "/data/bids"}
        assert record.run_id == logger.run_id

    def test_log_multiple_events(self, tmp_path):
        """Test logging multiple events."""
        log_dir = tmp_path / "logs"
        logger = AuditLogger(
            log_dir=log_dir,
            procedure="qsirecon",
            participant="02",
            session="01",
        )

        logger.log(AuditEventType.PROCEDURE_START)
        logger.log(AuditEventType.PRE_VALIDATION, {"status": "passed"})
        logger.log(AuditEventType.EXECUTION_START)

        assert len(logger.records) == 3
        assert logger.records[0].event_type == AuditEventType.PROCEDURE_START
        assert logger.records[1].event_type == AuditEventType.PRE_VALIDATION
        assert logger.records[2].event_type == AuditEventType.EXECUTION_START

    def test_log_writes_to_file(self, tmp_path):
        """Test that log events are written to file."""
        log_dir = tmp_path / "logs"
        logger = AuditLogger(
            log_dir=log_dir,
            procedure="heudiconv",
            participant="03",
        )

        logger.log(AuditEventType.PROCEDURE_START, {"test": "data"})

        log_file = logger._get_log_file()
        assert log_file.exists()

        with open(log_file) as f:
            lines = f.readlines()

        assert len(lines) == 1
        event = json.loads(lines[0])
        assert event["event_type"] == "procedure_start"
        assert event["data"] == {"test": "data"}

    def test_log_file_naming(self, tmp_path):
        """Test log file naming convention."""
        log_dir = tmp_path / "logs"

        # Without session
        logger1 = AuditLogger(
            log_dir=log_dir,
            procedure="qsiprep",
            participant="01",
        )
        log_file1 = logger1._get_log_file()
        assert "sub-01_qsiprep_" in log_file1.name
        assert "ses-" not in log_file1.name

        # With session
        logger2 = AuditLogger(
            log_dir=log_dir,
            procedure="qsirecon",
            participant="02",
            session="01",
        )
        log_file2 = logger2._get_log_file()
        assert "sub-02_ses-01_qsirecon_" in log_file2.name

    def test_log_validation_report_success(self, tmp_path):
        """Test logging a successful validation report."""
        log_dir = tmp_path / "logs"
        logger = AuditLogger(
            log_dir=log_dir,
            procedure="qsiprep",
            participant="01",
        )

        # Create a passing validation report
        result = ValidationResult(
            rule_name="test_rule",
            rule_description="Test rule",
            passed=True,
            severity="error",
            message="Test passed",
        )
        report = ValidationReport(
            phase="pre",
            procedure="qsiprep",
            participant="01",
            session=None,
            results=[result],
        )

        logger.log_validation_report(report)

        assert len(logger.records) == 1
        assert logger.records[0].event_type == AuditEventType.PRE_VALIDATION
        assert logger.records[0].data["passed"] is True
        assert logger.records[0].data["phase"] == "pre"

    def test_log_validation_report_failure(self, tmp_path):
        """Test logging a failed validation report."""
        log_dir = tmp_path / "logs"
        logger = AuditLogger(
            log_dir=log_dir,
            procedure="qsirecon",
            participant="02",
        )

        # Create a failing validation report
        result = ValidationResult(
            rule_name="test_rule",
            rule_description="Test rule",
            passed=False,
            severity="error",
            message="Test failed",
        )
        report = ValidationReport(
            phase="post",
            procedure="qsirecon",
            participant="02",
            session=None,
            results=[result],
        )

        logger.log_validation_report(report)

        assert len(logger.records) == 1
        assert logger.records[0].event_type == AuditEventType.POST_VALIDATION_FAILED
        assert logger.records[0].data["passed"] is False

    def test_get_summary(self, tmp_path):
        """Test getting a summary of logged events."""
        log_dir = tmp_path / "logs"
        logger = AuditLogger(
            log_dir=log_dir,
            procedure="heudiconv",
            participant="01",
            session="02",
        )

        logger.log(AuditEventType.PROCEDURE_START)
        logger.log(AuditEventType.EXECUTION_SUCCESS, {"duration": 123})

        summary = logger.get_summary()

        assert summary["run_id"] == logger.run_id
        assert summary["procedure"] == "heudiconv"
        assert summary["participant"] == "01"
        assert summary["session"] == "02"
        assert summary["event_count"] == 2
        assert len(summary["events"]) == 2
        assert "log_file" in summary

    def test_multiple_logs_append_to_file(self, tmp_path):
        """Test that multiple log calls append to the same file."""
        log_dir = tmp_path / "logs"
        logger = AuditLogger(
            log_dir=log_dir,
            procedure="qsiprep",
            participant="01",
        )

        logger.log(AuditEventType.PROCEDURE_START)
        logger.log(AuditEventType.PRE_VALIDATION)
        logger.log(AuditEventType.EXECUTION_START)

        log_file = logger._get_log_file()
        with open(log_file) as f:
            lines = f.readlines()

        assert len(lines) == 3
        events = [json.loads(line) for line in lines]
        assert events[0]["event_type"] == "procedure_start"
        assert events[1]["event_type"] == "pre_validation"
        assert events[2]["event_type"] == "execution_start"

    def test_unique_run_ids(self, tmp_path):
        """Test that each logger instance gets a unique run_id."""
        log_dir = tmp_path / "logs"

        logger1 = AuditLogger(
            log_dir=log_dir,
            procedure="qsiprep",
            participant="01",
        )
        logger2 = AuditLogger(
            log_dir=log_dir,
            procedure="qsiprep",
            participant="01",
        )

        assert logger1.run_id != logger2.run_id
