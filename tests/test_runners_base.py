"""Tests for voxelops.runners._base -- validate_input_dir, validate_participant, run_docker."""

import json
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from voxelops.exceptions import InputValidationError, ProcedureExecutionError
from voxelops.runners._base import run_docker, validate_input_dir, validate_participant

# -- validate_input_dir -------------------------------------------------------


class TestValidateInputDir:
    def test_exists(self, tmp_path):
        validate_input_dir(tmp_path)  # should not raise

    def test_not_exists(self, tmp_path):
        with pytest.raises(InputValidationError, match="not found"):
            validate_input_dir(tmp_path / "nope")

    def test_is_file_not_dir(self, tmp_path):
        f = tmp_path / "file.txt"
        f.write_text("hi")
        with pytest.raises(InputValidationError, match="not a directory"):
            validate_input_dir(f)

    def test_custom_dir_type(self, tmp_path):
        with pytest.raises(InputValidationError, match="DICOM directory not found"):
            validate_input_dir(tmp_path / "nope", dir_type="DICOM")


# -- validate_participant -----------------------------------------------------


class TestValidateParticipant:
    def test_exists(self, mock_bids_dir):
        validate_participant(mock_bids_dir, "01")  # should not raise

    def test_not_found(self, mock_bids_dir):
        with pytest.raises(InputValidationError, match="sub-99 not found"):
            validate_participant(mock_bids_dir, "99")

    def test_custom_prefix(self, tmp_path):
        (tmp_path / "ses-pre").mkdir()
        validate_participant(tmp_path, "pre", prefix="ses-")


# -- run_docker ---------------------------------------------------------------


class TestRunDocker:
    @patch("voxelops.runners._base.subprocess.run")
    def test_success_with_log_dir(self, mock_subproc, tmp_path):
        mock_subproc.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        log_dir = tmp_path / "logs"

        record = run_docker(
            cmd=["docker", "run", "img"],
            tool_name="test",
            participant="01",
            log_dir=log_dir,
        )

        assert record["success"] is True
        assert record["exit_code"] == 0
        assert record["stdout"] == "ok"
        assert "log_file" in record
        # log JSON written
        log_file = Path(record["log_file"])
        assert log_file.exists()
        saved = json.loads(log_file.read_text())
        assert saved["success"] is True

    @patch("voxelops.runners._base.ensure_docker_image")
    @patch("voxelops.runners._base.subprocess.run")
    def test_success_no_log_dir(self, mock_subproc, _ensure):
        mock_subproc.return_value = MagicMock(returncode=0, stdout="ok", stderr="")
        record = run_docker(
            cmd=["docker", "run", "img"], tool_name="t", participant="01"
        )
        assert record["success"] is True
        assert "log_file" not in record

    @patch("voxelops.runners._base.ensure_docker_image")
    @patch("voxelops.runners._base.subprocess.run")
    def test_capture_output_false(self, mock_subproc, _ensure):
        mock_subproc.return_value = MagicMock(returncode=0)
        record = run_docker(
            cmd=["docker", "run", "img"],
            tool_name="t",
            participant="01",
            capture_output=False,
        )
        assert record["success"] is True
        assert "stdout" not in record
        assert "stderr" not in record

    @patch("voxelops.runners._base.ensure_docker_image")
    @patch("voxelops.runners._base.subprocess.run")
    def test_failure_with_stderr(self, mock_subproc, _ensure, tmp_path):
        mock_subproc.return_value = MagicMock(
            returncode=1, stdout="", stderr="segfault"
        )
        log_dir = tmp_path / "logs"
        with pytest.raises(ProcedureExecutionError, match="failed"):
            run_docker(
                cmd=["docker", "run", "img"],
                tool_name="qsiprep",
                participant="01",
                log_dir=log_dir,
            )
        # log file should still be written with error
        log_files = list(log_dir.glob("*.json"))
        assert len(log_files) == 1
        saved = json.loads(log_files[0].read_text())
        assert saved["success"] is False
        assert "error" in saved

    @patch("voxelops.runners._base.ensure_docker_image")
    @patch("voxelops.runners._base.subprocess.run")
    def test_failure_no_stderr(self, mock_subproc, _ensure):
        mock_subproc.return_value = MagicMock(returncode=1, stdout="", stderr="")
        with pytest.raises(ProcedureExecutionError):
            run_docker(
                cmd=["docker", "run", "img"],
                tool_name="t",
                participant="01",
            )

    @patch("voxelops.runners._base.ensure_docker_image")
    @patch("voxelops.runners._base.subprocess.run")
    def test_failure_no_log_file(self, mock_subproc, _ensure):
        mock_subproc.return_value = MagicMock(returncode=2, stdout="", stderr="err")
        with pytest.raises(ProcedureExecutionError):
            run_docker(
                cmd=["docker", "run", "img"],
                tool_name="t",
                participant="01",
            )

    @patch("voxelops.runners._base.ensure_docker_image")
    @patch("voxelops.runners._base.subprocess.run")
    def test_timeout_exception(self, mock_subproc, _ensure):
        mock_subproc.side_effect = subprocess.TimeoutExpired(cmd=["docker"], timeout=60)
        with pytest.raises(ProcedureExecutionError, match="timed out"):
            run_docker(
                cmd=["docker", "run", "img"],
                tool_name="t",
                participant="01",
            )

    @patch("voxelops.runners._base.ensure_docker_image")
    @patch("voxelops.runners._base.subprocess.run")
    def test_generic_exception(self, mock_subproc, _ensure):
        mock_subproc.side_effect = OSError("no docker")
        with pytest.raises(ProcedureExecutionError, match="no docker"):
            run_docker(
                cmd=["docker", "run", "img"],
                tool_name="t",
                participant="01",
            )

    @patch("voxelops.runners._base.ensure_docker_image")
    @patch("voxelops.runners._base.subprocess.run")
    def test_procedure_execution_error_reraised(self, mock_subproc, _ensure):
        mock_subproc.side_effect = ProcedureExecutionError("t", "boom")
        with pytest.raises(ProcedureExecutionError, match="boom"):
            run_docker(
                cmd=["docker", "run", "img"],
                tool_name="t",
                participant="01",
            )
