#!/usr/bin/env python3
"""QSIRecon diffusion reconstruction and connectivity.

This script demonstrates how to run QSIRecon for reconstruction
within the VoxelOps framework.
"""

from pathlib import Path

from voxelops import QSIReconInputs, run_procedure

# Input paths -- update these to match your setup
qsiprep_dir = Path("/media/storage/yalab-dev/qsiprep_test/derivatives/qsiprep")
participant = "CLMC10"
recon_spec = Path("/home/galkepler/Projects/yalab-devops/VoxelOps/qsirecon_spec.yaml")
fs_license = Path("/home/galkepler/misc/freesurfer/license.txt")
datasets = {
    "atlases": Path("/media/storage/yalab-dev/voxelops/Schaefer2018Tian2020_atlases")
}
atlases = ["4S156Parcels", "Schaefer2018N100n7Tian2020S1"]
# Output paths (optional)
output_dir = Path("/media/storage/yalab-dev/qsiprep_test/derivatives/qsirecon/")
work_dir = Path("/media/storage/yalab-dev/qsiprep_test/work/qsirecon/")
log_dir = Path("/media/storage/yalab-dev/qsiprep_test/logs")


print("Running QSIRecon with the following settings:")
print(f"  QSIPrep directory: {qsiprep_dir} -- {qsiprep_dir.exists()}")
print(f"  Participant: {participant}")
print(f"  Reconstruction spec: {recon_spec} -- {recon_spec.exists()}")
print(f"  FreeSurfer license: {fs_license} -- {fs_license.exists()}")
print(f"  Output directory: {output_dir} -- {output_dir.exists()}")
print(f"  Work directory: {work_dir} -- {work_dir.exists()}")
print(f"  Log directory: {log_dir} -- {log_dir.exists()}")
# Create inputs
inputs = QSIReconInputs(
    qsiprep_dir=qsiprep_dir,
    participant=participant,
    recon_spec=recon_spec,
    output_dir=output_dir,
    work_dir=work_dir,
    atlases=atlases,
    datasets=datasets,
)

# Run with defaults
result = run_procedure(procedure="qsirecon", inputs=inputs, fs_license=fs_license)

if result.success:
    print(f"✓ Success! Completed in {result.duration_seconds:.1f}s")
    print("\nExpected workflow reports:")
    for workflow_name, session_reports in result.execution[
        "expected_outputs"
    ].workflow_reports.items():
        print(f"  Workflow: {workflow_name}")
        for session_id, html_path in session_reports.items():
            session_label = f"ses-{session_id}" if session_id else "no-session"
            status = "✓" if html_path.exists() else "✗"
            print(f"    {status} {session_label}: {html_path}")
else:
    print(f"✗ Failed: {result.get_failure_reason()}")
