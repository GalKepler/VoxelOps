"""VoxelOps: Clean, simple neuroimaging pipeline automation for brain banks.

This package provides straightforward functions for running neuroimaging procedures
in Docker containers. Each procedure follows a simple pattern:
1. Define inputs (required paths and parameters)
2. Run the procedure (returns execution record)
3. Use expected outputs (generated from inputs)

Quick Start:
    >>> from voxelops import run_qsiprep, QSIPrepInputs
    >>>
    >>> inputs = QSIPrepInputs(
    ...     bids_dir="/data/bids",
    ...     participant="01",
    ... )
    >>> result = run_qsiprep(inputs, nprocs=16)
    >>>
    >>> # Result is a dict with everything you need
    >>> print(f"Completed in {result['duration_human']}")
    >>> print(f"Outputs: {result['expected_outputs'].qsiprep_dir}")
    >>>
    >>> # Perfect for databases
    >>> db.save_processing_record(result)

Available Procedures:
    - run_heudiconv: DICOM → BIDS conversion
    - run_qsiprep: Diffusion MRI preprocessing
    - run_qsirecon: Diffusion reconstruction & connectivity
    - run_qsiparc: Parcellation using parcellate package

For full pipeline example, see examples/full_pipeline.py
"""

__author__ = "YALab DevOps"
__email__ = "yalab.dev@gmail.com"
__version__ = "2.0.0"

# Runner functions
# Exceptions
from voxelops.exceptions import (
    InputValidationError,
    ProcedureError,
    ProcedureExecutionError,
)
from voxelops.runners import (
    run_heudiconv,
    run_qsiparc,
    run_qsiprep,
    run_qsirecon,
)

# Schemas for inputs, outputs, and defaults
from voxelops.schemas import (
    HeudiconvDefaults,
    # HeudiConv
    HeudiconvInputs,
    HeudiconvOutputs,
    QSIParcDefaults,
    # QSIParc
    QSIParcInputs,
    QSIParcOutputs,
    QSIPrepDefaults,
    # QSIPrep
    QSIPrepInputs,
    QSIPrepOutputs,
    QSIReconDefaults,
    # QSIRecon
    QSIReconInputs,
    QSIReconOutputs,
)

__all__ = [
    # Runners
    "run_heudiconv",
    "run_qsiprep",
    "run_qsirecon",
    "run_qsiparc",
    # Schemas - HeudiConv
    "HeudiconvInputs",
    "HeudiconvOutputs",
    "HeudiconvDefaults",
    # Schemas - QSIPrep
    "QSIPrepInputs",
    "QSIPrepOutputs",
    "QSIPrepDefaults",
    # Schemas - QSIRecon
    "QSIReconInputs",
    "QSIReconOutputs",
    "QSIReconDefaults",
    # Schemas - QSIParc
    "QSIParcInputs",
    "QSIParcOutputs",
    "QSIParcDefaults",
    # Exceptions
    "ProcedureError",
    "InputValidationError",
    "ProcedureExecutionError",
]
