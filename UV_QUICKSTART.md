# uv Quick Start Guide

Quick reference for using uv with voxelops.

## Installation

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Verify installation
uv --version
```

## First Time Setup

```bash
# Clone repository
git clone https://github.com/yalab-devops/voxelops.git
cd voxelops

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Install package in development mode
uv pip install -e ".[dev]"

# Run tests to verify
pytest
```

## Daily Development Commands

### Installing Dependencies

```bash
# Install base package
uv pip install -e .

# Install with dev dependencies
uv pip install -e ".[dev]"

# Install with notebooks support
uv pip install -e ".[notebooks]"

# Install with config file support
uv pip install -e ".[config]"

# Install with everything
uv pip install -e ".[dev,notebooks,config]"
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=voxelops

# Specific test file
pytest tests/test_runners_qsiprep.py

# Specific test
pytest tests/test_runners_qsiprep.py::test_basic_run
```

### Code Quality

```bash
# Format code
black src tests

# Check formatting (no changes)
black --check src tests

# Lint code
ruff check src tests

# Auto-fix linting issues
ruff check src tests --fix
```

### Managing Dependencies

```bash
# Update lock file after changing pyproject.toml
uv lock

# Upgrade all dependencies
uv lock --upgrade

# Upgrade specific package
uv lock --upgrade-package pytest

# Sync environment with lock file
uv pip sync
```

## Common Workflows

### Starting a New Feature

```bash
# Create and switch to feature branch
git checkout -b feature/my-feature

# Ensure dependencies are up to date
uv pip install -e ".[dev]"

# Make your changes...

# Run tests
pytest

# Format and lint
black src tests
ruff check src tests --fix

# Commit
git add .
git commit -m "Add my feature"
```

### Adding a New Dependency

```bash
# 1. Edit pyproject.toml
# Add to dependencies = [...] or [project.optional-dependencies]

# 2. Update lock file
uv lock

# 3. Install
uv pip install -e .

# 4. Commit both files
git add pyproject.toml uv.lock
git commit -m "Add new-package dependency"
```

### Updating Dependencies

```bash
# Update all packages
uv lock --upgrade
uv pip install -e ".[dev]"

# Run tests to verify
pytest

# If all good, commit
git add uv.lock
git commit -m "Update dependencies"
```

## Notebook Development

```bash
# Install notebook dependencies
uv pip install -e ".[notebooks]"

# Start Jupyter
jupyter notebook

# Or use Jupyter Lab
jupyter lab
```

## Virtual Environment Management

### Creating Environments

```bash
# Default (uses .python-version)
uv venv

# Specific Python version
uv venv --python 3.11
uv venv --python 3.8

# Named environment
uv venv .venv-py38 --python 3.8
```

### Using Environments

```bash
# Activate
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Check which Python
which python
python --version

# Deactivate
deactivate
```

### Removing Environments

```bash
# Remove virtual environment
rm -rf .venv

# Recreate
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

## Package Installation Modes

### User Installation

```bash
# Install from PyPI
uv pip install voxelops

# Install specific version
uv pip install voxelops==2.0.0

# Install with extras
uv pip install voxelops[notebooks]
```

### Development Installation

```bash
# Editable install (changes take effect immediately)
uv pip install -e .

# With dev dependencies
uv pip install -e ".[dev]"

# From specific path
uv pip install -e /path/to/voxelops
```

## Performance Tips

### Faster Installs

```bash
# Use system Python (if compatible)
uv venv --python python3.11

# Skip lock file verification for quick installs
uv pip sync --no-verify

# Use link mode (faster for local dev)
uv pip install -e . --link-mode=copy
```

### Caching

```bash
# uv automatically caches wheels in ~/.cache/uv/

# Clear cache if needed
rm -rf ~/.cache/uv/
```

## Troubleshooting

### Command not found

```bash
# Add to PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Add to shell profile (~/.bashrc, ~/.zshrc)
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
```

### Lock file issues

```bash
# Regenerate lock file
uv lock --upgrade

# Force sync
uv pip sync --force
```

### Import errors

```bash
# Ensure package is installed
uv pip install -e ".[dev]"

# Check installation
uv pip list | grep voxelops

# Reinstall
uv pip uninstall voxelops
uv pip install -e ".[dev]"
```

### Virtual environment not activating

```bash
# Check if created correctly
ls .venv/bin/  # Should see python, activate, etc.

# Recreate if necessary
rm -rf .venv
uv venv
source .venv/bin/activate
```

## Comparison with pip

| Task | pip | uv |
|------|-----|-----|
| Install package | `pip install package` | `uv pip install package` |
| Install editable | `pip install -e .` | `uv pip install -e .` |
| Install with extras | `pip install ".[dev]"` | `uv pip install ".[dev]"` |
| Uninstall | `pip uninstall package` | `uv pip uninstall package` |
| List packages | `pip list` | `uv pip list` |
| Show package | `pip show package` | `uv pip show package` |
| Freeze deps | `pip freeze` | `uv pip freeze` |
| Create venv | `python -m venv .venv` | `uv venv` |

**Key difference**: uv is much faster (10-100x) and has better dependency resolution!

## VS Code Integration

Add to `.vscode/settings.json`:

```json
{
  "python.defaultInterpreterPath": "${workspaceFolder}/.venv/bin/python",
  "python.terminal.activateEnvironment": true,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.formatting.provider": "black",
  "python.linting.ruffEnabled": true,
  "editor.formatOnSave": true
}
```

## Git Integration

Files to commit:
- ✅ `pyproject.toml` (dependencies)
- ✅ `uv.lock` (lock file)
- ✅ `.python-version` (Python version)
- ✅ `.uvignore` (uv ignore file)

Files to ignore (add to `.gitignore`):
```
.venv/
__pycache__/
*.pyc
.pytest_cache/
.coverage
htmlcov/
dist/
build/
*.egg-info/
```

## Next Steps

- Read [DEVELOPMENT.md](DEVELOPMENT.md) for detailed development guide
- Check [README.md](README.md) for package usage
- Explore [notebooks/](notebooks/) for examples
- See [ARCHITECTURE.md](ARCHITECTURE.md) for design details

## Resources

- **uv Documentation**: https://docs.astral.sh/uv/
- **uv GitHub**: https://github.com/astral-sh/uv
- **This Project**: https://github.com/yalab-devops/voxelops
