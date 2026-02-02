#!/usr/bin/env python3
"""QSIPrep diffusion MRI preprocessing.

This script demonstrates how to run QSIPrep for diffusion preprocessing
within the VoxelOps framework.
"""

from pathlib import Path

from voxelops import QSIPrepInputs, run_qsiprep

# Input paths -- update these to match your setup
bids_dir = Path("/data/bids/")
participant = "01"
fs_license = Path("/opt/freesurfer/license.txt")

# Output paths (optional)
output_dir = Path("/data/derivatives/qsiprep/")
work_dir = Path("/data/work/qsiprep/")

# Prepare inputs
inputs = QSIPrepInputs(
    bids_dir=bids_dir,
    participant=participant,
    output_dir=output_dir,
    work_dir=work_dir,
)

# Run QSIPrep
result = run_qsiprep(inputs, fs_license=fs_license)

# Check result
print(f"Success: {result['success']}")
print(f"Duration: {result['duration_human']}")
print(f"Output: {result['expected_outputs'].qsiprep_dir}")
