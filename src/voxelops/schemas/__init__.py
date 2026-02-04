"""Schemas for procedure inputs, outputs, and defaults."""

from voxelops.schemas.heudiconv import (
    HeudiconvDefaults,
    HeudiconvInputs,
    HeudiconvOutputs,
)
from voxelops.schemas.qsiparc import (
    QSIParcDefaults,
    QSIParcInputs,
    QSIParcOutputs,
)
from voxelops.schemas.qsiprep import (
    QSIPrepDefaults,
    QSIPrepInputs,
    QSIPrepOutputs,
)
from voxelops.schemas.qsirecon import (
    QSIReconDefaults,
    QSIReconInputs,
    QSIReconOutputs,
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
