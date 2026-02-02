# VoxelOps Architecture

## Design Principles

1. **Simplicity** -- Functions, not classes. Dicts, not complex objects.
2. **Clarity** -- Typed dataclass schemas for every input, output, and configuration.
3. **Reproducibility** -- The exact Docker command is stored in every execution record.
4. **Database-Friendly** -- Results are plain dicts, trivial to persist anywhere.
5. **Extensibility** -- New procedures follow the same pattern, easy to add.

## Directory Structure

```
VoxelOps/
    src/voxelops/
        __init__.py                  # Package exports, version
        exceptions.py                # Exception hierarchy
        runners/
            __init__.py              # Runner exports
            _base.py                 # Shared: run_docker, validate_input_dir, validate_participant
            heudiconv.py             # DICOM -> BIDS
            qsiprep.py               # Diffusion preprocessing
            qsirecon.py              # Diffusion reconstruction
            qsiparc.py               # Parcellation (via parcellate, not Docker)
        schemas/
            __init__.py              # Schema exports
            heudiconv.py             # HeudiconvInputs / Outputs / Defaults
            qsiprep.py               # QSIPrepInputs / Outputs / Defaults
            qsirecon.py              # QSIReconInputs / Outputs / Defaults
            qsiparc.py               # QSIParcInputs / Outputs / Defaults
        utils/
            __init__.py
            bids.py                  # BIDS post-processing (IntendedFor, fmap cleanup)
    examples/
        dicom_to_bids.py             # HeudiConv example
        qsiprep.py                   # QSIPrep example
        qsirecon.py                  # QSIRecon example
        qsiparc.py                   # QSIParc example
    notebooks/
        01_heudiconv_basics.ipynb    # Step-by-step tutorials
        02_qsiprep_basics.ipynb
        03_qsirecon_basics.ipynb
        04_qsiparc_basics.ipynb
        05_full_pipeline.ipynb
    tests/                           # Pytest test suite
    docs/                            # Sphinx documentation source
    pyproject.toml                   # Build config, dependencies
```

## Code Organization

### Runners (`runners/`)

Each runner is a function that:

1. Accepts an `Inputs` dataclass and optional `Defaults` config
2. Validates inputs (directory exists, participant found)
3. Builds a Docker command (or calls `parcellate` directly for QSIParc)
4. Executes via `run_docker()` (or `run_parcellations()`)
5. Returns an execution record dict with expected outputs

```python
def run_procedure(
    inputs: ProcedureInputs,
    config: Optional[ProcedureDefaults] = None,
    **overrides,
) -> Dict[str, Any]:
    config = config or ProcedureDefaults()

    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)

    validate_input_dir(inputs.input_dir)
    validate_participant(inputs.input_dir, inputs.participant)

    output_dir = inputs.output_dir or default_path
    expected_outputs = ProcedureOutputs.from_inputs(inputs, output_dir)

    cmd = ["docker", "run", "--rm", ...]
    result = run_docker(cmd, "tool_name", inputs.participant, log_dir)

    result["inputs"] = inputs
    result["config"] = config
    result["expected_outputs"] = expected_outputs
    return result
```

### Schemas (`schemas/`)

Each procedure defines three dataclasses:

**Inputs** -- required parameters with `__post_init__` path coercion:

```python
@dataclass
class ProcedureInputs:
    input_dir: Path
    participant: str
    output_dir: Optional[Path] = None

    def __post_init__(self):
        self.input_dir = Path(self.input_dir)
        if self.output_dir:
            self.output_dir = Path(self.output_dir)
```

**Outputs** -- generated from inputs via `from_inputs()` classmethod:

```python
@dataclass
class ProcedureOutputs:
    output_dir: Path
    participant_dir: Path

    @classmethod
    def from_inputs(cls, inputs, output_dir):
        return cls(
            output_dir=output_dir,
            participant_dir=output_dir / f"sub-{inputs.participant}",
        )
```

**Defaults** -- configuration with brain bank standard values:

```python
@dataclass
class ProcedureDefaults:
    nprocs: int = 8
    mem_mb: int = 16000
    docker_image: str = "tool/image:latest"
```

### Base Utilities (`runners/_base.py`)

Three shared functions:

- `validate_input_dir(path, dir_type)` -- raises `InputValidationError` if missing or not a directory
- `validate_participant(input_dir, participant, prefix)` -- raises `InputValidationError` if participant subdir not found
- `run_docker(cmd, tool_name, participant, log_dir, capture_output)` -- executes subprocess, builds execution record, writes JSON log, raises `ProcedureExecutionError` on failure

### BIDS Utilities (`utils/bids.py`)

Post-processing for HeudiConv output:

- `post_process_heudiconv_output()` -- orchestrates three steps after DICOM conversion
- `verify_fmap_epi_files()` -- checks fieldmap NIfTI + JSON exist
- `add_intended_for_to_fmaps()` -- writes `IntendedFor` into fmap JSON sidecars
- `remove_bval_bvec_from_fmaps()` -- hides spurious `.bvec`/`.bval` files from fmap dirs

### Exceptions (`exceptions.py`)

```
YALabProcedureError              (base, aliased as ProcedureError)
    ProcedureExecutionError
        DockerExecutionError
    ProcedureConfigurationError
        FreeSurferLicenseError
    InputValidationError
    OutputCollectionError
    BIDSValidationError
    DependencyError
```

## Execution Flow

```
User calls run_procedure(inputs, config)
    -> Validate inputs
    -> Generate expected outputs
    -> Build Docker command
    -> run_docker() executes subprocess
    -> Build execution record dict
    -> Attach inputs, config, expected_outputs
    -> Return dict
```

## Execution Record Structure

```python
{
    "tool": str,
    "participant": str,
    "command": List[str],
    "exit_code": int,
    "start_time": str,              # ISO format
    "end_time": str,
    "duration_seconds": float,
    "duration_human": str,
    "success": bool,
    "log_file": str,                # Path to JSON log (if log_dir provided)
    "stdout": str,                  # If capture_output=True
    "stderr": str,
    "error": str,                   # If failed
    "inputs": ProcedureInputs,
    "config": ProcedureDefaults,
    "expected_outputs": ProcedureOutputs,
}
```

## Adding a New Procedure

1. **Schema** -- create `schemas/your_procedure.py` with `Inputs`, `Outputs`, `Defaults`
2. **Runner** -- create `runners/your_procedure.py` with `run_your_procedure()`
3. **Exports** -- add to `schemas/__init__.py`, `runners/__init__.py`, and `__init__.py`
4. **Tests** -- create `tests/test_runners_your_procedure.py` and `tests/test_schemas_your_procedure.py`
5. **Example** -- add `examples/your_procedure.py`

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Dataclasses for schemas | Type hints for IDE support, automatic `__init__` and `__repr__` |
| Functions, not classes | Simpler, no state, no inheritance, easier to test |
| Command stored in record | Perfect reproducibility -- just rerun the command |
| Minimal dependencies | Faster installs, fewer breaking changes, no Nipype lock-in |
| No output validation | Docker container handles that; keep this package simple |
