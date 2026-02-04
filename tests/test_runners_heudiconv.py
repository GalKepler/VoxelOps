"""Tests for voxelops.runners.heudiconv -- run_heudiconv."""

from unittest.mock import patch

import pytest
from voxelops.exceptions import InputValidationError
from voxelops.runners.heudiconv import (
    _build_heudiconv_docker_command,
    _handle_heudiconv_post_processing,
    run_heudiconv,
)
from voxelops.schemas.heudiconv import (
    HeudiconvDefaults,
    HeudiconvInputs,
)


def _make_inputs(tmp_path, *, session=None, output_dir=None):
    dicom_dir = tmp_path / "dicoms"
    dicom_dir.mkdir(exist_ok=True)
    heuristic = tmp_path / "heuristic.py"
    heuristic.write_text("# stub\n")
    return (
        HeudiconvInputs(
            dicom_dir=dicom_dir,
            participant="01",
            session=session,
            output_dir=output_dir,
        ),
        heuristic,
    )


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
        inputs = HeudiconvInputs(dicom_dir=tmp_path / "nope", participant="01")
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
        # Overwrite flag should appear exactly once
        assert cmd.count("--overwrite") == 1

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
        run_heudiconv(inputs, heuristic=heuristic, bids_validator=False, bids=None)
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


# -- Helper Functions --------------------------------------------------------


class TestHeudiconvHelpers:
    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_build_heudiconv_docker_command_basic(self, mock_gid, mock_uid, tmp_path):
        inputs, heuristic = _make_inputs(tmp_path)
        config = HeudiconvDefaults(heuristic=heuristic)
        output_dir = tmp_path / "bids"
        output_dir.mkdir()

        cmd = _build_heudiconv_docker_command(inputs, config, output_dir)

        expected_cmd_start = [
            "docker",
            "run",
            "--rm",
            "--user",
            "1000:1000",
            "-v",
            f"{inputs.dicom_dir}:/dicom:ro",
            "-v",
            f"{output_dir}:/output",
            "-v",
            f"{config.heuristic}:/heuristic.py:ro",
            config.docker_image,
            "--files",
            "/dicom",
            "--outdir",
            "/output",
            "--subjects",
            inputs.participant,
            "--converter",
            config.converter,
            "--heuristic",
            "/heuristic.py",
        ]
        assert cmd[: len(expected_cmd_start)] == expected_cmd_start
        assert "--ses" not in cmd
        assert "--overwrite" not in cmd  # default false
        assert "--bids" in cmd  # default true
        assert "--grouping" in cmd  # default true

    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_build_heudiconv_docker_command_with_session(
        self, mock_gid, mock_uid, tmp_path
    ):
        inputs, heuristic = _make_inputs(tmp_path, session="pre")
        config = HeudiconvDefaults(heuristic=heuristic)
        output_dir = tmp_path / "bids"
        output_dir.mkdir()

        cmd = _build_heudiconv_docker_command(inputs, config, output_dir)
        assert "--ses" in cmd
        assert "pre" in cmd

    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_build_heudiconv_docker_command_with_overwrite_true(
        self, mock_gid, mock_uid, tmp_path
    ):
        inputs, heuristic = _make_inputs(tmp_path)
        config = HeudiconvDefaults(heuristic=heuristic, overwrite=True)
        output_dir = tmp_path / "bids"
        output_dir.mkdir()

        cmd = _build_heudiconv_docker_command(inputs, config, output_dir)
        assert "--overwrite" in cmd
        # Ensure it only appears once
        assert cmd.count("--overwrite") == 1

    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_build_heudiconv_docker_command_with_overwrite_false(
        self, mock_gid, mock_uid, tmp_path
    ):
        inputs, heuristic = _make_inputs(tmp_path)
        config = HeudiconvDefaults(heuristic=heuristic, overwrite=False)
        output_dir = tmp_path / "bids"
        output_dir.mkdir()

        cmd = _build_heudiconv_docker_command(inputs, config, output_dir)
        assert "--overwrite" not in cmd

    @patch("voxelops.runners.heudiconv.os.getuid", return_value=1000)
    @patch("voxelops.runners.heudiconv.os.getgid", return_value=1000)
    def test_build_heudiconv_docker_command_bids_validator_false(
        self, mock_gid, mock_uid, tmp_path
    ):
        inputs, heuristic = _make_inputs(tmp_path)
        config = HeudiconvDefaults(heuristic=heuristic, bids_validator=False, bids=None)
        output_dir = tmp_path / "bids"
        output_dir.mkdir()

        cmd = _build_heudiconv_docker_command(inputs, config, output_dir)
        assert "--bids" not in cmd

    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    def test_handle_heudiconv_post_processing_success(
        self, mock_post_process, tmp_path
    ):
        mock_post_process.return_value = {"success": True}
        inputs, heuristic = _make_inputs(tmp_path)
        config = HeudiconvDefaults(heuristic=heuristic, post_process=True)
        output_dir = tmp_path / "bids"
        output_dir.mkdir()
        result = {"success": True}

        updated_result = _handle_heudiconv_post_processing(
            result, config, output_dir, inputs
        )

        mock_post_process.assert_called_once_with(
            bids_dir=output_dir,
            participant=inputs.participant,
            session=inputs.session,
            dry_run=config.post_process_dry_run,
        )
        assert updated_result["post_processing"]["success"] is True

    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    def test_handle_heudiconv_post_processing_warnings(
        self, mock_post_process, tmp_path
    ):
        mock_post_process.return_value = {"success": False, "errors": ["warn1"]}
        inputs, heuristic = _make_inputs(tmp_path)
        config = HeudiconvDefaults(heuristic=heuristic, post_process=True)
        output_dir = tmp_path / "bids"
        output_dir.mkdir()
        result = {"success": True}

        updated_result = _handle_heudiconv_post_processing(
            result, config, output_dir, inputs
        )
        assert updated_result["post_processing"]["success"] is False
        assert "warn1" in updated_result["post_processing"]["errors"]

    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    def test_handle_heudiconv_post_processing_exception(
        self, mock_post_process, tmp_path
    ):
        mock_post_process.side_effect = RuntimeError("post-process boom")
        inputs, heuristic = _make_inputs(tmp_path)
        config = HeudiconvDefaults(heuristic=heuristic, post_process=True)
        output_dir = tmp_path / "bids"
        output_dir.mkdir()
        result = {"success": True}

        updated_result = _handle_heudiconv_post_processing(
            result, config, output_dir, inputs
        )
        assert updated_result["post_processing"]["success"] is False
        assert "post-process boom" in updated_result["post_processing"]["error"]

    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    def test_handle_heudiconv_post_processing_disabled(
        self, mock_post_process, tmp_path
    ):
        inputs, heuristic = _make_inputs(tmp_path)
        config = HeudiconvDefaults(heuristic=heuristic, post_process=False)
        output_dir = tmp_path / "bids"
        output_dir.mkdir()
        result = {"success": True}

        updated_result = _handle_heudiconv_post_processing(
            result, config, output_dir, inputs
        )
        mock_post_process.assert_not_called()
        assert "post_processing" not in updated_result

    @patch("voxelops.runners.heudiconv.post_process_heudiconv_output")
    def test_handle_heudiconv_post_processing_skipped_on_run_docker_failure(
        self, mock_post_process, tmp_path
    ):
        inputs, heuristic = _make_inputs(tmp_path)
        config = HeudiconvDefaults(heuristic=heuristic, post_process=True)
        output_dir = tmp_path / "bids"
        output_dir.mkdir()
        result = {"success": False}  # Simulate run_docker failure

        updated_result = _handle_heudiconv_post_processing(
            result, config, output_dir, inputs
        )
        mock_post_process.assert_not_called()
        assert "post_processing" not in updated_result
