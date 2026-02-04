"""QSIRecon validator with pre and post validation rules."""

from voxelops.validation.base import ValidationResult, ValidationRule
from voxelops.validation.context import ValidationContext
from voxelops.validation.rules.common import (
    DirectoryExistsRule,
    GlobFilesExistRule,
    OutputDirectoryExistsRule,
    ParticipantExistsRule,
)
from voxelops.validation.validators.base import Validator


class WorkflowReportsExistRule(ValidationRule):
    """Check that workflow HTML reports exist for all expected workflows and sessions."""

    name = "workflow_reports_exist"
    description = "Check workflow HTML reports exist"
    severity = "error"

    def check(self, context: ValidationContext) -> ValidationResult:
        """Check that all expected workflow HTML reports exist."""
        if not context.expected_outputs:
            return self._fail("No expected outputs available")

        workflow_reports = context.expected_outputs.workflow_reports
        missing_reports = []
        found_reports = []

        for workflow_name, session_reports in workflow_reports.items():
            for session_id, html_path in session_reports.items():
                session_label = f"ses-{session_id}" if session_id else "no-session"
                report_label = f"{workflow_name}/{session_label}"

                if html_path.exists():
                    found_reports.append(report_label)
                else:
                    missing_reports.append(f"{report_label} ({html_path})")

        if missing_reports:
            return self._fail(
                f"Missing {len(missing_reports)} workflow report(s)",
                details={
                    "missing_reports": missing_reports,
                    "found_reports": found_reports,
                },
            )

        return self._pass(
            f"All {len(found_reports)} workflow HTML reports exist",
            details={"found_reports": found_reports},
        )


class QSIReconValidator(Validator):
    """Validator for QSIRecon diffusion reconstruction and connectivity."""

    procedure_name = "qsirecon"

    pre_rules = [
        # Directory checks - QSIRecon takes QSIPrep output as input
        DirectoryExistsRule("qsiprep_dir", "QSIPrep directory"),
        ParticipantExistsRule(),
        # Check for preprocessed DWI from QSIPrep
        GlobFilesExistRule(
            base_dir_attr="qsiprep_dir",
            pattern="**/dwi/*_desc-preproc_dwi.nii.gz",
            min_count=1,
            file_type="Preprocessed DWI",
            participant_level=True,
        ),
        # Check for QSIPrep confounds
        GlobFilesExistRule(
            base_dir_attr="qsiprep_dir",
            pattern="**/dwi/*-image_qc.tsv",
            min_count=1,
            file_type="QSIPrep QC files",
            participant_level=True,
        ),
    ]

    post_rules = [
        # Output existence checks
        OutputDirectoryExistsRule("qsirecon_dir", "QSIRecon output directory"),
        # OutputDirectoryExistsRule("participant_dir", "Participant output directory"),
        # Check for workflow HTML reports
        # WorkflowReportsExistRule(),
        # Check for reconstructed outputs (varies by reconstruction method)
        # Using a general check for any output files
        # GlobFilesExistRule(
        #     base_dir_attr="participant_dir",
        #     pattern="**/*.nii.gz",
        #     min_count=1,
        #     file_type="Reconstruction outputs",
        #     phase="post",
        #     participant_level=False,  # participant_dir is already participant-specific
        # ),
    ]
