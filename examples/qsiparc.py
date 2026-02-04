#!/usr/bin/env python3
"""QSIParc parcellation via the parcellate package.

This script demonstrates how to run QSIParc for parcellation
within the VoxelOps framework. Unlike other procedures, QSIParc
runs the `parcellate` Python package directly (not via Docker).
"""

from pathlib import Path

from voxelops import (
    QSIParcInputs,
    run_qsiparc,
)

# Input paths -- update these to match your setup
qsirecon_dir = Path("/data/derivatives/qsirecon/")
participant = "01"

# Output paths (optional)
output_dir = Path("/data/derivatives/qsiparc/")

# Create inputs
inputs = QSIParcInputs(
    qsirecon_dir=qsirecon_dir,
    participant=participant,
    output_dir=output_dir,
    n_jobs=4,
    n_procs=2,
)

# Run with defaults (atlases are auto-discovered from qsirecon outputs)
result = run_qsiparc(inputs)

print(f"Success: {result['success']}")
print(f"Duration: {result['duration_human']}")
print(f"Output files: {len(result['output_files'])}")
