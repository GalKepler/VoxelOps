"""HeudiConv validator with pre and post validation rules."""

from voxelops.validation.rules.common import (
    DirectoryExistsRule,
    FileExistsRule,
    GlobFilesExistRule,
    OutputDirectoryExistsRule,
)
from voxelops.validation.validators.base import Validator


class HeudiConvValidator(Validator):
    """Validator for HeudiConv DICOM to BIDS conversion."""

    procedure_name = "heudiconv"

    pre_rules = [
        # Directory checks
        DirectoryExistsRule("dicom_dir", "DICOM directory"),
        FileExistsRule("heuristic", "Heuristic file", on_config=False),
        # Data existence checks
        GlobFilesExistRule(
            base_dir_attr="dicom_dir",
            pattern="**/*.dcm",
            min_count=1,
            file_type="DICOM files",
        ),
    ]

    post_rules = [
        # Output existence checks
        OutputDirectoryExistsRule("bids_dir", "BIDS directory"),
        OutputDirectoryExistsRule("participant_dir", "Participant directory"),
    ]
