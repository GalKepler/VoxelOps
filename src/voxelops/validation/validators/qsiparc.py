"""QSIParc validator with pre and post validation rules."""

from voxelops.validation.base import ValidationResult, ValidationRule
from voxelops.validation.context import ValidationContext
from voxelops.validation.rules.common import (
    DirectoryExistsRule,
    GlobFilesExistRule,
    OutputDirectoryExistsRule,
    ParticipantExistsRule,
)
from voxelops.validation.validators.base import Validator


class WorkflowDirsExistRule(ValidationRule):
    """Check that workflow dwi directories exist for all expected workflows and sessions."""

    name = "workflow_dirs_exist"
    description = "Check workflow dwi directories exist"
    severity = "error"

    def check(self, context: ValidationContext) -> ValidationResult:
        """Check that all expected workflow dwi directories exist."""
        if not context.expected_outputs:
            return self._fail("No expected outputs available")

        workflow_dirs = context.expected_outputs.workflow_dirs
        missing_dirs = []
        found_dirs = []

        for workflow_name, session_dirs in workflow_dirs.items():
            for session_id, dwi_dir in session_dirs.items():
                session_label = f"ses-{session_id}" if session_id else "no-session"
                dir_label = f"{workflow_name}/{session_label}"

                if dwi_dir.exists():
                    found_dirs.append(dir_label)
                else:
                    missing_dirs.append(f"{dir_label} ({dwi_dir})")

        if missing_dirs:
            return self._fail(
                f"Missing {len(missing_dirs)} workflow dwi director(ies)",
                details={
                    "missing_dirs": missing_dirs,
                    "found_dirs": found_dirs,
                },
            )

        return self._pass(
            f"All {len(found_dirs)} workflow dwi directories exist",
            details={"found_dirs": found_dirs},
        )


class QSIParcValidator(Validator):
    """Validator for QSIParc parcellation."""

    procedure_name = "qsiparc"

    pre_rules = [
        # Directory checks - QSIParc takes QSIRecon output as input
        DirectoryExistsRule("qsirecon_dir", "QSIRecon directory"),
        ParticipantExistsRule(),
        # Check for required input files from QSIRecon
        GlobFilesExistRule(
            base_dir_attr="qsirecon_dir",
            pattern="**/*.nii.gz",
            min_count=1,
            file_type="Reconstruction files",
        ),
    ]

    post_rules = [
        # Output existence checks
        OutputDirectoryExistsRule("output_dir", "Parcellation output directory"),
        # Check for workflow dwi directories
        WorkflowDirsExistRule(),
        # Check for parcellation output files (TSV files)
        GlobFilesExistRule(
            base_dir_attr="output_dir",
            pattern="**/*.tsv",
            min_count=1,
            file_type="Parcellation TSV files",
            phase="post",
            participant_level=False,
        ),
    ]
