"""Example: Skip execution if outputs exist using the force flag.

The force flag allows efficient batch processing by skipping participants
whose outputs already exist. This is useful for:
- Re-running only failed participants
- Adding new participants to an existing dataset
- Avoiding redundant processing
"""

from pathlib import Path

from voxelops.runners.qsiprep import run_qsiprep
from voxelops.schemas.qsiprep import QSIPrepDefaults, QSIPrepInputs

# Setup paths
bids_dir = Path("/data/bids")
output_dir = Path("/data/derivatives")

# Example 1: Default behavior - skip if outputs exist
# ===================================================
print("Example 1: Skip if outputs exist (default)")
print("-" * 60)

inputs = QSIPrepInputs(
    bids_dir=bids_dir,
    participant="01",
    output_dir=output_dir,
)

result = run_qsiprep(inputs)  # force=False is the default

if result.get("skipped"):
    print(f"✓ Skipped participant {result['participant']} - outputs already exist")
    print(f"  Reason: {result['reason']}")
else:
    print(f"✓ Completed participant {result['participant']}")

# Example 2: Force re-run even if outputs exist
# ==============================================
print("\nExample 2: Force re-run")
print("-" * 60)

result = run_qsiprep(inputs, force=True)  # Force execution

print(f"✓ Completed participant {result['participant']} (forced)")

# Example 3: Batch processing with skip
# ======================================
print("\nExample 3: Batch processing multiple participants")
print("-" * 60)

participants = ["01", "02", "03", "04", "05"]
skipped = []
completed = []

for participant in participants:
    inputs = QSIPrepInputs(
        bids_dir=bids_dir,
        participant=participant,
        output_dir=output_dir,
    )

    result = run_qsiprep(inputs)  # Skip if exists

    if result.get("skipped"):
        skipped.append(participant)
    else:
        completed.append(participant)

print(f"Completed: {len(completed)} participants - {completed}")
print(f"Skipped: {len(skipped)} participants - {skipped}")

# Example 4: Configuration with force flag
# =========================================
print("\nExample 4: Using force in config")
print("-" * 60)

# Create config with force=True
config = QSIPrepDefaults(
    force=True,  # Force re-run
    nprocs=16,
    mem_mb=32000,
)

inputs = QSIPrepInputs(
    bids_dir=bids_dir,
    participant="01",
    output_dir=output_dir,
)

result = run_qsiprep(inputs, config=config)  # Will run even if outputs exist

print(f"✓ Forced execution for participant {result['participant']}")
