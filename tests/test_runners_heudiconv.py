"""Tests for voxelops.runners.heudiconv -- run_heudiconv."""

from unittest.mock import patch

import pytest

from voxelops.exceptions import InputValidationError
from voxelops.runners.heudiconv import run_heudiconv
from voxelops.schemas.heudiconv import (
    HeudiconvDefaults,
    HeudiconvInputs,
)


def _make_inputs(tmp_path, *, session=None, output_dir=None):
    dicom_dir = tmp_path / "dicoms"
    dicom_dir.mkdir(exist_ok=True)
    heuristic = tmp_path / "heuristic.py"
    heuristic.write_text("# stub\n")
    return HeudiconvInputs(
        dicom_dir=dicom_dir,
        participant="01",
        session=session,
        output_dir=output_dir,
    ), heuristic


def _docker_ok():
    return {
        "tool": "heudiconv",
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
    @patch("voxelops.runners.heudiconv.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_default_config(self, _gid, _uid, _pp, mock_rd, tmp_path):
        inputs, heuristic = _make_inputs(tmp_path)
        result = run_heudiconv(inputs, heuristic=heuristic)
        assert result["config"].docker_image == "nipy/heudiconv:1.3.4"

    @patch("voxelops.runners.heudiconv.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_custom_config(self, _gid, _uid, _pp, mock_rd, tmp_path):
        inputs, heuristic = _make_inputs(tmp_path)
        cfg = HeudiconvDefaults(heuristic=heuristic, overwrite=True)
        result = run_heudiconv(inputs, config=cfg)
        assert result["config"].overwrite is True

    @patch("voxelops.runners.heudiconv.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_override_known_key(self, _gid, _uid, _pp, mock_rd, tmp_path):
        inputs, heuristic = _make_inputs(tmp_path)
        result = run_heudiconv(inputs, heuristic=heuristic, overwrite=True)
        assert result["config"].overwrite is True

    @patch("voxelops.runners.heudiconv.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_override_unknown_key_ignored(self, _gid, _uid, _pp, mock_rd, tmp_path):
        inputs, heuristic = _make_inputs(tmp_path)
        result = run_heudiconv(inputs, heuristic=heuristic, bogus_key=42)
        assert not hasattr(result["config"], "bogus_key")


# -- Validation ---------------------------------------------------------------


class TestValidation:
    def test_missing_dicom_dir(self, tmp_path):
        inputs = HeudiconvInputs(
            dicom_dir=tmp_path / "nope", participant="01"
        )
        with pytest.raises(InputValidationError, match="DICOM directory not found"):
            run_heudiconv(inputs, heuristic=tmp_path / "h.py")

    def test_missing_heuristic(self, tmp_path):
        dicom_dir = tmp_path / "dicoms"
        dicom_dir.mkdir()
        inputs = HeudiconvInputs(dicom_dir=dicom_dir, participant="01")
        with pytest.raises(InputValidationError, match="Heuristic file is required"):
            run_heudiconv(inputs)

    def test_heuristic_file_not_found(self, tmp_path):
        dicom_dir = tmp_path / "dicoms"
        dicom_dir.mkdir()
        inputs = HeudiconvInputs(dicom_dir=dicom_dir, participant="01")
        cfg = HeudiconvDefaults(heuristic=tmp_path / "missing.py")
        with pytest.raises(InputValidationError, match="Heuristic file not found"):
            run_heudiconv(inputs, config=cfg)


# -- Output dir ---------------------------------------------------------------


class TestOutputDir:
    @patch("voxelops.runners.heudiconv.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_default_output_dir(self, _gid, _uid, _pp, mock_rd, tmp_path):
        inputs, heuristic = _make_inputs(tmp_path)
        result = run_heudiconv(inputs, heuristic=heuristic)
        # default: dicom_dir.parent / "bids"
        assert result["expected_outputs"].bids_dir == tmp_path / "bids"

    @patch("voxelops.runners.heudiconv.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_custom_output_dir(self, _gid, _uid, _pp, mock_rd, tmp_path):
        custom = tmp_path / "custom_out"
        inputs, heuristic = _make_inputs(tmp_path, output_dir=custom)
        result = run_heudiconv(inputs, heuristic=heuristic)
        assert result["expected_outputs"].bids_dir == custom


# -- Docker command flags -----------------------------------------------------


class TestDockerCommandFlags:
    @patch("voxelops.runners.heudiconv.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_session_flag(self, _gid, _uid, _pp, mock_rd, tmp_path):
        inputs, heuristic = _make_inputs(tmp_path, session="pre")
        run_heudiconv(inputs, heuristic=heuristic)
        cmd = mock_rd.call_args.kwargs["cmd"]
        assert "--ses" in cmd
        idx = cmd.index("--ses")
        assert cmd[idx + 1] == "pre"

    @patch("voxelops.runners.heudiconv.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_overwrite_flag(self, _gid, _uid, _pp, mock_rd, tmp_path):
        inputs, heuristic = _make_inputs(tmp_path)
        run_heudiconv(inputs, heuristic=heuristic, overwrite=True)
        cmd = mock_rd.call_args.kwargs["cmd"]
        # Note: overwrite appears twice (lines 118-119 and 130-131)
        assert cmd.count("--overwrite") == 2

    @patch("voxelops.runners.heudiconv.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_bids_validator_flag(self, _gid, _uid, _pp, mock_rd, tmp_path):
        inputs, heuristic = _make_inputs(tmp_path)
        run_heudiconv(inputs, heuristic=heuristic)  # bids_validator=True by default
        cmd = mock_rd.call_args.kwargs["cmd"]
        # bids_validator adds --bids, and config.bids="notop" also adds --bids notop
        assert "--bids" in cmd

    @patch("voxelops.runners.heudiconv.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_grouping_flag(self, _gid, _uid, _pp, mock_rd, tmp_path):
        inputs, heuristic = _make_inputs(tmp_path)
        run_heudiconv(inputs, heuristic=heuristic)
        cmd = mock_rd.call_args.kwargs["cmd"]
        assert "--grouping" in cmd
        idx = cmd.index("--grouping")
        assert cmd[idx + 1] == "all"

    @patch("voxelops.runners.heudiconv.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_no_session_flag(self, _gid, _uid, _pp, mock_rd, tmp_path):
        inputs, heuristic = _make_inputs(tmp_path)
        run_heudiconv(inputs, heuristic=heuristic)
        cmd = mock_rd.call_args.kwargs["cmd"]
        assert "--ses" not in cmd

    @patch("voxelops.runners.heudiconv.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_no_overwrite_flag(self, _gid, _uid, _pp, mock_rd, tmp_path):
        inputs, heuristic = _make_inputs(tmp_path)
        run_heudiconv(inputs, heuristic=heuristic, overwrite=False)
        cmd = mock_rd.call_args.kwargs["cmd"]
        assert "--overwrite" not in cmd

    @patch("voxelops.runners.heudiconv.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_bids_validator_false(self, _gid, _uid, _pp, mock_rd, tmp_path):
        inputs, heuristic = _make_inputs(tmp_path)
        run_heudiconv(
            inputs, heuristic=heuristic, bids_validator=False, bids=None
        )
        cmd = mock_rd.call_args.kwargs["cmd"]
        assert "--bids" not in cmd


# -- Post-processing ---------------------------------------------------------


class TestPostProcessing:
    @patch("voxelops.runners.heudiconv.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_post_process_success(self, _gid, _uid, mock_pp, mock_rd, tmp_path):
        mock_pp.return_value = {"success": True}
        inputs, heuristic = _make_inputs(tmp_path)
        result = run_heudiconv(inputs, heuristic=heuristic)
        assert result["post_processing"]["success"] is True
        mock_pp.assert_called_once()

    @patch("voxelops.runners.heudiconv.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_post_process_warnings(self, _gid, _uid, mock_pp, mock_rd, tmp_path):
        mock_pp.return_value = {"success": False, "errors": ["warn1"]}
        inputs, heuristic = _make_inputs(tmp_path)
        result = run_heudiconv(inputs, heuristic=heuristic)
        assert result["post_processing"]["success"] is False

    @patch("voxelops.runners.heudiconv.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_post_process_exception(self, _gid, _uid, mock_pp, mock_rd, tmp_path):
        mock_pp.side_effect = RuntimeError("post-process boom")
        inputs, heuristic = _make_inputs(tmp_path)
        result = run_heudiconv(inputs, heuristic=heuristic)
        assert result["post_processing"]["success"] is False
        assert "post-process boom" in result["post_processing"]["error"]

    @patch("voxelops.runners.heudiconv.run_docker", return_value=_docker_ok())
    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_post_process_disabled(self, _gid, _uid, mock_pp, mock_rd, tmp_path):
        inputs, heuristic = _make_inputs(tmp_path)
        result = run_heudiconv(inputs, heuristic=heuristic, post_process=False)
        mock_pp.assert_not_called()
        assert "post_processing" not in result

    @patch("voxelops.runners.heudiconv.run_docker")
    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_post_process_skipped_on_failure(
        self, _gid, _uid, mock_pp, mock_rd, tmp_path
    ):
        failed = _docker_ok()
        failed["success"] = False
        mock_rd.return_value = failed
        inputs, heuristic = _make_inputs(tmp_path)
        _ = run_heudiconv(inputs, heuristic=heuristic)
        mock_pp.assert_not_called()
