"""Tests for voxelops.runners.qsiprep -- run_qsiprep."""

from unittest.mock import patch

import pytest

from voxelops.exceptions import InputValidationError
from voxelops.runners.qsiprep import run_qsiprep
from voxelops.schemas.qsiprep import QSIPrepDefaults, QSIPrepInputs


def _docker_ok():
    return {
        "tool": "qsiprep",
        "participant": "01",
        "command": [],
        "exit_code": 0,
        "success": True,
        "start_time": "t0",
        "end_time": "t1",
        "duration_seconds": 1,
        "duration_human": "0:00:01",
    }


# -- Config -------------------------------------------------------------------


class TestConfig:
    @patch("voxelops.runners.qsiprep.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsiprep.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsiprep.os.getgid", return_value=1000)
    def test_default_config(self, _gid, _uid, mock_rd, mock_bids_dir):
        inputs = QSIPrepInputs(bids_dir=mock_bids_dir, participant="01")
        result = run_qsiprep(inputs)
        assert result["config"].docker_image == "pennlinc/qsiprep:latest"

    @patch("voxelops.runners.qsiprep.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsiprep.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsiprep.os.getgid", return_value=1000)
    def test_custom_config(self, _gid, _uid, mock_rd, mock_bids_dir):
        inputs = QSIPrepInputs(bids_dir=mock_bids_dir, participant="01")
        cfg = QSIPrepDefaults(nprocs=16)
        result = run_qsiprep(inputs, config=cfg)
        assert result["config"].nprocs == 16

    @patch("voxelops.runners.qsiprep.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsiprep.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsiprep.os.getgid", return_value=1000)
    def test_override_known_key(self, _gid, _uid, mock_rd, mock_bids_dir):
        inputs = QSIPrepInputs(bids_dir=mock_bids_dir, participant="01")
        result = run_qsiprep(inputs, nprocs=32)
        assert result["config"].nprocs == 32

    @patch("voxelops.runners.qsiprep.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsiprep.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsiprep.os.getgid", return_value=1000)
    def test_override_unknown_key_ignored(self, _gid, _uid, mock_rd, mock_bids_dir):
        inputs = QSIPrepInputs(bids_dir=mock_bids_dir, participant="01")
        result = run_qsiprep(inputs, bogus=42)
        assert not hasattr(result["config"], "bogus")


# -- Validation ---------------------------------------------------------------


class TestValidation:
    def test_missing_bids_dir(self, tmp_path):
        inputs = QSIPrepInputs(bids_dir=tmp_path / "nope", participant="01")
        with pytest.raises(InputValidationError, match="BIDS directory not found"):
            run_qsiprep(inputs)

    def test_missing_participant(self, mock_bids_dir):
        inputs = QSIPrepInputs(bids_dir=mock_bids_dir, participant="99")
        with pytest.raises(InputValidationError, match="sub-99 not found"):
            run_qsiprep(inputs)


# -- Directory defaults -------------------------------------------------------


class TestDirectoryDefaults:
    @patch("voxelops.runners.qsiprep.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsiprep.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsiprep.os.getgid", return_value=1000)
    def test_default_output_dir(self, _gid, _uid, mock_rd, mock_bids_dir):
        inputs = QSIPrepInputs(bids_dir=mock_bids_dir, participant="01")
        result = run_qsiprep(inputs)
        expected_out = mock_bids_dir.parent / "derivatives"
        assert result["expected_outputs"].qsiprep_dir == expected_out / "qsiprep"

    @patch("voxelops.runners.qsiprep.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsiprep.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsiprep.os.getgid", return_value=1000)
    def test_default_work_dir(self, _gid, _uid, mock_rd, mock_bids_dir):
        inputs = QSIPrepInputs(bids_dir=mock_bids_dir, participant="01")
        result = run_qsiprep(inputs)
        expected_work = mock_bids_dir.parent / "work" / "qsiprep"
        assert result["expected_outputs"].work_dir == expected_work

    @patch("voxelops.runners.qsiprep.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsiprep.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsiprep.os.getgid", return_value=1000)
    def test_custom_output_dir(self, _gid, _uid, mock_rd, mock_bids_dir, tmp_path):
        custom = tmp_path / "custom_out"
        inputs = QSIPrepInputs(
            bids_dir=mock_bids_dir, participant="01", output_dir=custom
        )
        result = run_qsiprep(inputs)
        assert result["expected_outputs"].qsiprep_dir == custom / "qsiprep"


# -- Docker command flags -----------------------------------------------------


class TestDockerCommandFlags:
    @patch("voxelops.runners.qsiprep.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsiprep.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsiprep.os.getgid", return_value=1000)
    def test_fs_license_mount(self, _gid, _uid, mock_rd, mock_bids_dir, mock_fs_license):
        inputs = QSIPrepInputs(bids_dir=mock_bids_dir, participant="01")
        cfg = QSIPrepDefaults(fs_license=mock_fs_license)
        run_qsiprep(inputs, config=cfg)
        cmd = mock_rd.call_args.kwargs["cmd"]
        assert "--fs-license-file" in cmd
        assert "/license.txt" in cmd

    @patch("voxelops.runners.qsiprep.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsiprep.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsiprep.os.getgid", return_value=1000)
    def test_bids_filters_mount(self, _gid, _uid, mock_rd, mock_bids_dir, mock_bids_filters):
        inputs = QSIPrepInputs(
            bids_dir=mock_bids_dir, participant="01", bids_filters=mock_bids_filters
        )
        run_qsiprep(inputs)
        cmd = mock_rd.call_args.kwargs["cmd"]
        assert "--bids-filter-file" in cmd

    @patch("voxelops.runners.qsiprep.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsiprep.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsiprep.os.getgid", return_value=1000)
    def test_longitudinal_flag(self, _gid, _uid, mock_rd, mock_bids_dir):
        inputs = QSIPrepInputs(bids_dir=mock_bids_dir, participant="01")
        run_qsiprep(inputs, longitudinal=True)
        cmd = mock_rd.call_args.kwargs["cmd"]
        assert "--longitudinal" in cmd

    @patch("voxelops.runners.qsiprep.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsiprep.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsiprep.os.getgid", return_value=1000)
    def test_subject_anatomical_reference(self, _gid, _uid, mock_rd, mock_bids_dir):
        inputs = QSIPrepInputs(bids_dir=mock_bids_dir, participant="01")
        run_qsiprep(inputs)
        cmd = mock_rd.call_args.kwargs["cmd"]
        assert "--subject-anatomical-reference" in cmd
        idx = cmd.index("--subject-anatomical-reference")
        assert cmd[idx + 1] == "unbiased"

    @patch("voxelops.runners.qsiprep.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsiprep.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsiprep.os.getgid", return_value=1000)
    def test_skip_bids_validation(self, _gid, _uid, mock_rd, mock_bids_dir):
        inputs = QSIPrepInputs(bids_dir=mock_bids_dir, participant="01")
        run_qsiprep(inputs, skip_bids_validation=True)
        cmd = mock_rd.call_args.kwargs["cmd"]
        assert "--skip-bids-validation" in cmd

    @patch("voxelops.runners.qsiprep.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsiprep.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsiprep.os.getgid", return_value=1000)
    def test_anatomical_template_loop(self, _gid, _uid, mock_rd, mock_bids_dir):
        inputs = QSIPrepInputs(bids_dir=mock_bids_dir, participant="01")
        run_qsiprep(inputs, anatomical_template=["MNI152NLin2009cAsym", "T1w"])
        cmd = mock_rd.call_args.kwargs["cmd"]
        indices = [i for i, x in enumerate(cmd) if x == "--anatomical-template"]
        assert len(indices) == 2

    @patch("voxelops.runners.qsiprep.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsiprep.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsiprep.os.getgid", return_value=1000)
    def test_result_structure(self, _gid, _uid, mock_rd, mock_bids_dir):
        inputs = QSIPrepInputs(bids_dir=mock_bids_dir, participant="01")
        result = run_qsiprep(inputs)
        assert "inputs" in result
        assert "config" in result
        assert "expected_outputs" in result
        assert result["expected_outputs"].participant_dir.name == "sub-01"
