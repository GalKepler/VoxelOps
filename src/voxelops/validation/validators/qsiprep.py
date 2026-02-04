"""QSIPrep validator with pre and post validation rules."""

from voxelops.validation.rules.common import (
    DirectoryExistsRule,
    GlobFilesExistRule,
    OutputDirectoryExistsRule,
    ParticipantExistsRule,
)
from voxelops.validation.validators.base import Validator


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
        ),
        # Check for bval/bvec files
        GlobFilesExistRule(
            base_dir_attr="bids_dir",
            pattern="**/dwi/*_dwi.bval",
            min_count=1,
            file_type="b-value files",
        ),
        GlobFilesExistRule(
            base_dir_attr="bids_dir",
            pattern="**/dwi/*_dwi.bvec",
            min_count=1,
            file_type="b-vector files",
        ),
        # Anatomical reference
        GlobFilesExistRule(
            base_dir_attr="bids_dir",
            pattern="**/anat/*_T1w.nii.gz",
            min_count=1,
            file_type="T1w anatomical",
        ),
    ]

    post_rules = [
        # Output existence checks
        OutputDirectoryExistsRule("qsiprep_dir", "QSIPrep output directory"),
        OutputDirectoryExistsRule("participant_dir", "Participant output directory"),
    ]
