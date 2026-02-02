#!/usr/bin/env python3
"""DICOM to BIDS coversion via Heudiconv

This script demonstrates how to convert DICOM files to BIDS format using Heudiconv
within the VoxelOps framework. It sets up the necessary inputs and configurations,
executes the conversion, and prints out the results.
"""

from pathlib import Path
from voxelops import (
    run_heudiconv,
    HeudiconvInputs,
    HeudiconvDefaults,
)
import json

# Your data paths
DATA_ROOT = Path("/media/storage/yalab-dev/test_dicom/20251003_0917/")
HEURISTIC_FILE = Path("/home/galkepler/Projects/yalab-devops/VoxelOps/heuristic.py")
OUTPUT_DIR = Path("/media/storage/yalab-dev/qsiprep_test/heudiconv_test/")

# Participant to process
PARTICIPANT = "01"

# Create inputs
inputs = HeudiconvInputs(
    dicom_dir=DATA_ROOT,
    participant=PARTICIPANT,
    session="01",
    output_dir=OUTPUT_DIR,
)

# Run with defaults
result = run_heudiconv(inputs, heuristic=HEURISTIC_FILE, overwrite=True, bids=None)

# Check result
print(f"Success: {result['success']}")
print(f"Duration: {result['duration_human']}")
print(f"Output: {result['expected_outputs'].bids_dir}")
