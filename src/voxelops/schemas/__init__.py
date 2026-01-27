"""Schemas for procedure inputs, outputs, and defaults."""

from voxelops.schemas.heudiconv import (
    HeudiconvInputs,
    HeudiconvOutputs,
    HeudiconvDefaults,
)
from voxelops.schemas.qsiprep import (
    QSIPrepInputs,
    QSIPrepOutputs,
    QSIPrepDefaults,
)
from voxelops.schemas.qsirecon import (
    QSIReconInputs,
    QSIReconOutputs,
    QSIReconDefaults,
)
from voxelops.schemas.qsiparc import (
    QSIParcInputs,
    QSIParcOutputs,
    QSIParcDefaults,
)

__all__ = [
    # HeudiConv
    "HeudiconvInputs",
    "HeudiconvOutputs",
    "HeudiconvDefaults",
    # QSIPrep
    "QSIPrepInputs",
    "QSIPrepOutputs",
    "QSIPrepDefaults",
    # QSIRecon
    "QSIReconInputs",
    "QSIReconOutputs",
    "QSIReconDefaults",
    # QSIParc
    "QSIParcInputs",
    "QSIParcOutputs",
    "QSIParcDefaults",
]
