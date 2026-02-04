"""QSIRecon validator with pre and post validation rules."""

from voxelops.validation.rules.common import (
    DirectoryExistsRule,
    GlobFilesExistRule,
    OutputDirectoryExistsRule,
    ParticipantExistsRule,
)
from voxelops.validation.validators.base import Validator


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
            pattern="dwi/*_desc-preproc_dwi.nii.gz",
            min_count=1,
            file_type="Preprocessed DWI",
        ),
        # Check for QSIPrep confounds
        GlobFilesExistRule(
            base_dir_attr="qsiprep_dir",
            pattern="dwi/*_confounds.tsv",
            min_count=1,
            file_type="Confounds file",
        ),
    ]

    post_rules = [
        # Output existence checks
        OutputDirectoryExistsRule("qsirecon_dir", "QSIRecon output directory"),
        OutputDirectoryExistsRule("participant_dir", "Participant output directory"),
        # Check for reconstructed outputs (varies by reconstruction method)
        # Using a general check for any output files
        GlobFilesExistRule(
            base_dir_attr="participant_dir",
            pattern="**/*.nii.gz",
            min_count=1,
            file_type="Reconstruction outputs",
            phase="post",
            participant_level=False,  # participant_dir is already participant-specific
        ),
    ]
