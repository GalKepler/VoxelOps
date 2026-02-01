from pathlib import Path
from voxelops import (
    run_qsirecon,
    QSIReconInputs,
    QSIReconDefaults,
)
import json

# Input paths
qsiprep_dir = Path("/media/storage/yalab-dev/qsiprep_test/qsiprep_output/")
participant = "01"
recon_spec = Path("/home/galkepler/Projects/yalab-devops/VoxelOps/qsirecon_spec.yaml")
fs_license = Path("/home/galkepler/misc/freesurfer/license.txt")

# Output paths (optional)
output_dir = Path("/media/storage/yalab-dev/qsiprep_test/qsirecon_output/")
work_dir = Path("/media/storage/yalab-dev/qsiprep_test/work/qsirecon/")

# Create inputs
inputs = QSIReconInputs(
    qsiprep_dir=qsiprep_dir,
    participant=participant,
    recon_spec=recon_spec,
    output_dir=output_dir,
    work_dir=work_dir,
)

# Run with defaults
result = run_qsirecon(
    inputs, fs_license=fs_license, docker_image="pennlinc/qsirecon:1.1.1"
)

print(f"Success: {result['success']}")
print(f"Duration: {result['duration_human']}")
