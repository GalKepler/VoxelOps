"""QSIPrep validator with pre and post validation rules."""

from voxelops.validation.base import ValidationResult, ValidationRule
from voxelops.validation.context import ValidationContext
from voxelops.validation.rules.common import (
    DirectoryExistsRule,
    GlobFilesExistRule,
    OutputDirectoryExistsRule,
    ParticipantExistsRule,
)
from voxelops.validation.validators.base import Validator


class HtmlReportExistsRule(ValidationRule):
    """Check that the HTML report exists."""

    name = "html_report_exists"
    description = "Check HTML report exists"
    severity = "error"

    def check(self, context: ValidationContext) -> ValidationResult:
        """Check that the expected HTML report exists."""
        if not context.expected_outputs:
            return self._fail("No expected outputs available")

        html_report = context.expected_outputs.html_report

        if html_report.exists():
            return self._pass(
                f"HTML report exists: {html_report}",
                details={"html_report": str(html_report)},
            )
        else:
            return self._fail(
                f"HTML report not found: {html_report}",
                details={"html_report": str(html_report)},
            )


class QSIPrepValidator(Validator):
    """Validator for QSIPrep diffusion MRI preprocessing."""

    procedure_name = "qsiprep"

    pre_rules = [
        # Directory checks
        DirectoryExistsRule("bids_dir", "BIDS directory"),
        ParticipantExistsRule(),
        # DWI data checks - using **/ to handle both session and non-session datasets
        GlobFilesExistRule(
            base_dir_attr="bids_dir",
            pattern="**/dwi/*_dwi.nii.gz",
            min_count=1,
            file_type="DWI files",
            participant_level=True,
        ),
        # Check for bval/bvec files
        GlobFilesExistRule(
            base_dir_attr="bids_dir",
            pattern="**/dwi/*_dwi.bval",
            min_count=1,
            file_type="b-value files",
            participant_level=True,
        ),
        GlobFilesExistRule(
            base_dir_attr="bids_dir",
            pattern="**/dwi/*_dwi.bvec",
            min_count=1,
            file_type="b-vector files",
            participant_level=True,
        ),
        # Anatomical reference
        GlobFilesExistRule(
            base_dir_attr="bids_dir",
            pattern="**/anat/*_T1w.nii.gz",
            min_count=1,
            file_type="T1w anatomical",
            participant_level=True,
        ),
    ]

    post_rules = [
        # Output existence checks
        OutputDirectoryExistsRule("qsiprep_dir", "QSIPrep output directory"),
        OutputDirectoryExistsRule("participant_dir", "Participant output directory"),
        HtmlReportExistsRule(),
    ]
