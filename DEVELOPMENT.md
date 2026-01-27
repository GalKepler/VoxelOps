# Development Guide

This guide covers development setup for voxelops using uv.

## Why uv?

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver, written in Rust. It's 10-100x faster than pip and provides:

- **Speed**: Resolves and installs dependencies much faster than pip
- **Reliability**: Better dependency resolution
- **Reproducibility**: Lock files ensure consistent installs
- **Compatibility**: Works with existing pip workflows
- **Virtual environments**: Built-in venv management

## Quick Start

### 1. Install uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### 2. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/yalab-devops/voxelops.git
cd voxelops

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install package in editable mode with dev dependencies
uv pip install -e ".[dev]"
```

### 3. Verify Installation

```bash
# Run tests
pytest

# Check code formatting
black --check src tests

# Run linter
ruff check src tests
```

## uv Commands Reference

### Package Management

```bash
# Install dependencies
uv pip install -r requirements.txt

# Install with extras
uv pip install -e ".[dev]"           # Dev dependencies
uv pip install -e ".[notebooks]"     # Jupyter notebooks
uv pip install -e ".[config]"        # Config file support
uv pip install -e ".[dev,notebooks]" # Multiple extras

# Add a new dependency
uv pip install some-package

# Update dependencies and lock file
uv lock --upgrade

# Sync environment with lock file
uv pip sync
```

### Virtual Environments

```bash
# Create virtual environment
uv venv

# Create with specific Python version
uv venv --python 3.11

# Activate (same as standard venv)
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Deactivate
deactivate
```

### Lock Files

```bash
# Generate lock file (already done)
uv lock

# Update all dependencies
uv lock --upgrade

# Update specific package
uv lock --upgrade-package pytest
```

## Development Workflow

### Initial Setup

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USERNAME/voxelops.git
cd voxelops

# 2. Create virtual environment
uv venv
source .venv/bin/activate

# 3. Install in development mode
uv pip install -e ".[dev]"

# 4. Create a branch
git checkout -b feature/your-feature
```

### Making Changes

```bash
# 1. Make your changes to src/voxelops/

# 2. Format code
black src tests

# 3. Lint code
ruff check src tests --fix

# 4. Run tests
pytest

# 5. Check coverage
pytest --cov=voxelops --cov-report=html
```

### Adding Dependencies

#### Runtime Dependency

```bash
# Edit pyproject.toml to add to dependencies list
dependencies = [
    "new-package>=1.0",
]

# Update lock file
uv lock

# Install updated dependencies
uv pip install -e .
```

#### Development Dependency

```bash
# Edit pyproject.toml to add to dev dependency group
[dependency-groups]
dev = [
    "pytest>=7.0",
    "new-dev-tool>=2.0",  # Add here
]

# Update lock file
uv lock

# Install updated dependencies
uv pip install -e ".[dev]"
```

#### Optional Dependency

```bash
# Edit pyproject.toml to add to optional-dependencies
[project.optional-dependencies]
new-extra = [
    "optional-package>=1.0",
]

# Update lock file
uv lock

# Install with new extra
uv pip install -e ".[new-extra]"
```

## Testing

### Run All Tests

```bash
pytest
```

### Run Specific Test File

```bash
pytest tests/test_runners.py
```

### Run Specific Test

```bash
pytest tests/test_runners.py::test_qsiprep_basic
```

### With Coverage

```bash
pytest --cov=voxelops --cov-report=term-missing
```

### With HTML Coverage Report

```bash
pytest --cov=voxelops --cov-report=html
open htmlcov/index.html  # View report
```

## Code Quality

### Formatting with Black

```bash
# Check formatting
black --check src tests

# Format code
black src tests
```

### Linting with Ruff

```bash
# Check for issues
ruff check src tests

# Auto-fix issues
ruff check src tests --fix

# Check specific file
ruff check src/voxelops/runners/qsiprep.py
```

## Project Structure

```
voxelops-v2/
├── src/
│   └── voxelops/
│       ├── __init__.py
│       ├── exceptions.py
│       ├── runners/
│       │   ├── __init__.py
│       │   ├── _base.py
│       │   ├── heudiconv.py
│       │   ├── qsiprep.py
│       │   ├── qsirecon.py
│       │   └── qsiparc.py
│       └── schemas/
│           ├── __init__.py
│           ├── heudiconv.py
│           ├── qsiprep.py
│           ├── qsirecon.py
│           └── qsiparc.py
├── tests/
│   └── test_runners.py
├── examples/
│   ├── full_pipeline.py
│   └── brain_bank_integration.py
├── notebooks/
│   ├── 01_heudiconv_basics.ipynb
│   ├── 02_qsiprep_basics.ipynb
│   ├── 03_qsirecon_basics.ipynb
│   ├── 04_qsiparc_basics.ipynb
│   ├── 05_full_pipeline.ipynb
│   └── README.md
├── pyproject.toml
├── uv.lock
├── .python-version
├── README.md
├── DEVELOPMENT.md (this file)
└── ARCHITECTURE.md
```

## Adding a New Procedure

1. **Create schema** in `src/voxelops/schemas/`:
   ```python
   # your_procedure.py
   from dataclasses import dataclass
   from pathlib import Path
   from typing import Optional

   @dataclass
   class YourProcedureInputs:
       """Required inputs."""
       input_dir: Path
       participant: str

   @dataclass
   class YourProcedureOutputs:
       """Expected outputs."""
       output_dir: Path

       @classmethod
       def from_inputs(cls, inputs, output_dir):
           return cls(output_dir=output_dir)

   @dataclass
   class YourProcedureDefaults:
       """Default configuration."""
       nprocs: int = 8
       docker_image: str = "tool/image:latest"
   ```

2. **Create runner** in `src/voxelops/runners/`:
   ```python
   # your_procedure.py
   from pathlib import Path
   from typing import Dict, Any, Optional
   from ..schemas.your_procedure import (
       YourProcedureInputs,
       YourProcedureOutputs,
       YourProcedureDefaults,
   )
   from ._base import run_docker, validate_input_dir

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

       # Validate inputs
       validate_input_dir(inputs.input_dir)

       # Build Docker command
       cmd = ["docker", "run", "--rm", ...]

       # Execute
       result = run_docker(cmd, "your_procedure", inputs.participant)

       # Add context
       result['inputs'] = inputs
       result['config'] = config
       result['expected_outputs'] = YourProcedureOutputs.from_inputs(...)

       return result
   ```

3. **Add exports** in `src/voxelops/__init__.py`

4. **Write tests** in `tests/test_runners.py`

5. **Create example notebook** in `notebooks/`

6. **Update documentation** in README.md

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Install uv
        uses: astral-sh/setup-uv@v1

      - name: Set up Python
        run: uv python install 3.11

      - name: Install dependencies
        run: |
          uv venv
          uv pip install -e ".[dev]"

      - name: Run tests
        run: uv run pytest

      - name: Check formatting
        run: uv run black --check src tests

      - name: Lint
        run: uv run ruff check src tests
```

## Tips

### Faster Installs

uv is already fast, but you can make it even faster:

```bash
# Use cached wheels
uv pip install -e ".[dev]" --cache-dir ~/.uv-cache

# Skip lock file validation for quick installs
uv pip sync --no-verify
```

### Working with Multiple Python Versions

```bash
# Create venv with specific Python
uv venv --python 3.8
uv venv --python 3.11

# Test against multiple versions
for version in 3.8 3.9 3.10 3.11; do
    uv venv --python $version .venv-$version
    source .venv-$version/bin/activate
    uv pip install -e ".[dev]"
    pytest
    deactivate
done
```

### Integration with IDEs

#### VS Code

Add to `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.terminal.activateEnvironment": true
}
```

#### PyCharm

1. Go to Settings → Project → Python Interpreter
2. Click gear icon → Add
3. Select "Existing environment"
4. Choose `.venv/bin/python`

## Troubleshooting

### uv command not found

```bash
# Ensure uv is in PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Or reinstall
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Lock file out of sync

```bash
# Regenerate lock file
uv lock

# Force sync
uv pip sync --force
```

### Virtual environment issues

```bash
# Remove and recreate
rm -rf .venv
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Resources

- **uv Documentation**: https://docs.astral.sh/uv/
- **Project Repository**: https://github.com/yalab-devops/voxelops
- **Issue Tracker**: https://github.com/yalab-devops/voxelops/issues

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.
