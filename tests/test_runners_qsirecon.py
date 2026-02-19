"""Tests for voxelops.runners.qsirecon -- run_qsirecon."""

from unittest.mock import patch

import pytest

from voxelops.exceptions import InputValidationError
from voxelops.runners.qsirecon import run_qsirecon
from voxelops.schemas.qsirecon import QSIReconDefaults, QSIReconInputs


def _docker_ok():
    return {
        "tool": "qsirecon",
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
    @patch("voxelops.runners.qsirecon.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsirecon.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsirecon.os.getgid", return_value=1000)
    def test_default_config(self, _gid, _uid, mock_rd, mock_qsiprep_dir):
        inputs = QSIReconInputs(qsiprep_dir=mock_qsiprep_dir, participant="01")
        result = run_qsirecon(inputs)
        assert result["config"].docker_image == "pennlinc/qsirecon:1.2.0"

    @patch("voxelops.runners.qsirecon.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsirecon.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsirecon.os.getgid", return_value=1000)
    def test_override_nprocs(self, _gid, _uid, mock_rd, mock_qsiprep_dir):
        inputs = QSIReconInputs(qsiprep_dir=mock_qsiprep_dir, participant="01")
        result = run_qsirecon(inputs, nprocs=32)
        assert result["config"].nprocs == 32

    @patch("voxelops.runners.qsirecon.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsirecon.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsirecon.os.getgid", return_value=1000)
    def test_override_unknown_ignored(self, _gid, _uid, mock_rd, mock_qsiprep_dir):
        inputs = QSIReconInputs(qsiprep_dir=mock_qsiprep_dir, participant="01")
        result = run_qsirecon(inputs, bogus=42)
        assert not hasattr(result["config"], "bogus")


# -- Validation ---------------------------------------------------------------


class TestValidation:
    def test_missing_qsiprep_dir(self, tmp_path):
        inputs = QSIReconInputs(qsiprep_dir=tmp_path / "nope", participant="01")
        with pytest.raises(InputValidationError, match="QSIPrep directory not found"):
            run_qsirecon(inputs)

    def test_missing_participant(self, mock_qsiprep_dir):
        inputs = QSIReconInputs(qsiprep_dir=mock_qsiprep_dir, participant="99")
        with pytest.raises(InputValidationError, match="sub-99 not found"):
            run_qsirecon(inputs)


# -- Directory defaults -------------------------------------------------------


class TestDirectoryDefaults:
    @patch("voxelops.runners.qsirecon.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsirecon.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsirecon.os.getgid", return_value=1000)
    def test_default_output_dir(self, _gid, _uid, mock_rd, mock_qsiprep_dir):
        inputs = QSIReconInputs(qsiprep_dir=mock_qsiprep_dir, participant="01")
        result = run_qsirecon(inputs)
        # qsirecon_dir is now the output_dir directly (not output_dir / "qsirecon")
        # default output_dir: qsiprep_dir.parent (typically "derivatives")
        expected = mock_qsiprep_dir.parent
        assert result["expected_outputs"].qsirecon_dir == expected

    @patch("voxelops.runners.qsirecon.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsirecon.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsirecon.os.getgid", return_value=1000)
    def test_default_work_dir(self, _gid, _uid, mock_rd, mock_qsiprep_dir):
        inputs = QSIReconInputs(qsiprep_dir=mock_qsiprep_dir, participant="01")
        result = run_qsirecon(inputs)
        # work_dir default: output_dir.parent / "work" / "qsirecon"
        # output_dir = qsiprep_dir.parent  => derivatives
        # work_dir = derivatives.parent / "work" / "qsirecon"
        expected_work = mock_qsiprep_dir.parent.parent / "work" / "qsirecon"
        assert result["expected_outputs"].work_dir == expected_work


# -- Docker command -----------------------------------------------------------


class TestDockerCommand:
    @patch("voxelops.runners.qsirecon.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsirecon.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsirecon.os.getgid", return_value=1000)
    def test_fs_license_mount(
        self, _gid, _uid, mock_rd, mock_qsiprep_dir, mock_fs_license
    ):
        inputs = QSIReconInputs(qsiprep_dir=mock_qsiprep_dir, participant="01")
        cfg = QSIReconDefaults(fs_license=mock_fs_license)
        run_qsirecon(inputs, config=cfg)
        cmd = mock_rd.call_args.kwargs["cmd"]
        assert "--fs-license-file" in cmd

    @patch("voxelops.runners.qsirecon.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsirecon.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsirecon.os.getgid", return_value=1000)
    def test_fs_subjects_dir_mount(
        self, _gid, _uid, mock_rd, mock_qsiprep_dir, tmp_path
    ):
        fs_dir = tmp_path / "fs_subjects"
        fs_dir.mkdir()
        inputs = QSIReconInputs(qsiprep_dir=mock_qsiprep_dir, participant="01")
        cfg = QSIReconDefaults(fs_subjects_dir=fs_dir)
        run_qsirecon(inputs, config=cfg)
        cmd = mock_rd.call_args.kwargs["cmd"]
        assert "--freesurfer-input" in cmd
        assert "/subjects" in cmd

    @patch("voxelops.runners.qsirecon.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsirecon.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsirecon.os.getgid", return_value=1000)
    def test_datasets_volumes_and_args(
        self, _gid, _uid, mock_rd, mock_qsiprep_dir, tmp_path
    ):
        ds1 = tmp_path / "ds1"
        ds1.mkdir()
        inputs = QSIReconInputs(
            qsiprep_dir=mock_qsiprep_dir,
            participant="01",
            datasets={"freesurfer": ds1},
        )
        run_qsirecon(inputs)
        cmd = mock_rd.call_args.kwargs["cmd"]
        # volume mount
        assert f"{ds1}:/datasets/freesurfer:ro" in " ".join(cmd)
        # arguments
        assert "--datasets" in cmd
        assert "freesurfer=/datasets/freesurfer" in cmd

    @patch("voxelops.runners.qsirecon.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsirecon.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsirecon.os.getgid", return_value=1000)
    def test_config_atlases(self, _gid, _uid, mock_rd, mock_qsiprep_dir):
        # atlases moved to QSIReconInputs
        inputs = QSIReconInputs(
            qsiprep_dir=mock_qsiprep_dir,
            participant="01",
            atlases=["AAL116", "Gordon333Ext"],
        )
        run_qsirecon(inputs)
        cmd = mock_rd.call_args.kwargs["cmd"]
        assert "--atlases" in cmd
        idx = cmd.index("--atlases")
        assert cmd[idx + 1] == "AAL116"
        assert cmd[idx + 2] == "Gordon333Ext"

    @patch("voxelops.runners.qsirecon.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsirecon.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsirecon.os.getgid", return_value=1000)
    def test_inputs_atlases(self, _gid, _uid, mock_rd, mock_qsiprep_dir):
        inputs = QSIReconInputs(
            qsiprep_dir=mock_qsiprep_dir,
            participant="01",
            atlases=["custom_atlas"],
        )
        # atlases are now on inputs, not config
        run_qsirecon(inputs)
        cmd = mock_rd.call_args.kwargs["cmd"]
        assert "custom_atlas" in cmd

    @patch("voxelops.runners.qsirecon.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsirecon.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsirecon.os.getgid", return_value=1000)
    def test_recon_spec_mount(
        self, _gid, _uid, mock_rd, mock_qsiprep_dir, mock_recon_spec
    ):
        inputs = QSIReconInputs(
            qsiprep_dir=mock_qsiprep_dir,
            participant="01",
            recon_spec=mock_recon_spec,
        )
        run_qsirecon(inputs)
        cmd = mock_rd.call_args.kwargs["cmd"]
        assert "--recon-spec" in cmd
        assert "/recon_spec.yaml" in cmd

    @patch("voxelops.runners.qsirecon.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsirecon.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsirecon.os.getgid", return_value=1000)
    def test_recon_spec_volume_always_mounted(
        self, _gid, _uid, mock_rd, mock_qsiprep_dir
    ):
        """Quirk: line 95 unconditionally mounts inputs.recon_spec even when None."""
        inputs = QSIReconInputs(qsiprep_dir=mock_qsiprep_dir, participant="01")
        run_qsirecon(inputs)
        cmd = mock_rd.call_args.kwargs["cmd"]
        # The volume mount is always present (even for None)
        volume_strs = [c for c in cmd if "/recon_spec.yaml:ro" in c]
        assert len(volume_strs) == 1

    @patch("voxelops.runners.qsirecon.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsirecon.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsirecon.os.getgid", return_value=1000)
    def test_result_structure(self, _gid, _uid, mock_rd, mock_qsiprep_dir):
        inputs = QSIReconInputs(qsiprep_dir=mock_qsiprep_dir, participant="01")
        result = run_qsirecon(inputs)
        assert "inputs" in result
        assert "config" in result
        assert "expected_outputs" in result

    @patch("voxelops.runners.qsirecon.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsirecon.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsirecon.os.getgid", return_value=1000)
    def test_no_datasets_no_flag(self, _gid, _uid, mock_rd, mock_qsiprep_dir):
        inputs = QSIReconInputs(qsiprep_dir=mock_qsiprep_dir, participant="01")
        run_qsirecon(inputs)
        cmd = mock_rd.call_args.kwargs["cmd"]
        assert "--datasets" not in cmd

    @patch("voxelops.runners.qsirecon.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.qsirecon.os.getuid", return_value=1000)
    @patch("voxelops.runners.qsirecon.os.getgid", return_value=1000)
    def test_no_atlases_no_flag(self, _gid, _uid, mock_rd, mock_qsiprep_dir):
        # atlases moved to inputs - pass empty list
        inputs = QSIReconInputs(
            qsiprep_dir=mock_qsiprep_dir,
            participant="01",
            atlases=[],
        )
        run_qsirecon(inputs)
        cmd = mock_rd.call_args.kwargs["cmd"]
        assert "--atlases" not in cmd
