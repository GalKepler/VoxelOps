"""Integration tests for the complete validation framework."""

from dataclasses import dataclass
from pathlib import Path
from unittest.mock import Mock, patch

import voxelops


class TestPackageImports:
    """Test that all key components are importable from main package."""

    def test_basic_runners_importable(self):
        """Test that basic runners are accessible."""
        assert hasattr(voxelops, "run_heudiconv")
        assert hasattr(voxelops, "run_qsiprep")
        assert hasattr(voxelops, "run_qsirecon")
        assert hasattr(voxelops, "run_qsiparc")

    def test_orchestration_importable(self):
        """Test that orchestration functions are accessible."""
        assert hasattr(voxelops, "run_procedure")
        assert hasattr(voxelops, "ProcedureResult")

    def test_validation_importable(self):
        """Test that validation classes are accessible."""
        assert hasattr(voxelops, "ValidationResult")
        assert hasattr(voxelops, "ValidationReport")
        assert hasattr(voxelops, "ValidationContext")
        assert hasattr(voxelops, "HeudiConvValidator")
        assert hasattr(voxelops, "QSIPrepValidator")
        assert hasattr(voxelops, "QSIReconValidator")
        assert hasattr(voxelops, "QSIParcValidator")

    def test_audit_importable(self):
        """Test that audit classes are accessible."""
        assert hasattr(voxelops, "AuditEventType")
        assert hasattr(voxelops, "AuditRecord")
        assert hasattr(voxelops, "AuditLogger")

    def test_schemas_importable(self):
        """Test that schemas are still accessible."""
        assert hasattr(voxelops, "HeudiconvInputs")
        assert hasattr(voxelops, "QSIPrepInputs")
        assert hasattr(voxelops, "QSIReconInputs")
        assert hasattr(voxelops, "QSIParcInputs")


@dataclass
class MockInputs:
    """Mock inputs for integration testing."""

    participant: str
    session: str | None = None
    bids_dir: Path | None = None
    output_dir: Path | None = None


class TestEndToEndIntegration:
    """Test end-to-end integration of validation framework."""

    def test_run_procedure_with_validation(self, tmp_path):
        """Test running a procedure with full validation."""
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
                {"qsiprep": mock_validator},
            ),
            patch.dict(
                "voxelops.procedures.orchestrator.RUNNERS", {"qsiprep": mock_runner}
            ),
        ):
            # Run procedure using the imported function
            result = voxelops.run_procedure(
                "qsiprep", inputs, log_dir=tmp_path / "logs"
            )

        # Verify result
        assert isinstance(result, voxelops.ProcedureResult)
        assert result.status == "success"
        assert result.success is True
        assert result.procedure == "qsiprep"
        assert result.participant == "01"
        assert result.pre_validation is not None
        assert result.post_validation is not None
        assert result.audit_log_file is not None

    def test_validators_instantiated(self):
        """Test that validators are properly instantiated."""
        # Get validators from the orchestrator
        from voxelops.procedures.orchestrator import VALIDATORS

        assert "heudiconv" in VALIDATORS
        assert "qsiprep" in VALIDATORS
        assert "qsirecon" in VALIDATORS
        assert "qsiparc" in VALIDATORS

        # Verify they're instances of the correct classes
        assert isinstance(VALIDATORS["heudiconv"], voxelops.HeudiConvValidator)
        assert isinstance(VALIDATORS["qsiprep"], voxelops.QSIPrepValidator)
        assert isinstance(VALIDATORS["qsirecon"], voxelops.QSIReconValidator)
        assert isinstance(VALIDATORS["qsiparc"], voxelops.QSIParcValidator)

    def test_validation_result_serialization(self):
        """Test that validation results can be serialized."""
        result = voxelops.ValidationResult(
            rule_name="test_rule",
            rule_description="Test rule",
            passed=True,
            severity="error",
            message="Test passed",
        )

        data = result.to_dict()
        assert data["rule_name"] == "test_rule"
        assert data["passed"] is True
        assert "timestamp" in data

    def test_audit_logger_creates_log(self, tmp_path):
        """Test that audit logger creates log files."""
        logger = voxelops.AuditLogger(
            log_dir=tmp_path / "logs",
            procedure="qsiprep",
            participant="01",
        )

        logger.log(voxelops.AuditEventType.PROCEDURE_START, {"test": "data"})

        # Verify log file was created
        log_files = list((tmp_path / "logs").glob("*.jsonl"))
        assert len(log_files) == 1
        assert "sub-01_qsiprep_" in log_files[0].name
