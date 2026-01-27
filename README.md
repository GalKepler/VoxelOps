# VoxelOps

Clean, simple neuroimaging pipeline automation for brain banks.

## Why This Package?

Brain banks need to process neuroimaging data **consistently**, **reproducibly**, and **auditablely**. This package makes that simple:

- ✅ **Simple Functions**: No classes, no complex objects - just functions that return dicts
- ✅ **Clear Inputs/Outputs**: Each procedure explicitly defines what it needs and produces
- ✅ **Perfect Reproducibility**: Exact Docker command stored in every execution record
- ✅ **Database-Ready**: Results are plain dicts - trivial to save anywhere
- ✅ **Brain Bank Standards**: Define your standard parameters once, use everywhere
- ✅ **Comprehensive Logging**: Every execution logged to JSON with full details

## Installation

### Using uv (recommended)

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install voxelops
uv pip install voxelops
```

### Using pip

```bash
pip install voxelops
```

**Requirements**: Docker (the procedures run in containers)

## Quick Start

```python
from voxelops import run_qsiprep, QSIPrepInputs

# Define inputs
inputs = QSIPrepInputs(
    bids_dir="/data/bids",
    participant="01",
)

# Run QSIPrep with brain bank defaults
result = run_qsiprep(inputs, nprocs=16)

# Result is a dict with everything you need
print(f"Completed in: {result['duration_human']}")
print(f"Outputs: {result['expected_outputs'].qsiprep_dir}")
print(f"Command: {' '.join(result['command'])}")

# Save to your database - it's just a dict!
db.processing_records.insert_one(result)
```

## Available Procedures

| Procedure | Purpose | Function |
|-----------|---------|----------|
| **HeudiConv** | DICOM → BIDS conversion | `run_heudiconv()` |
| **QSIPrep** | Diffusion MRI preprocessing | `run_qsiprep()` |
| **QSIRecon** | Diffusion reconstruction & connectivity | `run_qsirecon()` |
| **QSIParc** | Parcellation using parcellate | `run_qsiparc()` |

## Full Pipeline Example

```python
from pathlib import Path
from voxelops import (
    run_heudiconv, HeudiconvInputs,
    run_qsiprep, QSIPrepInputs,
    run_qsirecon, QSIReconInputs,
    run_qsiparc, QSIParcInputs,
)

participant = "01"

# Step 1: DICOM → BIDS
heudiconv_result = run_heudiconv(
    inputs=HeudiconvInputs(
        dicom_dir=Path("/data/dicoms"),
        participant=participant,
    ),
    heuristic=Path("/code/heuristic.py"),
)

# Step 2: QSIPrep (use output from step 1)
qsiprep_result = run_qsiprep(
    inputs=QSIPrepInputs(
        bids_dir=heudiconv_result['expected_outputs'].bids_dir,
        participant=participant,
    ),
    nprocs=16,
    mem_gb=32,
)

# Step 3: QSIRecon
qsirecon_result = run_qsirecon(
    inputs=QSIReconInputs(
        qsiprep_dir=qsiprep_result['expected_outputs'].qsiprep_dir,
        participant=participant,
    ),
)

# Step 4: QSIParc
qsiparc_result = run_qsiparc(
    inputs=QSIParcInputs(
        qsirecon_dir=qsirecon_result['expected_outputs'].qsirecon_dir,
        participant=participant,
    ),
)

# All results are dicts - save to your database
db.save_pipeline({
    'participant': participant,
    'heudiconv': heudiconv_result,
    'qsiprep': qsiprep_result,
    'qsirecon': qsirecon_result,
    'qsiparc': qsiparc_result,
})
```

## Brain Bank Standards

Define your standard parameters once, use them everywhere:

```python
from voxelops import run_qsiprep, QSIPrepInputs, QSIPrepDefaults

# Define brain bank standard configuration
BRAIN_BANK_QSIPREP = QSIPrepDefaults(
    nprocs=16,
    mem_gb=32,
    output_resolution=1.6,
    output_spaces=["MNI152NLin2009cAsym"],
    longitudinal=True,
    docker_image="pennlinc/qsiprep:1.0.2",  # Pin version for consistency
)

# Use for all participants
for participant in participants:
    inputs = QSIPrepInputs(
        bids_dir=bids_root,
        participant=participant,
    )

    result = run_qsiprep(inputs, BRAIN_BANK_QSIPREP)
    db.save_processing_record(result)
```

## What's in the Execution Record?

Every `run_*()` function returns a dict with:

```python
{
    "tool": "qsiprep",                          # Tool name
    "participant": "01",                        # Participant label
    "command": ["docker", "run", ...],          # Full Docker command
    "exit_code": 0,                             # Process exit code
    "start_time": "2026-01-26T10:00:00",       # ISO timestamp
    "end_time": "2026-01-26T11:30:00",         # ISO timestamp
    "duration_seconds": 5400,                   # Duration in seconds
    "duration_human": "1:30:00",               # Human-readable duration
    "success": True,                            # Boolean status
    "log_file": "/path/to/log.json",           # Path to detailed log
    "inputs": QSIPrepInputs(...),              # What you provided
    "config": QSIPrepDefaults(...),            # Configuration used
    "expected_outputs": QSIPrepOutputs(...),   # Where to find outputs
}
```

## Database Integration

Results are just dicts - works with anything:

### PostgreSQL (JSON column)

```python
from sqlalchemy import insert, JSON

session.execute(
    insert(processing_records).values(
        participant_id=result['participant'],
        tool=result['tool'],
        timestamp=result['start_time'],
        duration=result['duration_seconds'],
        success=result['success'],
        full_record=result,  # JSON column
    )
)
```

### MongoDB

```python
db.processing_records.insert_one({
    'participant': result['participant'],
    'tool': result['tool'],
    'timestamp': result['start_time'],
    'record': result,
})
```

### SQLAlchemy ORM

```python
class ProcessingRecord(Base):
    __tablename__ = 'processing_records'

    id = Column(Integer, primary_key=True)
    participant = Column(String)
    tool = Column(String)
    command = Column(JSON)
    duration = Column(Float)
    success = Column(Boolean)
    timestamp = Column(DateTime)
    full_record = Column(JSON)

# Save
record = ProcessingRecord(
    participant=result['participant'],
    tool=result['tool'],
    command=result['command'],
    duration=result['duration_seconds'],
    success=result['success'],
    timestamp=datetime.fromisoformat(result['start_time']),
    full_record=result,
)
session.add(record)
session.commit()
```

## Perfect Reproducibility

The execution record contains the **exact Docker command** that was run. To reproduce:

```python
# Get record from database
record = db.get_processing_record(participant='01', tool='qsiprep')

# Extract command
cmd = record['command']

# Run it again - perfect reproduction!
import subprocess
subprocess.run(cmd)
```

## Inputs, Outputs, and Defaults

Each procedure has three schemas:

### Inputs (Required)

What the procedure needs to run:

```python
from voxelops import QSIPrepInputs

inputs = QSIPrepInputs(
    bids_dir=Path("/data/bids"),      # Required
    participant="01",                  # Required
    output_dir=None,                   # Optional (has sensible default)
    work_dir=None,                     # Optional (has sensible default)
)
```

### Outputs (Generated)

Where to find the results:

```python
# Automatically generated from inputs
outputs = result['expected_outputs']

print(outputs.qsiprep_dir)      # /data/derivatives/qsiprep
print(outputs.participant_dir)   # /data/derivatives/qsiprep/sub-01
print(outputs.html_report)       # /data/derivatives/qsiprep/sub-01.html
```

### Defaults (Brain Bank Standards)

Configuration parameters with sensible defaults:

```python
from voxelops import QSIPrepDefaults

config = QSIPrepDefaults(
    nprocs=8,                                        # Number of cores
    mem_gb=16,                                       # Memory limit
    output_resolution=1.6,                           # Output resolution (mm)
    output_spaces=["MNI152NLin2009cAsym"],          # Anatomical templates
    longitudinal=True,                               # Longitudinal processing
    docker_image="pennlinc/qsiprep:1.0.2",          # Docker image
)

# Use defaults
result = run_qsiprep(inputs, config)

# Or override specific parameters
result = run_qsiprep(inputs, nprocs=32, mem_gb=64)
```

## Examples

See `examples/` directory:

- **`full_pipeline.py`**: Complete DICOM → BIDS → QSIPrep → QSIRecon → QSIParc
- **`brain_bank_integration.py`**: Database integration patterns and audit trails

## Design Philosophy

### What This Package Does

✅ Builds Docker commands
✅ Executes them
✅ Returns execution records
✅ Defines clear inputs/outputs
✅ Provides sensible defaults

### What This Package Doesn't Do

❌ Complex workflow orchestration (use Airflow, Prefect, etc.)
❌ Job scheduling (use your cluster scheduler)
❌ Database management (use SQLAlchemy, MongoDB, etc.)
❌ File validation (use BIDS validator separately)
❌ Result aggregation (do that in your analysis code)

**Philosophy**: Do one thing well. Make it easy to integrate with your existing tools.

## Why Not [Complex Alternative]?

You might wonder why not use Nipype, BIDS Apps, or other frameworks?

**For a brain bank, you need**:
1. **Reproducibility** - Exact command stored in database
2. **Auditability** - Clear logs of what was run
3. **Database integration** - Easy to store processing records
4. **Simplicity** - New team members can understand quickly

**Complex frameworks** are designed for:
- Building complex workflows with many dependencies
- Graph-based execution
- Advanced features you don't need for running Docker containers

**voxelops** is designed for:
- Running Docker containers with clear inputs/outputs
- Storing execution records in your database
- Perfect reproducibility (command is in the record)
- Simple integration with your existing tools

## Requirements

- **Python**: >= 3.8
- **Docker**: Must be installed and accessible
- **Data**: BIDS-formatted neuroimaging data
- **Docker Images**: The procedures run in containers (will be pulled automatically)

## Contributing

Contributions welcome! This package is designed to be simple and maintainable.

To add a new procedure:
1. Create schema in `src/voxelops/schemas/your_procedure.py`
2. Create runner in `src/voxelops/runners/your_procedure.py`
3. Follow the pattern of existing procedures
4. Add example usage

## License

MIT License - see LICENSE file

## Citation

If you use this package in your research, please cite:

```bibtex
@software{voxelops,
  title = {VoxelOps: Simple neuroimaging pipeline automation for brain banks},
  author = {{YALab DevOps}},
  year = {2026},
  url = {https://github.com/yalab-devops/VoxelOps}
}
```

## Support

- **Issues**: https://github.com/yalab-devops/voxelops/issues
- **Documentation**: See `examples/` directory
- **Email**: yalab.dev@gmail.com
