#!/usr/bin/env python3
"""QSIParc parcellation via the parcellate package.

This script demonstrates how to run QSIParc for parcellation
within the VoxelOps framework. Unlike other procedures, QSIParc
runs the `parcellate` Python package directly (not via Docker).
"""

from pathlib import Path

from voxelops import (
    QSIParcInputs,
)
from voxelops.procedures.orchestrator import run_procedure

# Input paths -- update these to match your setup
qsirecon_dir = Path("/media/storage/yalab-dev/qsiprep_test/derivatives/qsirecon/")
participant = "CLMC10"

# Output paths (optional)
output_dir = Path("/media/storage/yalab-dev/qsiprep_test/derivatives/qsiparc/")
log_dir = Path("/media/storage/yalab-dev/qsiprep_test/logs")

# Create inputs
inputs = QSIParcInputs(
    qsirecon_dir=qsirecon_dir,
    participant=participant,
    output_dir=output_dir,
    n_jobs=4,
    n_procs=2,
)

# Run with defaults (atlases are auto-discovered from qsirecon outputs)
result = run_procedure(procedure="qsiparc", inputs=inputs, log_dir=log_dir)


if result.success:
    print(f"✓ Success! Completed in {result.duration_seconds:.1f}s")
    print("\nExpected workflow directories:")
    for workflow_name, session_dirs in result.execution[
        "expected_outputs"
    ].workflow_dirs.items():
        print(f"  Workflow: {workflow_name}")
        for session_id, dwi_dir in session_dirs.items():
            session_label = f"ses-{session_id}" if session_id else "no-session"
            status = "✓" if dwi_dir.exists() else "✗"
            print(f"    {status} {session_label}: {dwi_dir}")
else:
    print(f"✗ Failed: {result.get_failure_reason()}")
