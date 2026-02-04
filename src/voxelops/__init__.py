"""VoxelOps: Clean, simple neuroimaging pipeline automation for brain banks.

This package provides straightforward functions for running neuroimaging procedures
in Docker containers. Each procedure follows a simple pattern:
1. Define inputs (required paths and parameters)
2. Run the procedure (returns execution record)
3. Use expected outputs (generated from inputs)

Quick Start (Basic):
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

Quick Start (With Validation):
    >>> from voxelops import run_procedure, QSIPrepInputs
    >>>
    >>> inputs = QSIPrepInputs(
    ...     bids_dir="/data/bids",
    ...     participant="01",
    ... )
    >>> result = run_procedure("qsiprep", inputs)
    >>>
    >>> if result.success:
    ...     print(f"✓ Completed in {result.duration_seconds:.1f}s")
    ... else:
    ...     print(f"✗ Failed: {result.get_failure_reason()}")
    >>>
    >>> # Save complete audit trail to database
    >>> db.save_procedure_result(result.to_dict())

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

# Exceptions
# Audit system
from voxelops.audit import AuditEventType, AuditLogger, AuditRecord
from voxelops.exceptions import (
    InputValidationError,
    ProcedureError,
    ProcedureExecutionError,
)

# Procedure orchestration with validation and audit logging
from voxelops.procedures import ProcedureResult, run_procedure

# Basic runner functions (direct execution without validation)
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

# Validation framework
from voxelops.validation.base import ValidationReport, ValidationResult
from voxelops.validation.context import ValidationContext
from voxelops.validation.validators import (
    HeudiConvValidator,
    QSIParcValidator,
    QSIPrepValidator,
    QSIReconValidator,
)

__all__ = [
    # Basic runners (direct execution)
    "run_heudiconv",
    "run_qsiprep",
    "run_qsirecon",
    "run_qsiparc",
    # Procedure orchestration (with validation & audit)
    "run_procedure",
    "ProcedureResult",
    # Validation framework
    "ValidationResult",
    "ValidationReport",
    "ValidationContext",
    "HeudiConvValidator",
    "QSIPrepValidator",
    "QSIReconValidator",
    "QSIParcValidator",
    # Audit system
    "AuditEventType",
    "AuditRecord",
    "AuditLogger",
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
