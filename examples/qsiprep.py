from pathlib import Path
from voxelops import (
    run_qsiprep,
    QSIPrepInputs,
    QSIPrepDefaults,
)
import json

# Input paths
# Input paths
bids_dir = Path("/media/storage/yalab-dev/qsiprep_test/heudiconv_test/")
participant = "01"
fs_license = Path("/home/galkepler/misc/freesurfer/license.txt")
bids_filters = Path("/home/galkepler/Projects/yalab-devops/VoxelOps/bids_filters.json")

# Output paths (optional)
output_dir = Path("/media/storage/yalab-dev/qsiprep_test/qsiprep_output/")
work_dir = Path("/media/storage/yalab-dev/qsiprep_test/work/qsiprep/")

# Prepare inputs
inputs = QSIPrepInputs(
    bids_dir=bids_dir,
    participant=participant,
    output_dir=output_dir,
    work_dir=work_dir,
    bids_filters=bids_filters,
)

# Run QSIPrep
result = run_qsiprep(inputs, fs_license=fs_license)  # Override default nprocs
