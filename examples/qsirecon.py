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

# Datasets to include
datasets = {
    "atlases": "/media/storage/yalab-dev/voxelops/Schaefer2018Tian2020_atlases"
}
# Create inputs
inputs = QSIReconInputs(
    qsiprep_dir=qsiprep_dir,
    participant=participant,
    recon_spec=recon_spec,
    output_dir=output_dir,
    work_dir=work_dir,
    datasets=datasets,
    atlases=['Schaefer2018N100n7Tian2020S1',
 'Schaefer2018N100n7Tian2020S2',
 'Schaefer2018N100n7Tian2020S3',
 'Schaefer2018N100n7Tian2020S4',
 'Schaefer2018N200n7Tian2020S1',
 'Schaefer2018N200n7Tian2020S2',
 'Schaefer2018N200n7Tian2020S3',
 'Schaefer2018N200n7Tian2020S4',
 'Schaefer2018N300n7Tian2020S1',
 'Schaefer2018N300n7Tian2020S2',
 'Schaefer2018N300n7Tian2020S3',
 'Schaefer2018N300n7Tian2020S4',
 'Schaefer2018N400n7Tian2020S1',
 'Schaefer2018N400n7Tian2020S2',
 'Schaefer2018N400n7Tian2020S3',
 'Schaefer2018N400n7Tian2020S4',
 'Schaefer2018N500n7Tian2020S1',
 'Schaefer2018N500n7Tian2020S2',
 'Schaefer2018N500n7Tian2020S3',
 'Schaefer2018N500n7Tian2020S4',
 'Schaefer2018N600n7Tian2020S1',
 'Schaefer2018N600n7Tian2020S2',
 'Schaefer2018N600n7Tian2020S3',
 'Schaefer2018N600n7Tian2020S4',
 'Schaefer2018N800n7Tian2020S1',
 'Schaefer2018N800n7Tian2020S2',
 'Schaefer2018N800n7Tian2020S3',
 'Schaefer2018N800n7Tian2020S4',
 'Schaefer2018N900n7Tian2020S1',
 'Schaefer2018N900n7Tian2020S2',
 'Schaefer2018N900n7Tian2020S3',
 'Schaefer2018N900n7Tian2020S4',
 'Schaefer2018N1000n7Tian2020S1',
 'Schaefer2018N1000n7Tian2020S2',
 'Schaefer2018N1000n7Tian2020S3',
 'Schaefer2018N1000n7Tian2020S4']
)


# Run with defaults
result = run_qsirecon(
    inputs, fs_license=fs_license, docker_image="pennlinc/qsirecon:1.1.1"
)

print(f"Success: {result['success']}")
print(f"Duration: {result['duration_human']}")
