"""FreeSurfer validators with pre and post validation rules."""

from voxelops.validation.rules.common import (
    DirectoryExistsRule,
    ExpectedOutputsExistRule,
    GlobFilesExistRule,
    OutputDirectoryExistsRule,
    ParticipantExistsRule,
)
from voxelops.validation.validators.base import Validator


class FreeSurferValidator(Validator):
    """Validator for FreeSurfer cortical reconstruction (recon-all)."""

    procedure_name = "freesurfer"

    pre_rules = [
        DirectoryExistsRule("bids_dir", "BIDS directory"),
        ParticipantExistsRule(),
        GlobFilesExistRule(
            base_dir_attr="bids_dir",
            pattern="**/anat/*_T1w.nii.gz",
            min_count=1,
            file_type="T1w anatomical",
            participant_level=True,
        ),
    ]

    post_rules = [
        OutputDirectoryExistsRule("subject_dir", "FreeSurfer subject directory"),
        OutputDirectoryExistsRule("mri_dir", "mri directory"),
        OutputDirectoryExistsRule("surf_dir", "surf directory"),
        ExpectedOutputsExistRule(
            outputs_attr="recon_done_flag",
            item_type="recon-all completion flag",
        ),
        GlobFilesExistRule(
            base_dir_attr="mri_dir",
            pattern="aparc+aseg.mgz",
            min_count=1,
            file_type="aparc+aseg parcellation",
            phase="post",
            participant_level=False,
        ),
    ]


class FreeSurferBaseValidator(Validator):
    """Validator for the FreeSurfer longitudinal base-template step."""

    procedure_name = "freesurfer_base"

    pre_rules = [
        # subjects_dir must exist before attempting the base template
        DirectoryExistsRule("subjects_dir", "FreeSurfer subjects directory"),
    ]

    post_rules = [
        OutputDirectoryExistsRule(
            "base_subject_dir", "FreeSurfer base subject directory"
        ),
        OutputDirectoryExistsRule("mri_dir", "base template mri directory"),
        ExpectedOutputsExistRule(
            outputs_attr="recon_done_flag",
            item_type="base recon-all completion flag",
        ),
    ]
