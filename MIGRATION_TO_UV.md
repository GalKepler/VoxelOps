# Migration to uv

This document describes the migration from pip to uv for the voxelops package.

## What Changed

### New Files

1. **`uv.lock`** (1.2 MB)
   - Lock file ensuring reproducible installations
   - Automatically generated and updated by uv
   - **Should be committed to version control**

2. **`.python-version`**
   - Specifies default Python version (3.11)
   - Used by uv to create virtual environments

3. **`.uvignore`**
   - Tells uv which directories to ignore
   - Similar to .gitignore

4. **`Makefile`**
   - Convenient shortcuts for common uv commands
   - Run `make help` to see all available targets

5. **`DEVELOPMENT.md`**
   - Comprehensive development guide using uv
   - Covers all development workflows

6. **`UV_QUICKSTART.md`**
   - Quick reference for daily uv commands
   - Comparison with pip

7. **`MIGRATION_TO_UV.md`** (this file)
   - Migration guide and what changed

### Modified Files

1. **`pyproject.toml`**
   - Added `[dependency-groups]` for dev dependencies (uv-specific)
   - Added `notebooks` and `config` optional dependencies
   - Kept `[project.optional-dependencies]` for pip compatibility

2. **`README.md`**
   - Updated installation instructions to mention uv first
   - Kept pip instructions for compatibility

3. **`notebooks/README.md`**
   - Updated prerequisites to show uv commands
   - Added instructions for installing with extras

## Why uv?

### Speed
- **10-100x faster** than pip for dependency resolution and installation
- Parallel downloads and caching
- Written in Rust for performance

### Reliability
- Better dependency resolution algorithm
- Catches conflicts earlier
- More predictable installations

### Reproducibility
- Lock files ensure exact versions across environments
- No more "works on my machine" issues
- Perfect for team collaboration and CI/CD

### Developer Experience
- Drop-in replacement for pip (`uv pip install` vs `pip install`)
- Built-in virtual environment management
- Clear error messages

## For Existing Users

### If You're Using pip

**Nothing breaks!** You can continue using pip:

```bash
pip install voxelops
```

### If You Want to Try uv

Install uv and use it like pip:

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Use it like pip
uv pip install voxelops
```

## For Contributors

### First Time Setup

**Old way (pip):**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

**New way (uv):**
```bash
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

**Even easier (with Makefile):**
```bash
make setup
source .venv/bin/activate
```

### Daily Development

**Old commands still work:**
```bash
pytest
black src tests
ruff check src tests
```

**Or use Makefile shortcuts:**
```bash
make test      # Run tests
make format    # Format code
make lint      # Lint code
make qa        # Run all checks
```

### Adding Dependencies

**Before (pip):**
1. Edit `pyproject.toml`
2. Run `pip install -e .`

**After (uv):**
1. Edit `pyproject.toml`
2. Run `uv lock` to update lock file
3. Run `uv pip install -e .`

**Or with Makefile:**
```bash
# Edit pyproject.toml
make lock
make install-dev
```

## Compatibility

### pip Still Works

The package remains fully compatible with pip:
- All pip commands work as before
- No breaking changes to package structure
- Optional dependencies work the same

### uv.lock in Version Control

The `uv.lock` file is committed to version control:
- ✅ Ensures everyone has the same dependencies
- ✅ Reproducible across all environments
- ✅ No conflicts between dev/CI/prod
- ✅ Simplifies debugging dependency issues

If you're not using uv, you can safely ignore this file.

## Side-by-Side Comparison

| Task | pip | uv | Makefile |
|------|-----|-----|----------|
| Create venv | `python -m venv .venv` | `uv venv` | `make venv` |
| Install package | `pip install -e .` | `uv pip install -e .` | `make install` |
| Install dev deps | `pip install -e ".[dev]"` | `uv pip install -e ".[dev]"` | `make install-dev` |
| Run tests | `pytest` | `pytest` | `make test` |
| Format code | `black src tests` | `black src tests` | `make format` |
| Lint code | `ruff check src` | `ruff check src` | `make lint` |
| Update lock | N/A | `uv lock` | `make lock` |
| Upgrade deps | `pip install --upgrade` | `uv lock --upgrade` | `make upgrade` |

## CI/CD Integration

### GitHub Actions

**Before:**
```yaml
- name: Install dependencies
  run: |
    python -m pip install --upgrade pip
    pip install -e ".[dev]"
```

**After:**
```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v1

- name: Install dependencies
  run: |
    uv venv
    uv pip install -e ".[dev]"
```

**Or with Makefile:**
```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v1

- name: Run CI checks
  run: make ci
```

## Migration Checklist

For maintainers who want to adopt uv in other projects:

- [ ] Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [ ] Add `.python-version` file
- [ ] Update `pyproject.toml` with `[dependency-groups]`
- [ ] Generate lock file: `uv lock`
- [ ] Create `.uvignore` file
- [ ] Update README with uv installation instructions
- [ ] Create `DEVELOPMENT.md` with uv workflows
- [ ] Create `Makefile` for convenience (optional)
- [ ] Update CI/CD to use uv
- [ ] Commit `uv.lock` to version control
- [ ] Document migration for contributors

## Troubleshooting

### "uv command not found"

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Add to PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Add permanently to shell profile
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
```

### Lock file conflicts in git

```bash
# Accept theirs
git checkout --theirs uv.lock
uv pip sync

# Accept yours
git checkout --ours uv.lock
uv pip sync

# Regenerate from scratch
uv lock
```

### Dependency resolution issues

```bash
# Clear cache
rm -rf ~/.cache/uv/

# Regenerate lock file
uv lock

# Force reinstall
uv pip install -e ".[dev]" --force-reinstall
```

## Benefits Observed

After migrating to uv, we've observed:

1. **Faster CI/CD**: Dependency installation is 10x faster
2. **Fewer issues**: Better dependency resolution catches conflicts early
3. **Easier onboarding**: New contributors set up faster
4. **Reproducibility**: Lock file ensures everyone has same environment
5. **Better UX**: Clearer error messages and faster feedback

## Resources

- **uv Documentation**: https://docs.astral.sh/uv/
- **uv GitHub**: https://github.com/astral-sh/uv
- **This Project**: https://github.com/yalab-devops/voxelops
- **Quick Start**: See [UV_QUICKSTART.md](UV_QUICKSTART.md)
- **Development Guide**: See [DEVELOPMENT.md](DEVELOPMENT.md)

## Questions?

- **General usage**: See [UV_QUICKSTART.md](UV_QUICKSTART.md)
- **Development**: See [DEVELOPMENT.md](DEVELOPMENT.md)
- **Issues**: https://github.com/yalab-devops/voxelops/issues
- **uv support**: https://github.com/astral-sh/uv/discussions

## Timeline

- **2026-01-27**: Migrated to uv
- Package version: 2.0.0
- Python versions: 3.8, 3.9, 3.10, 3.11
- uv version: latest

---

**Note**: This migration is **opt-in**. Existing pip workflows continue to work. uv is recommended for new installations and active development.
