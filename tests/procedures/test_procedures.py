"""Tests for procedure orchestration and results."""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from voxelops.procedures import ProcedureResult, run_procedure
from voxelops.validation.base import ValidationReport, ValidationResult


@dataclass
class MockInputs:
    """Mock inputs for testing."""

    participant: str
    session: str | None = None
    bids_dir: Path | None = None
    output_dir: Path | None = None


class TestProcedureResult:
    """Tests for ProcedureResult."""

    def test_init_minimal(self):
        """Test ProcedureResult initialization with minimal params."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        result = ProcedureResult(
            procedure="qsiprep",
            participant="01",
            session=None,
            run_id="test-run-id",
            status="success",
            start_time=start_time,
        )

        assert result.procedure == "qsiprep"
        assert result.participant == "01"
        assert result.session is None
        assert result.run_id == "test-run-id"
        assert result.status == "success"
        assert result.start_time == start_time
        assert result.end_time is None

    def test_success_property(self):
        """Test the success property."""
        start_time = datetime.now()

        result_success = ProcedureResult(
            procedure="qsiprep",
            participant="01",
            session=None,
            run_id="test-run-id",
            status="success",
            start_time=start_time,
        )
        assert result_success.success is True

        result_failed = ProcedureResult(
            procedure="qsiprep",
            participant="01",
            session=None,
            run_id="test-run-id",
            status="pre_validation_failed",
            start_time=start_time,
        )
        assert result_failed.success is False

    def test_duration_seconds(self):
        """Test duration_seconds calculation."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 10, 5, 30)

        result = ProcedureResult(
            procedure="qsiprep",
            participant="01",
            session=None,
            run_id="test-run-id",
            status="success",
            start_time=start_time,
            end_time=end_time,
        )

        assert result.duration_seconds == 330.0  # 5 minutes 30 seconds

    def test_duration_seconds_none(self):
        """Test duration_seconds when end_time is None."""
        result = ProcedureResult(
            procedure="qsiprep",
            participant="01",
            session=None,
            run_id="test-run-id",
            status="success",
            start_time=datetime.now(),
        )

        assert result.duration_seconds is None

    def test_to_dict(self):
        """Test serialization to dict."""
        start_time = datetime(2024, 1, 15, 10, 0, 0)
        end_time = datetime(2024, 1, 15, 10, 5, 0)

        result = ProcedureResult(
            procedure="heudiconv",
            participant="02",
            session="01",
            run_id="abc-123",
            status="success",
            start_time=start_time,
            end_time=end_time,
        )

        data = result.to_dict()

        assert data["procedure"] == "heudiconv"
        assert data["participant"] == "02"
        assert data["session"] == "01"
        assert data["run_id"] == "abc-123"
        assert data["status"] == "success"
        assert data["success"] is True
        assert data["start_time"] == "2024-01-15T10:00:00"
        assert data["end_time"] == "2024-01-15T10:05:00"
        assert data["duration_seconds"] == 300.0

    def test_get_failure_reason_success(self):
        """Test get_failure_reason for successful run."""
        result = ProcedureResult(
            procedure="qsiprep",
            participant="01",
            session=None,
            run_id="test-run-id",
            status="success",
            start_time=datetime.now(),
        )

        assert result.get_failure_reason() is None

    def test_get_failure_reason_pre_validation(self):
        """Test get_failure_reason for pre-validation failure."""
        validation_result = ValidationResult(
            rule_name="test_rule",
            rule_description="Test",
            passed=False,
            severity="error",
            message="DICOM directory not found",
        )
        pre_report = ValidationReport(
            phase="pre",
            procedure="heudiconv",
            participant="01",
            session=None,
            results=[validation_result],
        )

        result = ProcedureResult(
            procedure="heudiconv",
            participant="01",
            session=None,
            run_id="test-run-id",
            status="pre_validation_failed",
            start_time=datetime.now(),
            pre_validation=pre_report,
        )

        reason = result.get_failure_reason()
        assert reason == "Pre-validation failed: DICOM directory not found"

    def test_get_failure_reason_execution(self):
        """Test get_failure_reason for execution failure."""
        result = ProcedureResult(
            procedure="qsiprep",
            participant="01",
            session=None,
            run_id="test-run-id",
            status="execution_failed",
            start_time=datetime.now(),
            execution={"error": "Container crashed", "success": False},
        )

        reason = result.get_failure_reason()
        assert reason == "Execution failed: Container crashed"

    def test_get_failure_reason_post_validation(self):
        """Test get_failure_reason for post-validation failure."""
        validation_result = ValidationResult(
            rule_name="output_check",
            rule_description="Check outputs",
            passed=False,
            severity="error",
            message="Output directory not created",
        )
        post_report = ValidationReport(
            phase="post",
            procedure="qsirecon",
            participant="01",
            session=None,
            results=[validation_result],
        )

        result = ProcedureResult(
            procedure="qsirecon",
            participant="01",
            session=None,
            run_id="test-run-id",
            status="post_validation_failed",
            start_time=datetime.now(),
            post_validation=post_report,
        )

        reason = result.get_failure_reason()
        assert reason == "Post-validation failed: Output directory not created"


class TestRunProcedure:
    """Tests for run_procedure orchestrator."""

    def test_unknown_procedure_raises_error(self):
        """Test that unknown procedure raises ValueError."""
        inputs = MockInputs(participant="01")

        with pytest.raises(ValueError, match="Unknown procedure"):
            run_procedure("unknown_proc", inputs)

    def test_successful_run(self, tmp_path):
        """Test successful procedure run with all validations passing."""
        # Setup mocks
        mock_validator = Mock()

        # Mock pre-validation passing
        pre_report = Mock()
        pre_report.passed = True
        pre_report.phase = "pre"
        pre_report.to_dict.return_value = {"phase": "pre", "passed": True}
        mock_validator.validate_pre.return_value = pre_report

        # Mock post-validation passing
        post_report = Mock()
        post_report.passed = True
        post_report.phase = "post"
        post_report.to_dict.return_value = {"phase": "post", "passed": True}
        mock_validator.validate_post.return_value = post_report

        # Mock runner
        mock_runner = Mock(
            return_value={
                "success": True,
                "exit_code": 0,
                "duration_seconds": 123.45,
                "expected_outputs": {},
            }
        )

        # Setup inputs
        inputs = MockInputs(
            participant="01",
            bids_dir=tmp_path / "bids",
            output_dir=tmp_path / "output",
        )

        # Patch VALIDATORS and RUNNERS
        with (
            patch.dict(
                "voxelops.procedures.orchestrator.VALIDATORS",
                {"heudiconv": mock_validator},
            ),
            patch.dict(
                "voxelops.procedures.orchestrator.RUNNERS", {"heudiconv": mock_runner}
            ),
        ):
            # Run procedure
            result = run_procedure("heudiconv", inputs, log_dir=tmp_path / "logs")

        # Verify result
        assert result.status == "success"
        assert result.success is True
        assert result.procedure == "heudiconv"
        assert result.participant == "01"
        assert result.pre_validation == pre_report
        assert result.post_validation == post_report
        assert result.execution["success"] is True

    def test_pre_validation_failure(self, tmp_path):
        """Test procedure stops on pre-validation failure."""
        # Setup mocks
        mock_validator = Mock()

        # Mock pre-validation failing
        pre_report = Mock()
        pre_report.passed = False
        pre_report.phase = "pre"
        pre_report.to_dict.return_value = {
            "phase": "pre",
            "passed": False,
            "errors": [{"message": "BIDS directory not found"}],
        }
        mock_validator.validate_pre.return_value = pre_report

        # Mock runner
        mock_runner = Mock()

        # Setup inputs
        inputs = MockInputs(
            participant="01",
            bids_dir=tmp_path / "nonexistent",
            output_dir=tmp_path / "output",
        )

        # Patch VALIDATORS and RUNNERS
        with (
            patch.dict(
                "voxelops.procedures.orchestrator.VALIDATORS",
                {"qsiprep": mock_validator},
            ),
            patch.dict(
                "voxelops.procedures.orchestrator.RUNNERS", {"qsiprep": mock_runner}
            ),
        ):
            # Run procedure
            result = run_procedure("qsiprep", inputs, log_dir=tmp_path / "logs")

        # Verify result
        assert result.status == "pre_validation_failed"
        assert result.success is False
        assert result.pre_validation == pre_report
        assert result.post_validation is None
        assert result.execution is None

        # Verify runner was never called
        mock_runner.assert_not_called()

    def test_execution_failure(self, tmp_path):
        """Test handling of execution failure."""
        # Setup mocks
        mock_validator = Mock()

        # Mock pre-validation passing
        pre_report = Mock()
        pre_report.passed = True
        pre_report.to_dict.return_value = {"phase": "pre", "passed": True}
        mock_validator.validate_pre.return_value = pre_report

        # Mock runner raising exception
        mock_runner = Mock(side_effect=RuntimeError("Container failed"))

        # Setup inputs
        inputs = MockInputs(
            participant="01",
            output_dir=tmp_path / "output",
        )

        # Patch VALIDATORS and RUNNERS
        with (
            patch.dict(
                "voxelops.procedures.orchestrator.VALIDATORS",
                {"qsirecon": mock_validator},
            ),
            patch.dict(
                "voxelops.procedures.orchestrator.RUNNERS", {"qsirecon": mock_runner}
            ),
        ):
            # Run procedure
            result = run_procedure("qsirecon", inputs, log_dir=tmp_path / "logs")

        # Verify result
        assert result.status == "execution_failed"
        assert result.success is False
        assert result.pre_validation == pre_report
        assert result.post_validation is None
        assert result.execution["success"] is False
        assert "Container failed" in result.execution["error"]

    def test_post_validation_failure(self, tmp_path):
        """Test handling of post-validation failure."""
        # Setup mocks
        mock_validator = Mock()

        # Mock pre-validation passing
        pre_report = Mock()
        pre_report.passed = True
        pre_report.to_dict.return_value = {"phase": "pre", "passed": True}
        mock_validator.validate_pre.return_value = pre_report

        # Mock post-validation failing
        post_report = Mock()
        post_report.passed = False
        post_report.phase = "post"
        post_report.to_dict.return_value = {
            "phase": "post",
            "passed": False,
            "errors": [{"message": "Output files not found"}],
        }
        mock_validator.validate_post.return_value = post_report

        # Mock runner
        mock_runner = Mock(
            return_value={
                "success": True,
                "exit_code": 0,
                "expected_outputs": {},
            }
        )

        # Setup inputs
        inputs = MockInputs(
            participant="01",
            output_dir=tmp_path / "output",
        )

        # Patch VALIDATORS and RUNNERS
        with (
            patch.dict(
                "voxelops.procedures.orchestrator.VALIDATORS",
                {"qsiparc": mock_validator},
            ),
            patch.dict(
                "voxelops.procedures.orchestrator.RUNNERS", {"qsiparc": mock_runner}
            ),
        ):
            # Run procedure
            result = run_procedure("qsiparc", inputs, log_dir=tmp_path / "logs")

        # Verify result
        assert result.status == "post_validation_failed"
        assert result.success is False
        assert result.pre_validation == pre_report
        assert result.post_validation == post_report
        assert result.execution["success"] is True

    def test_skip_pre_validation(self, tmp_path):
        """Test skipping pre-validation."""
        # Setup mocks
        mock_validator = Mock()

        # Mock post-validation passing
        post_report = Mock()
        post_report.passed = True
        post_report.to_dict.return_value = {"phase": "post", "passed": True}
        mock_validator.validate_post.return_value = post_report

        # Mock runner
        mock_runner = Mock(
            return_value={
                "success": True,
                "expected_outputs": {},
            }
        )

        # Setup inputs
        inputs = MockInputs(
            participant="01",
            output_dir=tmp_path / "output",
        )

        # Patch VALIDATORS and RUNNERS
        with (
            patch.dict(
                "voxelops.procedures.orchestrator.VALIDATORS",
                {"heudiconv": mock_validator},
            ),
            patch.dict(
                "voxelops.procedures.orchestrator.RUNNERS", {"heudiconv": mock_runner}
            ),
        ):
            # Run procedure with skip_pre_validation
            result = run_procedure(
                "heudiconv",
                inputs,
                log_dir=tmp_path / "logs",
                skip_pre_validation=True,
            )

        # Verify result
        assert result.status == "success"
        assert result.pre_validation is None
        assert result.post_validation == post_report

        # Verify pre-validation was not called
        mock_validator.validate_pre.assert_not_called()

    def test_skip_post_validation(self, tmp_path):
        """Test skipping post-validation."""
        # Setup mocks
        mock_validator = Mock()

        # Mock pre-validation passing
        pre_report = Mock()
        pre_report.passed = True
        pre_report.to_dict.return_value = {"phase": "pre", "passed": True}
        mock_validator.validate_pre.return_value = pre_report

        # Mock runner
        mock_runner = Mock(
            return_value={
                "success": True,
                "expected_outputs": {},
            }
        )

        # Setup inputs
        inputs = MockInputs(
            participant="01",
            output_dir=tmp_path / "output",
        )

        # Patch VALIDATORS and RUNNERS
        with (
            patch.dict(
                "voxelops.procedures.orchestrator.VALIDATORS",
                {"qsiprep": mock_validator},
            ),
            patch.dict(
                "voxelops.procedures.orchestrator.RUNNERS", {"qsiprep": mock_runner}
            ),
        ):
            # Run procedure with skip_post_validation
            result = run_procedure(
                "qsiprep",
                inputs,
                log_dir=tmp_path / "logs",
                skip_post_validation=True,
            )

        # Verify result
        assert result.status == "success"
        assert result.pre_validation == pre_report
        assert result.post_validation is None

        # Verify post-validation was not called
        mock_validator.validate_post.assert_not_called()

    def test_nonzero_exit_proceeds_to_post_validation(self, tmp_path):
        """Non-zero exit code does not short-circuit; post-validation runs."""
        mock_validator = Mock()

        pre_report = Mock()
        pre_report.passed = True
        pre_report.to_dict.return_value = {"phase": "pre", "passed": True}
        mock_validator.validate_pre.return_value = pre_report

        post_report = Mock()
        post_report.passed = True
        post_report.phase = "post"
        post_report.to_dict.return_value = {"phase": "post", "passed": True}
        mock_validator.validate_post.return_value = post_report

        # Runner returns success=False (non-zero exit) but outputs exist
        mock_runner = Mock(
            return_value={
                "success": False,
                "exit_code": 1,
                "error": "heudiconv exited with code 1",
                "expected_outputs": {},
            }
        )

        inputs = MockInputs(participant="01", output_dir=tmp_path / "output")

        with (
            patch.dict(
                "voxelops.procedures.orchestrator.VALIDATORS",
                {"heudiconv": mock_validator},
            ),
            patch.dict(
                "voxelops.procedures.orchestrator.RUNNERS", {"heudiconv": mock_runner}
            ),
        ):
            result = run_procedure("heudiconv", inputs, log_dir=tmp_path / "logs")

        # Post-validation ran and passed → overall success
        assert result.status == "success"
        assert result.success is True
        mock_validator.validate_post.assert_called_once()

    def test_nonzero_exit_with_failed_post_validation(self, tmp_path):
        """Non-zero exit code + failing post-validation → post_validation_failed."""
        mock_validator = Mock()

        pre_report = Mock()
        pre_report.passed = True
        pre_report.to_dict.return_value = {"phase": "pre", "passed": True}
        mock_validator.validate_pre.return_value = pre_report

        post_report = Mock()
        post_report.passed = False
        post_report.phase = "post"
        post_report.to_dict.return_value = {
            "phase": "post",
            "passed": False,
            "errors": [{"message": "Output files not found"}],
        }
        mock_validator.validate_post.return_value = post_report

        mock_runner = Mock(
            return_value={
                "success": False,
                "exit_code": 1,
                "error": "heudiconv exited with code 1",
                "expected_outputs": {},
            }
        )

        inputs = MockInputs(participant="01", output_dir=tmp_path / "output")

        with (
            patch.dict(
                "voxelops.procedures.orchestrator.VALIDATORS",
                {"heudiconv": mock_validator},
            ),
            patch.dict(
                "voxelops.procedures.orchestrator.RUNNERS", {"heudiconv": mock_runner}
            ),
        ):
            result = run_procedure("heudiconv", inputs, log_dir=tmp_path / "logs")

        assert result.status == "post_validation_failed"
        assert result.success is False
        mock_validator.validate_post.assert_called_once()

    def test_audit_log_file_created(self, tmp_path):
        """Test that audit log file is created."""
        # Setup mocks
        mock_validator = Mock()

        pre_report = Mock()
        pre_report.passed = True
        pre_report.to_dict.return_value = {"phase": "pre", "passed": True}
        mock_validator.validate_pre.return_value = pre_report

        post_report = Mock()
        post_report.passed = True
        post_report.to_dict.return_value = {"phase": "post", "passed": True}
        mock_validator.validate_post.return_value = post_report

        mock_runner = Mock(
            return_value={
                "success": True,
                "expected_outputs": {},
            }
        )

        inputs = MockInputs(
            participant="01",
            output_dir=tmp_path / "output",
        )

        log_dir = tmp_path / "logs"

        # Patch VALIDATORS and RUNNERS
        with (
            patch.dict(
                "voxelops.procedures.orchestrator.VALIDATORS",
                {"heudiconv": mock_validator},
            ),
            patch.dict(
                "voxelops.procedures.orchestrator.RUNNERS", {"heudiconv": mock_runner}
            ),
        ):
            result = run_procedure("heudiconv", inputs, log_dir=log_dir)

        # Verify audit log file exists
        assert result.audit_log_file is not None
        audit_file = Path(result.audit_log_file)
        assert audit_file.exists()
        assert audit_file.parent == log_dir
        assert "sub-01_heudiconv_" in audit_file.name
