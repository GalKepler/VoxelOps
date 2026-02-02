from pathlib import Path
from voxelops import (
    run_qsiparc,
    QSIParcInputs,
    QSIParcDefaults,
)
from parcellate.interfaces.models import AtlasDefinition


# Input paths
qsirecon_dir = Path("/media/storage/yalab-dev/qsiprep_test/qsirecon_output/")
participant = "01"

# Output paths (optional)
output_dir = Path("/media/storage/yalab-dev/qsiprep_test/qsiparc_output/")


atlases = [AtlasDefinition(
    name="Schaefer2018N100n7Tian2020S1",
    nifti_path=Path("/media/storage/yalab-dev/voxelops/Schaefer2018Tian2020_atlases/Schaefer2018N100n7Tian2020S1/atlas-Schaefer2018N100n7Tian2020S1_space-MNI152NLin2009cAsym_res-01_dseg.nii.gz"),
    lut=Path("/media/storage/yalab-dev/voxelops/Schaefer2018Tian2020_atlases/Schaefer2018N100n7Tian2020S1/atlas-Schaefer2018N100n7Tian2020S1_dseg.tsv"),
    resolution="01",
    space="MNI152NLin2009cAsym",
)]
# Create inputs
inputs = QSIParcInputs(
    qsirecon_dir=qsirecon_dir,
    participant=participant,
    output_dir=output_dir,
    n_jobs=10,
    n_procs=20,
    atlases=atlases,
)

# Run with defaults (atlases are auto-discovered from qsirecon outputs)
result = run_qsiparc(inputs)

print(f"Success: {result['success']}")
print(f"Duration: {result['duration_human']}")
print(f"Output files: {len(result['output_files'])}")
