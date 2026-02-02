#!/usr/bin/env python3
"""DICOM to BIDS conversion via HeudiConv.

This script demonstrates how to convert DICOM files to BIDS format using HeudiConv
within the VoxelOps framework. It sets up the necessary inputs and configurations,
executes the conversion, and prints out the results.
"""

from pathlib import Path

from voxelops import HeudiconvInputs, run_heudiconv

# Your data paths -- update these to match your setup
DATA_ROOT = Path("/data/raw/dicom/")
HEURISTIC_FILE = Path("/config/heuristics/brain_bank.py")
OUTPUT_DIR = Path("/data/bids/")

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
result = run_heudiconv(inputs, heuristic=HEURISTIC_FILE, overwrite=True)

# Check result
print(f"Success: {result['success']}")
print(f"Duration: {result['duration_human']}")
print(f"Output: {result['expected_outputs'].bids_dir}")
