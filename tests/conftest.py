"""Shared fixtures and parcellate mock setup for VoxelOps tests.

The ``parcellate`` package is imported at module level in
``schemas/qsiparc.py`` and ``runners/qsiparc.py``.  Since
``voxelops.__init__`` transitively imports these, **no voxelops import
works** without first mocking ``parcellate`` in ``sys.modules``.

This module-level injection must happen before pytest discovers any
test that does ``from voxelops import ...``.
"""

import sys
import types
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# Mock the parcellate package hierarchy in sys.modules BEFORE any
# voxelops import can trigger the real import chain.
# ---------------------------------------------------------------------------

_parcellate = types.ModuleType("parcellate")
_parcellate_interfaces = types.ModuleType("parcellate.interfaces")
_parcellate_interfaces_models = types.ModuleType("parcellate.interfaces.models")
_parcellate_interfaces_qsirecon = types.ModuleType("parcellate.interfaces.qsirecon")
_parcellate_interfaces_qsirecon_models = types.ModuleType(
    "parcellate.interfaces.qsirecon.models"
)
_parcellate_interfaces_qsirecon_qsirecon = types.ModuleType(
    "parcellate.interfaces.qsirecon.qsirecon"
)


# Provide a stub AtlasDefinition that behaves enough like a dataclass
class MockAtlasDefinition:
    """Minimal stand-in for parcellate.interfaces.models.AtlasDefinition."""

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


_parcellate_interfaces_models.AtlasDefinition = MockAtlasDefinition

# QSIReconConfig stub
MockQSIReconConfig = MagicMock(name="QSIReconConfig")
_parcellate_interfaces_qsirecon_models.QSIReconConfig = MockQSIReconConfig

# run_parcellations stub
_parcellate_interfaces_qsirecon_qsirecon.run_parcellations = MagicMock(
    name="run_parcellations", return_value=[]
)

# Wire the hierarchy together
_parcellate.interfaces = _parcellate_interfaces
_parcellate_interfaces.models = _parcellate_interfaces_models
_parcellate_interfaces.qsirecon = _parcellate_interfaces_qsirecon
_parcellate_interfaces_qsirecon.models = _parcellate_interfaces_qsirecon_models
_parcellate_interfaces_qsirecon.qsirecon = _parcellate_interfaces_qsirecon_qsirecon

sys.modules["parcellate"] = _parcellate
sys.modules["parcellate.interfaces"] = _parcellate_interfaces
sys.modules["parcellate.interfaces.models"] = _parcellate_interfaces_models
sys.modules["parcellate.interfaces.qsirecon"] = _parcellate_interfaces_qsirecon
sys.modules["parcellate.interfaces.qsirecon.models"] = (
    _parcellate_interfaces_qsirecon_models
)
sys.modules["parcellate.interfaces.qsirecon.qsirecon"] = (
    _parcellate_interfaces_qsirecon_qsirecon
)

# ---------------------------------------------------------------------------
# Now it is safe to import voxelops
# ---------------------------------------------------------------------------

import pytest  # noqa: E402


@pytest.fixture
def mock_bids_dir(tmp_path):
    """Create a minimal mock BIDS directory with one participant."""
    bids_dir = tmp_path / "bids"
    bids_dir.mkdir()
    (bids_dir / "sub-01").mkdir()
    return bids_dir


@pytest.fixture
def mock_qsiprep_dir(tmp_path):
    """Create a minimal mock QSIPrep output directory with one participant."""
    d = tmp_path / "derivatives" / "qsiprep"
    d.mkdir(parents=True)
    (d / "sub-01").mkdir()
    return d


@pytest.fixture
def mock_qsirecon_dir(tmp_path):
    """Create a minimal mock QSIRecon output directory with one participant."""
    d = tmp_path / "derivatives" / "qsirecon"
    d.mkdir(parents=True)
    (d / "sub-01").mkdir()
    return d


@pytest.fixture
def mock_dicom_dir(tmp_path):
    """Create a minimal mock DICOM directory."""
    d = tmp_path / "dicoms"
    d.mkdir()
    return d


@pytest.fixture
def mock_heuristic(tmp_path):
    """Create a minimal heuristic.py file."""
    h = tmp_path / "heuristic.py"
    h.write_text("# heuristic stub\n")
    return h


@pytest.fixture
def mock_fs_license(tmp_path):
    """Create a minimal FreeSurfer license file."""
    f = tmp_path / "license.txt"
    f.write_text("dummy license\n")
    return f


@pytest.fixture
def mock_recon_spec(tmp_path):
    """Create a minimal recon spec YAML file."""
    f = tmp_path / "recon_spec.yaml"
    f.write_text("name: test\n")
    return f


@pytest.fixture
def mock_bids_filters(tmp_path):
    """Create a minimal BIDS filters JSON file."""
    import json

    f = tmp_path / "bids_filters.json"
    f.write_text(json.dumps({"dwi": {"datatype": "dwi"}}))
    return f
