"""QSIParc validator with pre and post validation rules."""

from voxelops.validation.rules.common import (
    DirectoryExistsRule,
    GlobFilesExistRule,
    OutputDirectoryExistsRule,
    ParticipantExistsRule,
)
from voxelops.validation.validators.base import Validator


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
        # Check for parcellation outputs
        GlobFilesExistRule(
            base_dir_attr="output_dir",
            pattern="**/*_parcellated.csv",
            min_count=1,
            file_type="Parcellation results",
            phase="post",
        ),
    ]
