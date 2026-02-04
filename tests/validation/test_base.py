"""Tests for base validation classes."""

from datetime import datetime

from voxelops.validation.base import (
    ValidationReport,
    ValidationResult,
    ValidationRule,
)
from voxelops.validation.context import ValidationContext


class TestValidationResult:
    """Tests for ValidationResult class."""

    def test_init(self):
        """Test basic initialization."""
        result = ValidationResult(
            rule_name="test_rule",
            rule_description="Test rule description",
            passed=True,
            severity="info",
            message="Test passed",
            details={"key": "value"},
        )
        assert result.rule_name == "test_rule"
        assert result.rule_description == "Test rule description"
        assert result.passed is True
        assert result.severity == "info"
        assert result.message == "Test passed"
        assert result.details == {"key": "value"}
        assert isinstance(result.timestamp, datetime)

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        result = ValidationResult(
            rule_name="test_rule",
            rule_description="Test rule",
            passed=False,
            severity="error",
            message="Test failed",
        )
        assert result.details == {}
        assert isinstance(result.timestamp, datetime)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        timestamp = datetime.now()
        result = ValidationResult(
            rule_name="test_rule",
            rule_description="Test rule description",
            passed=True,
            severity="warning",
            message="Test warning",
            details={"count": 42, "path": "/test"},
            timestamp=timestamp,
        )
        result_dict = result.to_dict()

        assert result_dict["rule_name"] == "test_rule"
        assert result_dict["rule_description"] == "Test rule description"
        assert result_dict["passed"] is True
        assert result_dict["severity"] == "warning"
        assert result_dict["message"] == "Test warning"
        assert result_dict["details"] == {"count": 42, "path": "/test"}
        assert result_dict["timestamp"] == timestamp.isoformat()

    def test_severity_types(self):
        """Test all severity types."""
        for severity in ["error", "warning", "info"]:
            result = ValidationResult(
                rule_name="test",
                rule_description="Test",
                passed=False,
                severity=severity,
                message="Test",
            )
            assert result.severity == severity


class TestValidationRule:
    """Tests for ValidationRule abstract base class."""

    def test_concrete_rule_implementation(self):
        """Test a concrete implementation of ValidationRule."""

        class TestRule(ValidationRule):
            name = "test_rule"
            description = "Test rule for testing"
            severity = "error"
            phase = "pre"

            def check(self, context: ValidationContext) -> ValidationResult:
                if context.participant == "pass":
                    return self._pass("Passed", {"status": "ok"})
                return self._fail("Failed", {"status": "fail"})

        rule = TestRule()
        assert rule.name == "test_rule"
        assert rule.description == "Test rule for testing"
        assert rule.severity == "error"
        assert rule.phase == "pre"

        # Test passing context
        context_pass = ValidationContext(procedure_name="test", participant="pass")
        result = rule.check(context_pass)
        assert result.passed is True
        assert result.message == "Passed"
        assert result.details == {"status": "ok"}
        assert result.rule_name == "test_rule"

        # Test failing context
        context_fail = ValidationContext(procedure_name="test", participant="fail")
        result = rule.check(context_fail)
        assert result.passed is False
        assert result.message == "Failed"
        assert result.details == {"status": "fail"}

    def test_skip_condition_default(self):
        """Test default skip_condition returns False."""

        class TestRule(ValidationRule):
            name = "test"
            description = "Test"

            def check(self, context: ValidationContext) -> ValidationResult:
                return self._pass("Ok")

        rule = TestRule()
        context = ValidationContext(procedure_name="test", participant="01")
        assert rule.skip_condition(context) is False

    def test_skip_condition_custom(self):
        """Test custom skip_condition implementation."""

        class ConditionalRule(ValidationRule):
            name = "conditional"
            description = "Conditional rule"

            def check(self, context: ValidationContext) -> ValidationResult:
                return self._pass("Ok")

            def skip_condition(self, context: ValidationContext) -> bool:
                # Skip if participant starts with "skip"
                return context.participant.startswith("skip")

        rule = ConditionalRule()

        context_run = ValidationContext(procedure_name="test", participant="01")
        assert rule.skip_condition(context_run) is False

        context_skip = ValidationContext(procedure_name="test", participant="skip_01")
        assert rule.skip_condition(context_skip) is True

    def test_pass_helper(self):
        """Test _pass helper method."""

        class TestRule(ValidationRule):
            name = "test"
            description = "Test rule"
            severity = "info"

            def check(self, context: ValidationContext) -> ValidationResult:
                return self._pass("Success", {"data": "value"})

        rule = TestRule()
        context = ValidationContext(procedure_name="test", participant="01")
        result = rule.check(context)

        assert result.passed is True
        assert result.rule_name == "test"
        assert result.rule_description == "Test rule"
        assert result.severity == "info"
        assert result.message == "Success"
        assert result.details == {"data": "value"}

    def test_pass_helper_no_details(self):
        """Test _pass helper without details."""

        class TestRule(ValidationRule):
            name = "test"
            description = "Test rule"

            def check(self, context: ValidationContext) -> ValidationResult:
                return self._pass("Success")

        rule = TestRule()
        context = ValidationContext(procedure_name="test", participant="01")
        result = rule.check(context)

        assert result.passed is True
        assert result.details == {}

    def test_fail_helper(self):
        """Test _fail helper method."""

        class TestRule(ValidationRule):
            name = "test"
            description = "Test rule"
            severity = "error"

            def check(self, context: ValidationContext) -> ValidationResult:
                return self._fail("Failure", {"error": "reason"})

        rule = TestRule()
        context = ValidationContext(procedure_name="test", participant="01")
        result = rule.check(context)

        assert result.passed is False
        assert result.rule_name == "test"
        assert result.rule_description == "Test rule"
        assert result.severity == "error"
        assert result.message == "Failure"
        assert result.details == {"error": "reason"}

    def test_fail_helper_no_details(self):
        """Test _fail helper without details."""

        class TestRule(ValidationRule):
            name = "test"
            description = "Test rule"

            def check(self, context: ValidationContext) -> ValidationResult:
                return self._fail("Failure")

        rule = TestRule()
        context = ValidationContext(procedure_name="test", participant="01")
        result = rule.check(context)

        assert result.passed is False
        assert result.details == {}

    def test_phase_attribute(self):
        """Test phase attribute values."""

        class PreRule(ValidationRule):
            name = "pre"
            description = "Pre rule"
            phase = "pre"

            def check(self, context: ValidationContext) -> ValidationResult:
                return self._pass("Ok")

        class PostRule(ValidationRule):
            name = "post"
            description = "Post rule"
            phase = "post"

            def check(self, context: ValidationContext) -> ValidationResult:
                return self._pass("Ok")

        pre_rule = PreRule()
        post_rule = PostRule()

        assert pre_rule.phase == "pre"
        assert post_rule.phase == "post"


class TestValidationReport:
    """Tests for ValidationReport class."""

    def test_init(self):
        """Test basic initialization."""
        result = ValidationResult(
            rule_name="test",
            rule_description="Test",
            passed=True,
            severity="info",
            message="Test",
        )
        report = ValidationReport(
            phase="pre",
            procedure="qsiprep",
            participant="01",
            session="01",
            results=[result],
        )
        assert report.phase == "pre"
        assert report.procedure == "qsiprep"
        assert report.participant == "01"
        assert report.session == "01"
        assert len(report.results) == 1
        assert isinstance(report.timestamp, datetime)

    def test_init_no_session(self):
        """Test initialization without session."""
        report = ValidationReport(
            phase="post",
            procedure="qsiprep",
            participant="01",
            session=None,
        )
        assert report.session is None

    def test_passed_property_all_passed(self):
        """Test passed property when all checks pass."""
        results = [
            ValidationResult("r1", "Rule 1", True, "info", "Passed 1"),
            ValidationResult("r2", "Rule 2", True, "warning", "Passed 2"),
        ]
        report = ValidationReport(
            phase="pre",
            procedure="test",
            participant="01",
            session=None,
            results=results,
        )
        assert report.passed is True

    def test_passed_property_with_warnings(self):
        """Test passed property with failed warnings."""
        results = [
            ValidationResult("r1", "Rule 1", True, "info", "Passed"),
            ValidationResult("r2", "Rule 2", False, "warning", "Warning"),
        ]
        report = ValidationReport(
            phase="pre",
            procedure="test",
            participant="01",
            session=None,
            results=results,
        )
        # Should still pass because warnings don't fail the report
        assert report.passed is True

    def test_passed_property_with_errors(self):
        """Test passed property with failed errors."""
        results = [
            ValidationResult("r1", "Rule 1", True, "info", "Passed"),
            ValidationResult("r2", "Rule 2", False, "error", "Error"),
        ]
        report = ValidationReport(
            phase="pre",
            procedure="test",
            participant="01",
            session=None,
            results=results,
        )
        assert report.passed is False

    def test_errors_property(self):
        """Test errors property."""
        results = [
            ValidationResult("r1", "R1", True, "error", "Pass"),
            ValidationResult("r2", "R2", False, "error", "Fail"),
            ValidationResult("r3", "R3", False, "warning", "Warn"),
            ValidationResult("r4", "R4", False, "error", "Fail2"),
        ]
        report = ValidationReport(
            phase="pre",
            procedure="test",
            participant="01",
            session=None,
            results=results,
        )
        errors = report.errors
        assert len(errors) == 2
        assert all(e.severity == "error" and not e.passed for e in errors)
        assert errors[0].rule_name == "r2"
        assert errors[1].rule_name == "r4"

    def test_warnings_property(self):
        """Test warnings property."""
        results = [
            ValidationResult("r1", "R1", True, "warning", "Pass"),
            ValidationResult("r2", "R2", False, "warning", "Warn"),
            ValidationResult("r3", "R3", False, "error", "Err"),
            ValidationResult("r4", "R4", False, "warning", "Warn2"),
        ]
        report = ValidationReport(
            phase="pre",
            procedure="test",
            participant="01",
            session=None,
            results=results,
        )
        warnings = report.warnings
        assert len(warnings) == 2
        assert all(w.severity == "warning" and not w.passed for w in warnings)
        assert warnings[0].rule_name == "r2"
        assert warnings[1].rule_name == "r4"

    def test_passed_checks_property(self):
        """Test passed_checks property."""
        results = [
            ValidationResult("r1", "R1", True, "error", "Pass"),
            ValidationResult("r2", "R2", False, "error", "Fail"),
            ValidationResult("r3", "R3", True, "warning", "Pass"),
            ValidationResult("r4", "R4", False, "warning", "Fail"),
        ]
        report = ValidationReport(
            phase="pre",
            procedure="test",
            participant="01",
            session=None,
            results=results,
        )
        passed = report.passed_checks
        assert len(passed) == 2
        assert all(p.passed for p in passed)
        assert passed[0].rule_name == "r1"
        assert passed[1].rule_name == "r3"

    def test_to_dict(self):
        """Test to_dict conversion."""
        timestamp = datetime.now()
        results = [
            ValidationResult("r1", "R1", True, "info", "Pass"),
            ValidationResult("r2", "R2", False, "error", "Fail"),
            ValidationResult("r3", "R3", False, "warning", "Warn"),
        ]
        report = ValidationReport(
            phase="post",
            procedure="qsiprep",
            participant="01",
            session="01",
            timestamp=timestamp,
            results=results,
        )
        report_dict = report.to_dict()

        assert report_dict["phase"] == "post"
        assert report_dict["procedure"] == "qsiprep"
        assert report_dict["participant"] == "01"
        assert report_dict["session"] == "01"
        assert report_dict["timestamp"] == timestamp.isoformat()
        assert report_dict["passed"] is False
        assert report_dict["total_checks"] == 3
        assert report_dict["error_count"] == 1
        assert report_dict["warning_count"] == 1
        assert report_dict["passed_count"] == 1
        assert len(report_dict["results"]) == 3
        assert isinstance(report_dict["results"][0], dict)

    def test_summary_passed(self):
        """Test summary method when passed."""
        results = [
            ValidationResult("r1", "R1", True, "info", "Pass"),
            ValidationResult("r2", "R2", True, "info", "Pass"),
        ]
        report = ValidationReport(
            phase="pre",
            procedure="test",
            participant="01",
            session=None,
            results=results,
        )
        summary = report.summary()
        assert "PRE validation PASSED" in summary
        assert "2 passed" in summary
        assert "0 errors" in summary
        assert "0 warnings" in summary

    def test_summary_failed(self):
        """Test summary method when failed."""
        results = [
            ValidationResult("r1", "R1", True, "info", "Pass"),
            ValidationResult("r2", "R2", False, "error", "Fail"),
            ValidationResult("r3", "R3", False, "warning", "Warn"),
        ]
        report = ValidationReport(
            phase="post",
            procedure="test",
            participant="01",
            session=None,
            results=results,
        )
        summary = report.summary()
        assert "POST validation FAILED" in summary
        assert "1 passed" in summary
        assert "1 errors" in summary
        assert "1 warnings" in summary

    def test_empty_report(self):
        """Test report with no results."""
        report = ValidationReport(
            phase="pre",
            procedure="test",
            participant="01",
            session=None,
            results=[],
        )
        assert report.passed is True
        assert len(report.errors) == 0
        assert len(report.warnings) == 0
        assert len(report.passed_checks) == 0
        assert "0 passed" in report.summary()
