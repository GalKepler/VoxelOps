"""Tests for voxelops.runners.qsiparc -- run_qsiparc."""

import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from voxelops.exceptions import InputValidationError, ProcedureExecutionError
from voxelops.schemas.qsiparc import QSIParcInputs, QSIParcDefaults
from voxelops.runners.qsiparc import run_qsiparc


# -- Config -------------------------------------------------------------------


class TestConfig:
    @patch("voxelops.runners.qsiparc.run_parcellations", return_value=[])
    @patch("voxelops.runners.qsiparc.QSIReconConfig")
    def test_default_config(self, mock_cfg_cls, mock_run, mock_qsirecon_dir):
        inputs = QSIParcInputs(qsirecon_dir=mock_qsirecon_dir, participant="01")
        result = run_qsiparc(inputs)
        assert result["config"].mask == "gm"
        assert result["config"].force is False

    @patch("voxelops.runners.qsiparc.run_parcellations", return_value=[])
    @patch("voxelops.runners.qsiparc.QSIReconConfig")
    def test_custom_config(self, mock_cfg_cls, mock_run, mock_qsirecon_dir):
        inputs = QSIParcInputs(qsirecon_dir=mock_qsirecon_dir, participant="01")
        cfg = QSIParcDefaults(mask="wm", force=True)
        result = run_qsiparc(inputs, config=cfg)
        assert result["config"].mask == "wm"
        assert result["config"].force is True

    @patch("voxelops.runners.qsiparc.run_parcellations", return_value=[])
    @patch("voxelops.runners.qsiparc.QSIReconConfig")
    def test_override(self, mock_cfg_cls, mock_run, mock_qsirecon_dir):
        inputs = QSIParcInputs(qsirecon_dir=mock_qsirecon_dir, participant="01")
        result = run_qsiparc(inputs, force=True)
        assert result["config"].force is True

    @patch("voxelops.runners.qsiparc.run_parcellations", return_value=[])
    @patch("voxelops.runners.qsiparc.QSIReconConfig")
    def test_override_unknown_ignored(self, mock_cfg_cls, mock_run, mock_qsirecon_dir):
        inputs = QSIParcInputs(qsirecon_dir=mock_qsirecon_dir, participant="01")
        result = run_qsiparc(inputs, bogus=42)
        assert not hasattr(result["config"], "bogus")


# -- Validation ---------------------------------------------------------------


class TestValidation:
    def test_missing_qsirecon_dir(self, tmp_path):
        inputs = QSIParcInputs(qsirecon_dir=tmp_path / "nope", participant="01")
        with pytest.raises(InputValidationError, match="QSIRecon directory not found"):
            run_qsiparc(inputs)

    def test_missing_participant(self, mock_qsirecon_dir):
        inputs = QSIParcInputs(qsirecon_dir=mock_qsirecon_dir, participant="99")
        with pytest.raises(InputValidationError, match="sub-99 not found"):
            run_qsiparc(inputs)


# -- Parcellate config building -----------------------------------------------


class TestParcellateConfig:
    @patch("voxelops.runners.qsiparc.run_parcellations", return_value=[])
    @patch("voxelops.runners.qsiparc.QSIReconConfig")
    def test_session_passed(self, mock_cfg_cls, mock_run, mock_qsirecon_dir):
        inputs = QSIParcInputs(
            qsirecon_dir=mock_qsirecon_dir, participant="01", session="pre"
        )
        run_qsiparc(inputs)
        call_kw = mock_cfg_cls.call_args
        assert call_kw.kwargs["sessions"] == ["pre"]

    @patch("voxelops.runners.qsiparc.run_parcellations", return_value=[])
    @patch("voxelops.runners.qsiparc.QSIReconConfig")
    def test_no_session(self, mock_cfg_cls, mock_run, mock_qsirecon_dir):
        inputs = QSIParcInputs(qsirecon_dir=mock_qsirecon_dir, participant="01")
        run_qsiparc(inputs)
        call_kw = mock_cfg_cls.call_args
        assert call_kw.kwargs["sessions"] is None

    @patch("voxelops.runners.qsiparc.run_parcellations", return_value=[])
    @patch("voxelops.runners.qsiparc.QSIReconConfig")
    def test_atlases_from_inputs(self, mock_cfg_cls, mock_run, mock_qsirecon_dir):
        from conftest import MockAtlasDefinition

        atlas = MockAtlasDefinition(name="test")
        inputs = QSIParcInputs(
            qsirecon_dir=mock_qsirecon_dir, participant="01", atlases=[atlas]
        )
        run_qsiparc(inputs)
        call_kw = mock_cfg_cls.call_args
        assert call_kw.kwargs["atlases"] == [atlas]

    @patch("voxelops.runners.qsiparc.run_parcellations", return_value=[])
    @patch("voxelops.runners.qsiparc.QSIReconConfig")
    def test_n_jobs_from_inputs(self, mock_cfg_cls, mock_run, mock_qsirecon_dir):
        inputs = QSIParcInputs(
            qsirecon_dir=mock_qsirecon_dir, participant="01", n_jobs=8
        )
        run_qsiparc(inputs)
        call_kw = mock_cfg_cls.call_args
        assert call_kw.kwargs["n_jobs"] == 8

    @patch("voxelops.runners.qsiparc.run_parcellations", return_value=[])
    @patch("voxelops.runners.qsiparc.QSIReconConfig")
    def test_n_procs_from_inputs(self, mock_cfg_cls, mock_run, mock_qsirecon_dir):
        inputs = QSIParcInputs(
            qsirecon_dir=mock_qsirecon_dir, participant="01", n_procs=4
        )
        run_qsiparc(inputs)
        call_kw = mock_cfg_cls.call_args
        assert call_kw.kwargs["n_procs"] == 4

    @patch("voxelops.runners.qsiparc.run_parcellations", return_value=[])
    @patch("voxelops.runners.qsiparc.QSIReconConfig")
    def test_n_jobs_falls_back_to_config(self, mock_cfg_cls, mock_run, mock_qsirecon_dir):
        inputs = QSIParcInputs(qsirecon_dir=mock_qsirecon_dir, participant="01")
        cfg = QSIParcDefaults(n_jobs=5)
        run_qsiparc(inputs, config=cfg)
        call_kw = mock_cfg_cls.call_args
        assert call_kw.kwargs["n_jobs"] == 5


# -- Log level mapping --------------------------------------------------------


class TestLogLevel:
    @patch("voxelops.runners.qsiparc.run_parcellations", return_value=[])
    @patch("voxelops.runners.qsiparc.QSIReconConfig")
    def test_valid_log_level(self, mock_cfg_cls, mock_run, mock_qsirecon_dir):
        inputs = QSIParcInputs(qsirecon_dir=mock_qsirecon_dir, participant="01")
        cfg = QSIParcDefaults(log_level="DEBUG")
        run_qsiparc(inputs, config=cfg)
        call_kw = mock_cfg_cls.call_args
        assert call_kw.kwargs["log_level"] == logging.DEBUG

    @patch("voxelops.runners.qsiparc.run_parcellations", return_value=[])
    @patch("voxelops.runners.qsiparc.QSIReconConfig")
    def test_invalid_log_level_falls_back_to_info(
        self, mock_cfg_cls, mock_run, mock_qsirecon_dir
    ):
        inputs = QSIParcInputs(qsirecon_dir=mock_qsirecon_dir, participant="01")
        cfg = QSIParcDefaults(log_level="BOGUS")
        run_qsiparc(inputs, config=cfg)
        call_kw = mock_cfg_cls.call_args
        assert call_kw.kwargs["log_level"] == logging.INFO


# -- Exception handling -------------------------------------------------------


class TestExceptionHandling:
    @patch("voxelops.runners.qsiparc.QSIReconConfig")
    @patch("voxelops.runners.qsiparc.run_parcellations")
    def test_procedure_execution_error_reraised(
        self, mock_run, mock_cfg_cls, mock_qsirecon_dir
    ):
        mock_run.side_effect = ProcedureExecutionError("qsiparc", "boom")
        inputs = QSIParcInputs(qsirecon_dir=mock_qsirecon_dir, participant="01")
        with pytest.raises(ProcedureExecutionError, match="boom"):
            run_qsiparc(inputs)

    @patch("voxelops.runners.qsiparc.QSIReconConfig")
    @patch("voxelops.runners.qsiparc.run_parcellations")
    def test_generic_exception_wrapped(
        self, mock_run, mock_cfg_cls, mock_qsirecon_dir
    ):
        mock_run.side_effect = RuntimeError("unexpected")
        inputs = QSIParcInputs(qsirecon_dir=mock_qsirecon_dir, participant="01")
        with pytest.raises(ProcedureExecutionError, match="unexpected"):
            run_qsiparc(inputs)

    @patch("voxelops.runners.qsiparc.run_parcellations", return_value=["f1.tsv"])
    @patch("voxelops.runners.qsiparc.QSIReconConfig")
    def test_success_record(self, mock_cfg_cls, mock_run, mock_qsirecon_dir):
        inputs = QSIParcInputs(qsirecon_dir=mock_qsirecon_dir, participant="01")
        result = run_qsiparc(inputs)
        assert result["success"] is True
        assert result["tool"] == "qsiparc"
        assert result["output_files"] == ["f1.tsv"]
        assert "inputs" in result
        assert "config" in result
        assert "expected_outputs" in result
        assert "start_time" in result
        assert "duration_seconds" in result
