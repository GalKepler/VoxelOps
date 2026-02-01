"""Tests for procedure runners."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from voxelops import (
    run_qsiprep,
    QSIPrepInputs,
    QSIPrepDefaults,
    InputValidationError,
)


@pytest.fixture
def mock_bids_dir(tmp_path):
    """Create a mock BIDS directory structure."""
    bids_dir = tmp_path / "bids"
    bids_dir.mkdir()

    # Create participant directory
    participant_dir = bids_dir / "sub-01"
    participant_dir.mkdir()

    return bids_dir


@pytest.fixture
def qsiprep_inputs(mock_bids_dir):
    """Create QSIPrepInputs for testing."""
    return QSIPrepInputs(
        bids_dir=mock_bids_dir,
        participant="01",
    )


def test_qsiprep_inputs_creation(qsiprep_inputs, mock_bids_dir):
    """Test QSIPrepInputs creation."""
    assert qsiprep_inputs.bids_dir == mock_bids_dir
    assert qsiprep_inputs.participant == "01"
    assert qsiprep_inputs.output_dir is None
    assert qsiprep_inputs.work_dir is None


def test_qsiprep_defaults():
    """Test QSIPrepDefaults."""
    defaults = QSIPrepDefaults()

    assert defaults.nprocs == 8
    assert defaults.mem_gb == 16
    assert defaults.output_resolution == 1.6
    assert defaults.output_spaces == ["MNI152NLin2009cAsym"]
    assert defaults.longitudinal is True
    assert defaults.docker_image == "pennlinc/qsiprep:1.0.2"


def test_qsiprep_validation_missing_bids_dir(tmp_path):
    """Test validation fails when BIDS directory doesn't exist."""
    inputs = QSIPrepInputs(
        bids_dir=tmp_path / "nonexistent",
        participant="01",
    )

    with pytest.raises(InputValidationError, match="BIDS directory not found"):
        run_qsiprep(inputs)


def test_qsiprep_validation_missing_participant(mock_bids_dir):
    """Test validation fails when participant doesn't exist."""
    inputs = QSIPrepInputs(
        bids_dir=mock_bids_dir,
        participant="99",  # Doesn't exist
    )

    with pytest.raises(InputValidationError, match="Participant sub-99 not found"):
        run_qsiprep(inputs)


@patch("voxelops.runners.qsiprep.run_docker")
def test_qsiprep_command_building(mock_run_docker, qsiprep_inputs, tmp_path):
    """Test that QSIPrep builds correct Docker command."""
    # Mock run_docker to inspect command
    mock_run_docker.return_value = {
        "tool": "qsiprep",
        "participant": "01",
        "command": [],
        "success": True,
        "duration_seconds": 100,
        "duration_human": "0:01:40",
    }

    # Run
    result = run_qsiprep(qsiprep_inputs, nprocs=4, mem_gb=8)

    # Check run_docker was called
    assert mock_run_docker.called

    # Get the command that was built
    call_args = mock_run_docker.call_args
    cmd = call_args.kwargs["cmd"]

    # Verify command structure
    assert cmd[0:2] == ["docker", "run"]
    assert "--rm" in cmd
    assert any("--participant-label=01" in arg for arg in cmd)
    assert any("--nprocs=4" in arg for arg in cmd)
    assert any("--mem-gb=8" in arg for arg in cmd)


@patch("voxelops.runners.qsiprep.run_docker")
def test_qsiprep_output_paths(mock_run_docker, qsiprep_inputs):
    """Test that expected outputs are generated correctly."""
    mock_run_docker.return_value = {
        "tool": "qsiprep",
        "participant": "01",
        "command": [],
        "success": True,
        "duration_seconds": 100,
        "duration_human": "0:01:40",
    }

    result = run_qsiprep(qsiprep_inputs)

    # Check expected outputs are in result
    assert "expected_outputs" in result
    outputs = result["expected_outputs"]

    assert outputs.qsiprep_dir.name == "qsiprep"
    assert outputs.participant_dir.name == "sub-01"
    assert "sub-01" in str(outputs.html_report)


@patch("voxelops.runners.qsiprep.run_docker")
def test_qsiprep_config_override(mock_run_docker, qsiprep_inputs):
    """Test that config parameters can be overridden."""
    mock_run_docker.return_value = {
        "tool": "qsiprep",
        "participant": "01",
        "command": [],
        "success": True,
    }

    # Override defaults
    result = run_qsiprep(
        qsiprep_inputs,
        nprocs=32,
        mem_gb=64,
        output_resolution=2.0,
    )

    # Get command
    cmd = mock_run_docker.call_args.kwargs["cmd"]

    # Verify overrides were applied
    assert any("--nprocs=32" in arg for arg in cmd)
    assert any("--mem-gb=64" in arg for arg in cmd)
    assert any("--output-resolution=2.0" in arg for arg in cmd)


@patch("voxelops.runners.qsiprep.run_docker")
def test_qsiprep_result_structure(mock_run_docker, qsiprep_inputs):
    """Test that result has expected structure."""
    mock_run_docker.return_value = {
        "tool": "qsiprep",
        "participant": "01",
        "command": ["docker", "run"],
        "exit_code": 0,
        "start_time": "2026-01-26T10:00:00",
        "end_time": "2026-01-26T11:00:00",
        "duration_seconds": 3600,
        "duration_human": "1:00:00",
        "success": True,
        "log_file": "/path/to/log.json",
    }

    result = run_qsiprep(qsiprep_inputs)

    # Check all expected keys
    assert result["tool"] == "qsiprep"
    assert result["participant"] == "01"
    assert "command" in result
    assert "exit_code" in result
    assert "start_time" in result
    assert "end_time" in result
    assert "duration_seconds" in result
    assert "duration_human" in result
    assert "success" in result
    assert "inputs" in result
    assert "config" in result
    assert "expected_outputs" in result


def test_input_path_conversion():
    """Test that string paths are converted to Path objects."""
    inputs = QSIPrepInputs(
        bids_dir="/data/bids",  # String
        participant="01",
    )

    assert isinstance(inputs.bids_dir, Path)
    assert inputs.bids_dir == Path("/data/bids")
