"""Base validator class for neuroimaging procedures.

This module provides the Validator base class that all procedure-specific
validators inherit from. Each validator defines validation rules for
pre-execution (input checking) and post-execution (output verification).
"""

from abc import ABC
from typing import List

from voxelops.validation.base import ValidationReport, ValidationRule
from voxelops.validation.context import ValidationContext


class Validator(ABC):
    """Base validator class for neuroimaging procedures.

    Subclass this to create procedure-specific validators (e.g., QSIPrepValidator,
    QSIReconValidator). Define validation rules by populating the pre_rules and
    post_rules class attributes.

    Attributes
    ----------
    procedure_name : str
        Name of the procedure (e.g., "qsiprep", "qsirecon").
        Must match the procedure name used in the orchestrator registry.
    pre_rules : List[ValidationRule]
        Rules to run before execution. These check inputs, verify files exist,
        and ensure the environment is ready for execution.
    post_rules : List[ValidationRule]
        Rules to run after execution. These verify expected outputs were created
        and check output integrity.

    Methods
    -------
    validate_pre(context)
        Run all pre-validation rules and return a report
    validate_post(context)
        Run all post-validation rules and return a report
    validate_all(context)
        Run both pre and post validation, return both reports

    Examples
    --------
    Creating a new validator:

    >>> from voxelops.validation.validators.base import Validator
    >>> from voxelops.validation.rules.common import (
    ...     DirectoryExistsRule,
    ...     ParticipantExistsRule,
    ...     OutputDirectoryExistsRule,
    ... )
    >>>
    >>> class MyToolValidator(Validator):
    ...     '''Validator for MyTool procedure.'''
    ...
    ...     procedure_name = "mytool"
    ...
    ...     pre_rules = [
    ...         DirectoryExistsRule("bids_dir", "BIDS directory"),
    ...         ParticipantExistsRule(),
    ...     ]
    ...
    ...     post_rules = [
    ...         OutputDirectoryExistsRule("output_dir", "Output directory"),
    ...     ]

    Using a validator:

    >>> from voxelops.validation.context import ValidationContext
    >>> from voxelops.validation.validators import QSIPrepValidator
    >>>
    >>> validator = QSIPrepValidator()
    >>> context = ValidationContext(
    ...     procedure_name="qsiprep",
    ...     participant="01",
    ...     inputs=inputs,
    ... )
    >>>
    >>> # Run pre-validation
    >>> pre_report = validator.validate_pre(context)
    >>> if not pre_report.passed:
    ...     print("Pre-validation failed!")
    ...     for error in pre_report.errors:
    ...         print(f"  - {error.message}")

    Notes
    -----
    - Rules are executed in the order they appear in the pre_rules/post_rules lists
    - If a rule's skip_condition() returns True, it is skipped
    - Warnings don't block execution, but errors do (via the orchestrator)
    - All validation results are logged to audit files
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
