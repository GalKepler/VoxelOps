# voxelops Architecture

## Overview

This package provides simple, clean functions for running neuroimaging procedures in Docker containers. It's designed specifically for brain banks that need reproducibility, auditability, and easy database integration.

## Design Principles

1. **Simplicity**: Functions, not classes. Dicts, not complex objects.
2. **Clarity**: Clear inputs, outputs, and defaults for each procedure
3. **Reproducibility**: Store exact Docker command in execution record
4. **Database-Friendly**: Results are plain dicts, easy to store anywhere
5. **Extensibility**: Easy to add new procedures following same pattern

## Directory Structure

```
voxelops-v2/
├── src/voxelops/
│   ├── __init__.py                    # Package exports
│   │
│   ├── runners/                       # Procedure runners
│   │   ├── __init__.py               # Runner exports
│   │   ├── _base.py                  # Shared utilities (run_docker, validate_paths)
│   │   ├── heudiconv.py              # DICOM → BIDS
│   │   ├── qsiprep.py                # Diffusion preprocessing
│   │   ├── qsirecon.py               # Diffusion reconstruction
│   │   └── qsiparc.py                # Parcellation
│   │
│   ├── schemas/                       # Input/Output definitions
│   │   ├── __init__.py               # Schema exports
│   │   ├── heudiconv.py              # HeudiconvInputs/Outputs/Defaults
│   │   ├── qsiprep.py                # QSIPrepInputs/Outputs/Defaults
│   │   ├── qsirecon.py               # QSIReconInputs/Outputs/Defaults
│   │   └── qsiparc.py                # QSIParcInputs/Outputs/Defaults
│   │
│   └── exceptions.py                  # Custom exceptions
│
├── examples/
│   ├── full_pipeline.py              # Complete DICOM→...→QSIParc pipeline
│   └── brain_bank_integration.py    # Database integration patterns
│
├── tests/
│   └── test_runners.py               # Unit tests
│
├── pyproject.toml                     # Minimal dependencies (no Nipype!)
├── README.md                          # Comprehensive documentation
├── LICENSE                            # MIT License
└── .gitignore                         # Standard Python .gitignore
```

## Code Organization

### 1. Runners (`runners/`)

Each runner is a simple function that:
1. Takes `Inputs` schema and optional `Defaults` config
2. Validates inputs
3. Builds Docker command
4. Executes via `run_docker()` from `_base.py`
5. Returns execution record (dict) with expected outputs

**Pattern**:
```python
def run_procedure(
    inputs: ProcedureInputs,
    config: Optional[ProcedureDefaults] = None,
    **overrides
) -> Dict[str, Any]:
    """Run the procedure."""
    # Use defaults if not provided
    config = config or ProcedureDefaults()

    # Apply overrides
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)

    # Validate
    validate_input_dir(inputs.input_dir)
    validate_participant(inputs.input_dir, inputs.participant)

    # Setup paths
    output_dir = inputs.output_dir or default_path

    # Generate expected outputs
    expected_outputs = ProcedureOutputs.from_inputs(inputs, output_dir)

    # Build Docker command
    cmd = ["docker", "run", "--rm", ...]

    # Execute
    result = run_docker(cmd, "tool_name", inputs.participant, log_dir)

    # Add context to result
    result['inputs'] = inputs
    result['config'] = config
    result['expected_outputs'] = expected_outputs

    return result
```

### 2. Schemas (`schemas/`)

Each procedure has three dataclasses:

#### **Inputs** (Required)
What the procedure needs to run:
```python
@dataclass
class ProcedureInputs:
    input_dir: Path          # Required
    participant: str         # Required
    output_dir: Optional[Path] = None  # Optional with default
```

#### **Outputs** (Generated)
Where to find results:
```python
@dataclass
class ProcedureOutputs:
    output_dir: Path
    participant_dir: Path
    specific_files: Path

    @classmethod
    def from_inputs(cls, inputs: ProcedureInputs, output_dir: Path):
        """Generate expected paths from inputs."""
        return cls(
            output_dir=output_dir,
            participant_dir=output_dir / f"sub-{inputs.participant}",
            specific_files=...,
        )
```

#### **Defaults** (Brain Bank Standards)
Configuration with sensible defaults:
```python
@dataclass
class ProcedureDefaults:
    nprocs: int = 8
    mem_gb: int = 16
    docker_image: str = "tool/image:version"
    # ... procedure-specific parameters
```

### 3. Base Utilities (`runners/_base.py`)

Shared functions used by all runners:

- **`run_docker()`**: Execute Docker command, return execution record
- **`validate_input_dir()`**: Check directory exists
- **`validate_participant()`**: Check participant exists in directory

### 4. Exceptions (`exceptions.py`)

Custom exception hierarchy:
- `ProcedureError` (base)
- `InputValidationError` (validation failures)
- `ProcedureExecutionError` (execution failures)

## Execution Flow

```
1. User calls run_procedure(inputs, config)
   ↓
2. Runner validates inputs
   ↓
3. Runner generates expected outputs
   ↓
4. Runner builds Docker command
   ↓
5. run_docker() executes command
   ↓
6. run_docker() creates execution record
   ↓
7. Runner adds inputs/config/outputs to record
   ↓
8. Return dict to user
```

## Execution Record Structure

Every `run_*()` function returns:

```python
{
    # Execution details
    "tool": str,                    # Tool name
    "participant": str,             # Participant label
    "command": List[str],           # Full Docker command
    "exit_code": int,               # Process exit code
    "start_time": str,              # ISO timestamp
    "end_time": str,                # ISO timestamp
    "duration_seconds": float,      # Duration
    "duration_human": str,          # Human-readable duration
    "success": bool,                # Success status
    "log_file": str,                # Path to JSON log

    # Optional (if captured)
    "stdout": str,                  # Process stdout
    "stderr": str,                  # Process stderr
    "error": str,                   # Error message (if failed)

    # Context (added by runner)
    "inputs": ProcedureInputs,      # What was provided
    "config": ProcedureDefaults,    # Configuration used
    "expected_outputs": ProcedureOutputs,  # Where to find results
}
```

## Adding a New Procedure

Follow this pattern:

### 1. Create Schema (`schemas/your_procedure.py`)

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class YourProcedureInputs:
    """Required inputs."""
    input_dir: Path
    participant: str
    output_dir: Optional[Path] = None

@dataclass
class YourProcedureOutputs:
    """Expected outputs."""
    output_dir: Path
    participant_dir: Path

    @classmethod
    def from_inputs(cls, inputs, output_dir):
        return cls(
            output_dir=output_dir,
            participant_dir=output_dir / f"sub-{inputs.participant}",
        )

@dataclass
class YourProcedureDefaults:
    """Default configuration."""
    param1: int = 8
    docker_image: str = "tool/image:latest"
```

### 2. Create Runner (`runners/your_procedure.py`)

```python
from voxelops.runners._base import run_docker, validate_input_dir
from voxelops.schemas.your_procedure import (
    YourProcedureInputs,
    YourProcedureOutputs,
    YourProcedureDefaults,
)

def run_your_procedure(
    inputs: YourProcedureInputs,
    config: Optional[YourProcedureDefaults] = None,
    **overrides
) -> Dict[str, Any]:
    """Run your procedure."""
    config = config or YourProcedureDefaults()

    # Apply overrides
    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)

    # Validate
    validate_input_dir(inputs.input_dir)

    # Setup paths
    output_dir = inputs.output_dir or default
    expected_outputs = YourProcedureOutputs.from_inputs(inputs, output_dir)

    # Build command
    cmd = ["docker", "run", "--rm", ...]

    # Execute
    result = run_docker(cmd, "your_tool", inputs.participant, log_dir)

    # Add context
    result['inputs'] = inputs
    result['config'] = config
    result['expected_outputs'] = expected_outputs

    return result
```

### 3. Update Exports

Add to `schemas/__init__.py`:
```python
from voxelops.schemas.your_procedure import (
    YourProcedureInputs,
    YourProcedureOutputs,
    YourProcedureDefaults,
)
```

Add to `runners/__init__.py`:
```python
from voxelops.runners.your_procedure import run_your_procedure
```

Add to main `__init__.py`:
```python
from voxelops.runners import run_your_procedure
from voxelops.schemas import (
    YourProcedureInputs,
    YourProcedureOutputs,
    YourProcedureDefaults,
)
```

### 4. Add Tests

Create `tests/test_your_procedure.py` following the pattern in `tests/test_runners.py`.

## Key Design Decisions

### Why Dataclasses for Schemas?

- Type hints for IDE support
- Automatic `__init__` and `__repr__`
- Immutable by default (can use `frozen=True`)
- Simple, standard Python

### Why Functions Not Classes?

- Simpler: No inheritance, no state
- Clearer: Input → function → output
- Easier to test: Mock the function call
- No framework lock-in

### Why Store Command in Record?

- **Perfect reproducibility**: Just run the command again
- **Auditability**: See exactly what was executed
- **Debugging**: Reproduce failures exactly
- **Versioning**: Command includes image version

### Why Minimal Dependencies?

- Faster installation
- Fewer breaking changes
- Easier maintenance
- No heavyweight frameworks (Nipype, etc.)

### Why Not Validate Outputs?

- Docker container handles that
- Keep this package simple
- Use BIDS validator separately if needed
- Procedure either succeeds or fails (exit code)

## Comparison with v1

| Aspect | v1 (Complex) | v2 (Simple) |
|--------|--------------|-------------|
| Lines of code | ~8,000 | ~1,500 |
| Files | 48 | 15 |
| Dependencies | Nipype, traits | None |
| Classes | 15+ | 0 |
| Inheritance levels | 4 | 0 |
| To run QSIPrep | 10 lines, 3 imports | 1 function call |
| Database integration | Complex extraction | Just save the dict |
| Reproducibility | Reconstruct from config | Command in record |
| Learning curve | Hours | Minutes |

## Why This Works for Brain Banks

1. **Reproducibility**: Command is in the record
2. **Auditability**: Every execution logged
3. **Database Integration**: Results are dicts
4. **Consistency**: Define standards once
5. **Simplicity**: Anyone can understand

## Future Extensions

Potential additions (keep it simple!):

- **CLI**: Simple `voxelops run qsiprep ...`
- **Validation**: Pre-flight checks (disk space, etc.)
- **Batch Helpers**: Parallel execution utilities
- **More Procedures**: fMRIPrep, FreeSurfer, etc.

But maintain the core principle: **Simple functions that return dicts.**
