"""Tests for Validator base class."""

from voxelops.validation.base import ValidationResult, ValidationRule
from voxelops.validation.context import ValidationContext
from voxelops.validation.validators.base import Validator


class AlwaysPassRule(ValidationRule):
    """Rule that always passes."""

    name = "always_pass"
    description = "Always passes"
    severity = "info"
    phase = "pre"

    def check(self, context: ValidationContext) -> ValidationResult:
        return self._pass("Passed", {"test": "data"})


class AlwaysFailRule(ValidationRule):
    """Rule that always fails."""

    name = "always_fail"
    description = "Always fails"
    severity = "error"
    phase = "pre"

    def check(self, context: ValidationContext) -> ValidationResult:
        return self._fail("Failed", {"reason": "test failure"})


class WarningRule(ValidationRule):
    """Rule that always fails with warning."""

    name = "warning_rule"
    description = "Warning rule"
    severity = "warning"
    phase = "pre"

    def check(self, context: ValidationContext) -> ValidationResult:
        return self._fail("Warning issued", {"warning": "test warning"})


class ConditionalRule(ValidationRule):
    """Rule that skips based on condition."""

    name = "conditional"
    description = "Conditional rule"
    severity = "info"
    phase = "pre"

    def check(self, context: ValidationContext) -> ValidationResult:
        return self._pass("Conditional passed")

    def skip_condition(self, context: ValidationContext) -> bool:
        # Skip if participant starts with "skip"
        return context.participant.startswith("skip")


class PostValidationRule(ValidationRule):
    """Post-validation rule."""

    name = "post_rule"
    description = "Post validation rule"
    severity = "error"
    phase = "post"

    def check(self, context: ValidationContext) -> ValidationResult:
        if context.execution_result and context.execution_result.get("success"):
            return self._pass("Post validation passed")
        return self._fail("Post validation failed")


class TestValidator:
    """Tests for Validator base class."""

    def test_validator_attributes(self):
        """Test validator has required attributes."""
        validator = Validator()
        assert hasattr(validator, "procedure_name")
        assert hasattr(validator, "pre_rules")
        assert hasattr(validator, "post_rules")
        assert validator.procedure_name == "unknown"
        assert validator.pre_rules == []
        assert validator.post_rules == []

    def test_custom_validator_subclass(self):
        """Test creating a custom validator."""

        class CustomValidator(Validator):
            procedure_name = "custom"
            pre_rules = [AlwaysPassRule()]
            post_rules = []

        validator = CustomValidator()
        assert validator.procedure_name == "custom"
        assert len(validator.pre_rules) == 1
        assert len(validator.post_rules) == 0

    def test_validate_pre_empty_rules(self):
        """Test validate_pre with no rules."""
        validator = Validator()
        context = ValidationContext(procedure_name="test", participant="01")

        report = validator.validate_pre(context)

        assert report.phase == "pre"
        assert report.procedure == "unknown"
        assert report.participant == "01"
        assert report.session is None
        assert len(report.results) == 0
        assert report.passed is True

    def test_validate_pre_single_passing_rule(self):
        """Test validate_pre with single passing rule."""

        class TestValidator(Validator):
            procedure_name = "test"
            pre_rules = [AlwaysPassRule()]

        validator = TestValidator()
        context = ValidationContext(procedure_name="test", participant="01")

        report = validator.validate_pre(context)

        assert report.phase == "pre"
        assert report.procedure == "test"
        assert len(report.results) == 1
        assert report.results[0].passed is True
        assert report.results[0].rule_name == "always_pass"
        assert report.passed is True

    def test_validate_pre_single_failing_rule(self):
        """Test validate_pre with single failing rule."""

        class TestValidator(Validator):
            procedure_name = "test"
            pre_rules = [AlwaysFailRule()]

        validator = TestValidator()
        context = ValidationContext(procedure_name="test", participant="01")

        report = validator.validate_pre(context)

        assert report.phase == "pre"
        assert len(report.results) == 1
        assert report.results[0].passed is False
        assert report.results[0].rule_name == "always_fail"
        assert report.passed is False
        assert len(report.errors) == 1

    def test_validate_pre_multiple_rules(self):
        """Test validate_pre with multiple rules."""

        class TestValidator(Validator):
            procedure_name = "test"
            pre_rules = [AlwaysPassRule(), AlwaysFailRule(), WarningRule()]

        validator = TestValidator()
        context = ValidationContext(procedure_name="test", participant="01")

        report = validator.validate_pre(context)

        assert len(report.results) == 3
        assert report.passed is False  # Has error
        assert len(report.errors) == 1
        assert len(report.warnings) == 1
        assert len(report.passed_checks) == 1

    def test_validate_pre_with_skip_condition(self):
        """Test validate_pre respects skip_condition."""

        class TestValidator(Validator):
            procedure_name = "test"
            pre_rules = [ConditionalRule(), AlwaysPassRule()]

        validator = TestValidator()

        # Rule should run
        context_run = ValidationContext(procedure_name="test", participant="01")
        report_run = validator.validate_pre(context_run)
        assert len(report_run.results) == 2

        # Rule should be skipped
        context_skip = ValidationContext(procedure_name="test", participant="skip_01")
        report_skip = validator.validate_pre(context_skip)
        assert len(report_skip.results) == 1
        assert report_skip.results[0].rule_name == "always_pass"

    def test_validate_pre_with_session(self):
        """Test validate_pre includes session in report."""

        class TestValidator(Validator):
            procedure_name = "test"
            pre_rules = [AlwaysPassRule()]

        validator = TestValidator()
        context = ValidationContext(
            procedure_name="test", participant="01", session="baseline"
        )

        report = validator.validate_pre(context)

        assert report.session == "baseline"

    def test_validate_post_empty_rules(self):
        """Test validate_post with no rules."""
        validator = Validator()
        context = ValidationContext(procedure_name="test", participant="01")

        report = validator.validate_post(context)

        assert report.phase == "post"
        assert report.procedure == "unknown"
        assert len(report.results) == 0
        assert report.passed is True

    def test_validate_post_with_rules(self):
        """Test validate_post with rules."""

        class TestValidator(Validator):
            procedure_name = "test"
            post_rules = [PostValidationRule()]

        validator = TestValidator()
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            execution_result={"success": True},
        )

        report = validator.validate_post(context)

        assert report.phase == "post"
        assert len(report.results) == 1
        assert report.results[0].passed is True

    def test_validate_post_failure(self):
        """Test validate_post with failing rule."""

        class TestValidator(Validator):
            procedure_name = "test"
            post_rules = [PostValidationRule()]

        validator = TestValidator()
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            execution_result={"success": False},
        )

        report = validator.validate_post(context)

        assert report.phase == "post"
        assert len(report.results) == 1
        assert report.results[0].passed is False
        assert report.passed is False

    def test_validate_all(self):
        """Test validate_all runs both pre and post."""

        class TestValidator(Validator):
            procedure_name = "test"
            pre_rules = [AlwaysPassRule()]
            post_rules = [PostValidationRule()]

        validator = TestValidator()
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            execution_result={"success": True},
        )

        pre_report, post_report = validator.validate_all(context)

        assert pre_report.phase == "pre"
        assert post_report.phase == "post"
        assert len(pre_report.results) == 1
        assert len(post_report.results) == 1
        assert pre_report.passed is True
        assert post_report.passed is True

    def test_validate_all_with_failures(self):
        """Test validate_all with failures in both phases."""

        class TestValidator(Validator):
            procedure_name = "test"
            pre_rules = [AlwaysFailRule()]
            post_rules = [PostValidationRule()]

        validator = TestValidator()
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            execution_result={"success": False},
        )

        pre_report, post_report = validator.validate_all(context)

        assert pre_report.passed is False
        assert post_report.passed is False
        assert len(pre_report.errors) == 1
        assert len(post_report.errors) == 1

    def test_rules_order_preserved(self):
        """Test that rules are executed in order."""

        rule_order = []

        class OrderedRule1(ValidationRule):
            name = "rule_1"
            description = "First rule"

            def check(self, context):
                rule_order.append(1)
                return self._pass("Rule 1")

        class OrderedRule2(ValidationRule):
            name = "rule_2"
            description = "Second rule"

            def check(self, context):
                rule_order.append(2)
                return self._pass("Rule 2")

        class OrderedRule3(ValidationRule):
            name = "rule_3"
            description = "Third rule"

            def check(self, context):
                rule_order.append(3)
                return self._pass("Rule 3")

        class TestValidator(Validator):
            procedure_name = "test"
            pre_rules = [OrderedRule1(), OrderedRule2(), OrderedRule3()]

        validator = TestValidator()
        context = ValidationContext(procedure_name="test", participant="01")

        rule_order.clear()
        report = validator.validate_pre(context)

        assert rule_order == [1, 2, 3]
        assert [r.rule_name for r in report.results] == ["rule_1", "rule_2", "rule_3"]

    def test_empty_validator_inheritance(self):
        """Test that empty subclass inherits correctly."""

        class EmptyValidator(Validator):
            pass

        validator = EmptyValidator()
        context = ValidationContext(procedure_name="test", participant="01")

        pre_report = validator.validate_pre(context)
        post_report = validator.validate_post(context)

        assert pre_report.procedure == "unknown"
        assert post_report.procedure == "unknown"
        assert len(pre_report.results) == 0
        assert len(post_report.results) == 0
