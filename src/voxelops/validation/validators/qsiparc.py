"""QSIParc validator with pre and post validation rules."""

from voxelops.validation.rules.common import (
    DirectoryExistsRule,
    ExpectedOutputsExistRule,
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
        # Check for required reconstruction outputs from QSIRecon workflows
        # Note: QSIRecon nests participant under workflow dirs (derivatives/qsirecon-*/sub-*)
        # so we check from qsirecon_dir root, not participant-scoped
        GlobFilesExistRule(
            base_dir_attr="qsirecon_dir",
            pattern="derivatives/qsirecon-*/**/dwi/*.nii.gz",
            min_count=1,
            file_type="Reconstruction outputs for parcellation",
            participant_level=False,
        ),
    ]

    post_rules = [
        # Output existence checks
        OutputDirectoryExistsRule("output_dir", "Parcellation output directory"),
        # Check for workflow dwi directories (nested dict: {workflow: {session: path}})
        ExpectedOutputsExistRule(
            outputs_attr="workflow_dirs",
            item_type="workflow dwi directories",
            flatten_nested=True,
        ),
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
