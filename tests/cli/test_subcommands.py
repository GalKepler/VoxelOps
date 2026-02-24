"""Integration-style tests for each CLI subcommand.

Each test calls the subcommand's ``run()`` function directly with a
pre-built ``argparse.Namespace``, patching ``run_procedure`` so no real
Docker process is spawned.
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from voxelops.procedures.result import ProcedureResult


def _ok_result(**kwargs) -> ProcedureResult:
    """Return a successful ProcedureResult."""
    return ProcedureResult(
        procedure="test",
        participant="SUBJ01",
        session=None,
        run_id="test-run-id",
        status="success",
        start_time=datetime.now(),
    )


def _fail_result(**kwargs) -> ProcedureResult:
    return ProcedureResult(
        procedure="test",
        participant="SUBJ01",
        session=None,
        run_id="test-run-id",
        status="execution_failed",
        start_time=datetime.now(),
    )


# ---------------------------------------------------------------------------
# qsiprep
# ---------------------------------------------------------------------------


class TestQsiprepSubcommand:
    def _args(self, tmp_path: Path, **overrides) -> argparse.Namespace:
        defaults = {
            "bids_dir": tmp_path,
            "participants": ["SUBJ01"],
            "csv": None,
            "output_dir": tmp_path / "out",
            "work_dir": None,
            "bids_filters": None,
            "fs_license": None,
            "output_resolution": 1.6,
            "nprocs": 4,
            "mem_mb": 8000,
            "skip_bids_validation": False,
            "docker_image": "pennlinc/qsiprep:1.1.1",
            "workers": 1,
            "log_dir": None,
            "log_level": "WARNING",
            "force": False,
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_success_returns_zero(self, tmp_path):
        from voxelops.cli import qsiprep

        args = self._args(tmp_path)
        with patch("voxelops.cli.qsiprep.run_procedure", return_value=_ok_result()):
            code = qsiprep.run(args)
        assert code == 0

    def test_failure_returns_nonzero(self, tmp_path):
        from voxelops.cli import qsiprep

        args = self._args(tmp_path)
        with patch("voxelops.cli.qsiprep.run_procedure", return_value=_fail_result()):
            code = qsiprep.run(args)
        assert code != 0

    def test_csv_loads_participants(self, tmp_path):
        from voxelops.cli import qsiprep

        csv_path = tmp_path / "sessions.csv"
        csv_path.write_text("SubjectCode,ScanID\n0001,000000000001\n")
        # Create a fake sub-0001 qsiprep output so it's not skipped
        (tmp_path / "out" / "qsiprep" / "sub-0001").mkdir(parents=True)

        args = self._args(tmp_path, participants=None, csv=csv_path, force=True)
        calls = []

        def fake_run(**kwargs):
            calls.append(kwargs)
            return _ok_result()

        with patch("voxelops.cli.qsiprep.run_procedure", side_effect=fake_run):
            qsiprep.run(args)

        assert len(calls) == 1


# ---------------------------------------------------------------------------
# qsirecon
# ---------------------------------------------------------------------------


class TestQsireconSubcommand:
    def _args(self, tmp_path: Path, **overrides) -> argparse.Namespace:
        defaults = {
            "qsiprep_dir": tmp_path / "qsiprep",
            "participants": ["SUBJ01"],
            "csv": None,
            "session": None,
            "output_dir": tmp_path / "out",
            "work_dir": None,
            "recon_spec": None,
            "recon_spec_aux_files": None,
            "datasets": None,
            "atlases": None,
            "fs_license": None,
            "fs_subjects_dir": None,
            "nprocs": 4,
            "mem_mb": 8000,
            "docker_image": "pennlinc/qsirecon:1.2.0",
            "workers": 1,
            "log_dir": None,
            "log_level": "WARNING",
            "force": False,
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_success_returns_zero(self, tmp_path):
        from voxelops.cli import qsirecon

        (tmp_path / "qsiprep" / "sub-SUBJ01").mkdir(parents=True)
        args = self._args(tmp_path)
        with patch("voxelops.cli.qsirecon.run_procedure", return_value=_ok_result()):
            code = qsirecon.run(args)
        assert code == 0

    def test_datasets_parsed_as_dict(self, tmp_path):
        from voxelops.cli import qsirecon

        (tmp_path / "qsiprep" / "sub-SUBJ01").mkdir(parents=True)
        args = self._args(tmp_path, datasets=["atlases=/data/atlases"])
        captured = []

        def fake_run(procedure, inputs, config, log_dir):
            captured.append(inputs)
            return _ok_result()

        with patch("voxelops.cli.qsirecon.run_procedure", side_effect=fake_run):
            qsirecon.run(args)

        assert len(captured) == 1
        assert captured[0].datasets == {"atlases": Path("/data/atlases")}


# ---------------------------------------------------------------------------
# freesurfer
# ---------------------------------------------------------------------------


class TestFreesurferSubcommand:
    def _args(self, tmp_path: Path, **overrides) -> argparse.Namespace:
        fs_lic = tmp_path / "license.txt"
        fs_lic.touch()
        defaults = {
            "bids_dir": tmp_path / "bids",
            "participants": ["SUBJ01"],
            "csv": None,
            "output_dir": tmp_path / "out",
            "work_dir": None,
            "fs_license": fs_lic,
            "t1w_filters": None,
            "t2w_filters": None,
            "no_t2w": False,
            "flair_filters": None,
            "nthreads": 4,
            "hires": False,
            "docker_image": "freesurfer/freesurfer:8.1.0",
            "workers": 1,
            "log_dir": None,
            "log_level": "WARNING",
            "force": False,
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_success_returns_zero(self, tmp_path):
        from voxelops.cli import freesurfer

        args = self._args(tmp_path)
        with patch("voxelops.cli.freesurfer.run_procedure", return_value=_ok_result()):
            code = freesurfer.run(args)
        assert code == 0

    def test_no_t2w_disables_t2w(self, tmp_path):
        from voxelops.cli import freesurfer

        args = self._args(tmp_path, no_t2w=True)
        captured = []

        def fake_run(procedure, inputs, config, log_dir):
            captured.append(inputs)
            return _ok_result()

        with patch("voxelops.cli.freesurfer.run_procedure", side_effect=fake_run):
            freesurfer.run(args)

        assert captured[0].t2w_filters is None

    def test_t2w_enabled_by_default(self, tmp_path):
        from voxelops.cli import freesurfer

        args = self._args(tmp_path)
        captured = []

        def fake_run(procedure, inputs, config, log_dir):
            captured.append(inputs)
            return _ok_result()

        with patch("voxelops.cli.freesurfer.run_procedure", side_effect=fake_run):
            freesurfer.run(args)

        # Default: t2w_filters is an empty dict (auto-detect any T2w)
        assert captured[0].t2w_filters == {}


# ---------------------------------------------------------------------------
# heudiconv
# ---------------------------------------------------------------------------


class TestHeudiconvSubcommand:
    def _args(self, tmp_path: Path, csv_path: Path, **overrides) -> argparse.Namespace:
        heuristic = tmp_path / "heuristic.py"
        heuristic.touch()
        defaults = {
            "csv": csv_path,
            "output_dir": tmp_path / "bids",
            "heuristic": heuristic,
            "overwrite": False,
            "docker_image": "nipy/heudiconv:1.3.4",
            "workers": 1,
            "log_dir": None,
            "log_level": "WARNING",
            "force": False,
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_success_returns_zero(self, tmp_path):
        from voxelops.cli import heudiconv

        csv_path = tmp_path / "sessions.csv"
        csv_path.write_text(
            "SubjectCode,ScanID,dicom_path\n0001,000000000001,/data/dicoms\n"
        )
        args = self._args(tmp_path, csv_path)
        with patch("voxelops.cli.heudiconv.run_procedure", return_value=_ok_result()):
            code = heudiconv.run(args)
        assert code == 0

    def test_iterates_csv_rows(self, tmp_path):
        from voxelops.cli import heudiconv

        csv_path = tmp_path / "sessions.csv"
        csv_path.write_text(
            "SubjectCode,ScanID,dicom_path\n"
            "0001,000000000001,/data/d1\n"
            "0002,000000000002,/data/d2\n"
        )
        args = self._args(tmp_path, csv_path)
        calls = []

        def fake_run(procedure, inputs, config, log_dir):
            calls.append(inputs)
            return _ok_result()

        with patch("voxelops.cli.heudiconv.run_procedure", side_effect=fake_run):
            heudiconv.run(args)

        assert len(calls) == 2


# ---------------------------------------------------------------------------
# qsiparc
# ---------------------------------------------------------------------------


class TestQsiparcSubcommand:
    def _args(self, tmp_path: Path, **overrides) -> argparse.Namespace:
        defaults = {
            "qsirecon_dir": tmp_path / "qsirecon",
            "participants": ["SUBJ01"],
            "csv": None,
            "session": None,
            "output_dir": tmp_path / "out",
            "atlases": None,
            "mask": "gm",
            "resampling_target": "data",
            "n_jobs": 1,
            "n_procs": 1,
            "workers": 1,
            "log_dir": None,
            "log_level": "WARNING",
            "force": False,
        }
        defaults.update(overrides)
        return argparse.Namespace(**defaults)

    def test_success_returns_zero(self, tmp_path):
        from voxelops.cli import qsiparc

        (tmp_path / "qsirecon" / "sub-SUBJ01").mkdir(parents=True)
        args = self._args(tmp_path)
        with patch("voxelops.cli.qsiparc.run_procedure", return_value=_ok_result()):
            code = qsiparc.run(args)
        assert code == 0

    def test_skips_missing_qsirecon_dir(self, tmp_path):
        from voxelops.cli import qsiparc

        # No sub-SUBJ01 directory — participant should be skipped
        (tmp_path / "qsirecon").mkdir(parents=True)
        csv_path = tmp_path / "sessions.csv"
        csv_path.write_text("SubjectCode,ScanID\nSUBJ01,000000000001\n")
        args = self._args(tmp_path, participants=None, csv=csv_path, force=False)
        calls = []

        def fake_run(**kwargs):
            calls.append(kwargs)
            return _ok_result()

        with patch("voxelops.cli.qsiparc.run_procedure", side_effect=fake_run):
            qsiparc.run(args)

        assert len(calls) == 0
