#!/usr/bin/env python3
"""QSIRecon diffusion reconstruction and connectivity.

This script demonstrates how to run QSIRecon for reconstruction
within the VoxelOps framework.
"""

from pathlib import Path

from voxelops import QSIReconInputs, run_qsirecon

# Input paths -- update these to match your setup
qsiprep_dir = Path("/data/derivatives/qsiprep/")
participant = "01"
recon_spec = Path("/config/recon_specs/dsi_studio_gqi.json")
fs_license = Path("/opt/freesurfer/license.txt")

# Output paths (optional)
output_dir = Path("/data/derivatives/qsirecon/")
work_dir = Path("/data/work/qsirecon/")

# Create inputs
inputs = QSIReconInputs(
    qsiprep_dir=qsiprep_dir,
    participant=participant,
    recon_spec=recon_spec,
    output_dir=output_dir,
    work_dir=work_dir,
)

# Run with defaults
result = run_qsirecon(inputs, fs_license=fs_license)

print(f"Success: {result['success']}")
print(f"Duration: {result['duration_human']}")
print(f"Output: {result['expected_outputs'].qsirecon_dir}")
