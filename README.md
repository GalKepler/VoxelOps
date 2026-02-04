# VoxelOps

**Clean, simple neuroimaging pipeline automation for brain banks.**

[![CI](https://github.com/yalab-devops/VoxelOps/actions/workflows/ci.yml/badge.svg)](https://github.com/yalab-devops/VoxelOps/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/yalab-devops/VoxelOps/branch/main/graph/badge.svg?token=YOUR_CODECOV_TOKEN)](https://codecov.io/gh/yalab-devops/VoxelOps)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/YOUR_CODACY_PROJECT_ID)](https://www.codacy.com/gh/yalab-devops/VoxelOps/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=yalab-devops/VoxelOps&amp;utm_campaign=Badge_Grade)
[![PyPI version](https://badge.fury.io/py/voxelops.svg)](https://badge.fury.io/py/voxelops)
[![Documentation Status](https://readthedocs.org/projects/voxelops/badge/?version=latest)](https://voxelops.readthedocs.io/en/latest/?badge=latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)

---

Brain banks need to process neuroimaging data **consistently**, **reproducibly**, and **auditably**. VoxelOps makes that simple by wrapping Docker-based neuroimaging tools into clean Python functions that return plain dicts -- ready for your database, your logs, and your peace of mind.

## Highlights

| Feature | Description |
|---------|-------------|
| **Simple Functions** | No classes, no inheritance -- just `run_*()` functions that return dicts |
| **Clear Schemas** | Typed dataclass inputs, outputs, and defaults for every procedure |
| **Reproducibility** | The exact Docker command is stored in every execution record |
| **Database-Ready** | Results are plain dicts -- trivial to save to PostgreSQL, MongoDB, or JSON |
| **Brain Bank Defaults** | Define your standard parameters once, reuse across all participants |
| **Comprehensive Logging** | Every run logged to JSON with timestamps, duration, and exit codes |

## Installation

```bash
# Using uv (recommended)
uv pip install voxelops

# Using pip
pip install voxelops
```

For development:

```bash
git clone https://github.com/yalab-devops/VoxelOps.git
cd VoxelOps
pip install -e ".[dev]"
```

**Requirements**: Python >= 3.8, Docker installed and accessible.

## Quick Start

```python
from voxelops import run_qsiprep, QSIPrepInputs

inputs = QSIPrepInputs(
    bids_dir="/data/bids",
    participant="01",
)

result = run_qsiprep(inputs, nprocs=16)

print(f"Completed in: {result['duration_human']}")
print(f"Outputs: {result['expected_outputs'].qsiprep_dir}")
print(f"Command: {' '.join(result['command'])}")

# Save to your database -- it's just a dict
db.processing_records.insert_one(result)
```

## Available Procedures

| Procedure | Purpose | Function | Execution |
|-----------|---------|----------|-----------|
| **HeudiConv** | DICOM to BIDS conversion | `run_heudiconv()` | Docker |
| **QSIPrep** | Diffusion MRI preprocessing | `run_qsiprep()` | Docker |
| **QSIRecon** | Diffusion reconstruction & connectivity | `run_qsirecon()` | Docker |
| **QSIParc** | Parcellation via `parcellate` | `run_qsiparc()` | Python (direct) |

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

# Step 1: DICOM -> BIDS
heudiconv_result = run_heudiconv(
    HeudiconvInputs(dicom_dir=Path("/data/dicoms"), participant=participant),
    heuristic=Path("/code/heuristic.py"),
)

# Step 2: Preprocessing
qsiprep_result = run_qsiprep(
    QSIPrepInputs(
        bids_dir=heudiconv_result["expected_outputs"].bids_dir,
        participant=participant,
    ),
    nprocs=16,
    mem_mb=32000,
)

# Step 3: Reconstruction
qsirecon_result = run_qsirecon(
    QSIReconInputs(
        qsiprep_dir=qsiprep_result["expected_outputs"].qsiprep_dir,
        participant=participant,
    ),
)

# Step 4: Parcellation
qsiparc_result = run_qsiparc(
    QSIParcInputs(
        qsirecon_dir=qsirecon_result["expected_outputs"].qsirecon_dir,
        participant=participant,
    ),
)
```

## Brain Bank Standards

Define your standard parameters once, use them everywhere:

```python
from voxelops import run_qsiprep, QSIPrepInputs, QSIPrepDefaults

# Define brain bank standard configuration
BRAIN_BANK_QSIPREP = QSIPrepDefaults(
    nprocs=16,
    mem_mb=32000,
    output_resolution=1.6,
    anatomical_template=["MNI152NLin2009cAsym"],
    docker_image="pennlinc/qsiprep:latest",
)

# Use for all participants
for participant in participants:
    inputs = QSIPrepInputs(bids_dir=bids_root, participant=participant)
    result = run_qsiprep(inputs, config=BRAIN_BANK_QSIPREP)
    db.save_processing_record(result)
```

## Execution Record

Every `run_*()` function returns a dict with:

```python
{
    "tool": "qsiprep",
    "participant": "01",
    "command": ["docker", "run", ...],    # Exact Docker command
    "exit_code": 0,
    "start_time": "2026-01-26T10:00:00",  # ISO timestamp
    "end_time": "2026-01-26T11:30:00",
    "duration_seconds": 5400,
    "duration_human": "1:30:00",
    "success": True,
    "log_file": "/path/to/log.json",
    "inputs": QSIPrepInputs(...),          # What you provided
    "config": QSIPrepDefaults(...),        # Configuration used
    "expected_outputs": QSIPrepOutputs(...),  # Where to find outputs
}
```

## Inputs, Outputs, and Defaults

Each procedure has three dataclass schemas:

**Inputs** -- what the procedure needs:

```python
inputs = QSIPrepInputs(
    bids_dir=Path("/data/bids"),  # Required
    participant="01",              # Required
    output_dir=None,               # Optional -- sensible default
    work_dir=None,                 # Optional -- sensible default
    bids_filters=None,             # Optional -- BIDS filter JSON
)
```

**Outputs** -- generated automatically from inputs:

```python
outputs = result["expected_outputs"]
outputs.qsiprep_dir       # /data/derivatives/qsiprep
outputs.participant_dir   # /data/derivatives/qsiprep/sub-01
outputs.html_report       # /data/derivatives/qsiprep/sub-01.html
```

**Defaults** -- brain bank standard configuration:

```python
config = QSIPrepDefaults(
    nprocs=8,                                         # CPU cores
    mem_mb=16000,                                     # Memory in MB
    output_resolution=1.6,                            # Resolution in mm
    anatomical_template=["MNI152NLin2009cAsym"],      # Template space(s)
    longitudinal=False,                               # Longitudinal mode
    skip_bids_validation=False,                       # BIDS validation
    docker_image="pennlinc/qsiprep:latest",           # Docker image
)

# Pass config object, or override individual parameters:
result = run_qsiprep(inputs, config=config)
result = run_qsiprep(inputs, nprocs=32, mem_mb=64000)
```

## Reproducibility

The execution record contains the exact Docker command. To reproduce any run:

```python
import subprocess

record = db.get_processing_record(participant="01", tool="qsiprep")
subprocess.run(record["command"])
```

## Project Structure

```
src/voxelops/
    __init__.py            # Package exports and version
    exceptions.py          # Exception hierarchy
    runners/               # Procedure runners
        _base.py           #   Shared: run_docker, validate_input_dir, validate_participant
        heudiconv.py       #   DICOM -> BIDS
        qsiprep.py         #   Diffusion preprocessing
        qsirecon.py        #   Reconstruction & connectivity
        qsiparc.py         #   Parcellation (via parcellate)
    schemas/               # Typed dataclass schemas
        heudiconv.py       #   HeudiconvInputs / Outputs / Defaults
        qsiprep.py         #   QSIPrepInputs / Outputs / Defaults
        qsirecon.py        #   QSIReconInputs / Outputs / Defaults
        qsiparc.py         #   QSIParcInputs / Outputs / Defaults
    utils/
        bids.py            # Post-processing utilities for BIDS compliance
examples/                  # Standalone usage scripts
notebooks/                 # Jupyter tutorial notebooks (01-05)
tests/                     # Pytest test suite
docs/                      # Sphinx documentation source
```

## Examples and Notebooks

- `examples/` -- standalone scripts for each procedure
- `notebooks/` -- step-by-step Jupyter tutorials:
  - `01_heudiconv_basics.ipynb` -- DICOM to BIDS conversion
  - `02_qsiprep_basics.ipynb` -- Diffusion preprocessing
  - `03_qsirecon_basics.ipynb` -- Reconstruction & connectivity
  - `04_qsiparc_basics.ipynb` -- Parcellation
  - `05_full_pipeline.ipynb` -- End-to-end pipeline

## Design Philosophy

**What VoxelOps does:**
Build Docker commands, execute them, return structured execution records, define clear inputs/outputs, provide sensible defaults.

**What VoxelOps does not do:**
Workflow orchestration (use Airflow/Prefect), job scheduling (use your cluster scheduler), database management (use SQLAlchemy/MongoDB), result aggregation (do that in your analysis code).

**Philosophy**: Do one thing well. Make it easy to integrate with your existing tools.

## Contributing

Contributions welcome! To add a new procedure:

1. Create schema in `src/voxelops/schemas/your_procedure.py`
2. Create runner in `src/voxelops/runners/your_procedure.py`
3. Follow the pattern of existing procedures
4. Add tests in `tests/`
5. Add an example in `examples/`

## License

MIT License -- see [LICENSE](LICENSE) file.

## Citation

```bibtex
@software{voxelops,
  title = {VoxelOps: Simple neuroimaging pipeline automation for brain banks},
  author = {{YALab DevOps}},
  year = {2026},
  url = {https://github.com/yalab-devops/VoxelOps}
}
```

## Support

- **Issues**: https://github.com/yalab-devops/VoxelOps/issues
- **Documentation**: https://voxelops.readthedocs.io
- **Email**: yalab.dev@gmail.com
