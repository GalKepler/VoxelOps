"""Base validator class."""

from abc import ABC
from typing import List

from voxelops.validation.base import ValidationReport, ValidationRule
from voxelops.validation.context import ValidationContext


class Validator(ABC):
    """Base validator class for a procedure.

    Subclass this for each procedure (HeudiConv, QSIPrep, etc.)
    and define the pre_rules and post_rules lists.
    """

    procedure_name: str = "unknown"
    pre_rules: List[ValidationRule] = []
    post_rules: List[ValidationRule] = []

    def validate_pre(self, context: ValidationContext) -> ValidationReport:
        """Run all pre-validation rules.

        Parameters
        ----------
        context : ValidationContext
            Validation context with inputs and config.

        Returns
        -------
        ValidationReport
            Report with all pre-validation results.
        """
        results = []
        for rule in self.pre_rules:
            if not rule.skip_condition(context):
                result = rule.check(context)
                results.append(result)

        return ValidationReport(
            phase="pre",
            procedure=self.procedure_name,
            participant=context.participant,
            session=context.session,
            results=results,
        )

    def validate_post(self, context: ValidationContext) -> ValidationReport:
        """Run all post-validation rules.

        Parameters
        ----------
        context : ValidationContext
            Validation context with execution results and expected outputs.

        Returns
        -------
        ValidationReport
            Report with all post-validation results.
        """
        results = []
        for rule in self.post_rules:
            if not rule.skip_condition(context):
                result = rule.check(context)
                results.append(result)

        return ValidationReport(
            phase="post",
            procedure=self.procedure_name,
            participant=context.participant,
            session=context.session,
            results=results,
        )

    def validate_all(
        self, context: ValidationContext
    ) -> tuple[ValidationReport, ValidationReport]:
        """Run both pre and post validation.

        Returns
        -------
        tuple[ValidationReport, ValidationReport]
            (pre_report, post_report)
        """
        return self.validate_pre(context), self.validate_post(context)
