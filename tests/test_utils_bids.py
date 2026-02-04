"""Tests for voxelops.utils.bids -- BIDS post-processing utilities."""

import json
import stat
from pathlib import Path
from unittest.mock import Mock, patch

from voxelops.utils.bids import (
    _build_intended_for_path,
    _find_dwi_targets,
    _find_func_targets,
    _process_single_fmap_json,
    _read_json_sidecar,
    _run_post_processing_step,
    _update_json_sidecar,
    add_intended_for_to_fmaps,
    post_process_heudiconv_output,
    remove_bval_bvec_from_fmaps,
    verify_fmap_epi_files,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_participant(tmp_path, participant="01", session=None):
    """Build a minimal BIDS participant directory tree."""
    bids_dir = tmp_path / "bids"
    bids_dir.mkdir(exist_ok=True)
    p = bids_dir / f"sub-{participant}"
    p.mkdir(exist_ok=True)
    if session:
        p = p / f"ses-{session}"
        p.mkdir(exist_ok=True)
    return bids_dir, p


def _add_fmap(
    participant_dir, acq="dwi", *, nii=True, json_file=True, bvec=True, bval=True
):
    """Add fieldmap files to participant_dir/fmap."""
    fmap = participant_dir / "fmap"
    fmap.mkdir(exist_ok=True)
    base = f"sub-01_acq-{acq}_epi"
    if nii:
        (fmap / f"{base}.nii.gz").write_bytes(b"")
    if json_file:
        (fmap / f"{base}.json").write_text(json.dumps({"EchoTime": 0.05}))
    if bvec:
        (fmap / f"{base}.bvec").write_text("0 0 0\n")
    if bval:
        (fmap / f"{base}.bval").write_text("0\n")
    return fmap


def _add_dwi(participant_dir):
    dwi = participant_dir / "dwi"
    dwi.mkdir(exist_ok=True)
    f = dwi / "sub-01_dwi.nii.gz"
    f.write_bytes(b"")
    return f


def _add_func(participant_dir):
    func = participant_dir / "func"
    func.mkdir(exist_ok=True)
    f = func / "sub-01_bold.nii.gz"
    f.write_bytes(b"")
    return f


# ---------------------------------------------------------------------------
# post_process_heudiconv_output
# ---------------------------------------------------------------------------


class TestPostProcessHeudiconvOutput:
    def test_no_session(self, tmp_path):
        bids, pdir = _make_participant(tmp_path)
        _add_fmap(pdir)
        _add_dwi(pdir)
        result = post_process_heudiconv_output(bids, "01")
        assert "verification" in result
        assert "intended_for" in result
        assert "cleanup" in result

    def test_with_session(self, tmp_path):
        bids, pdir = _make_participant(tmp_path, session="pre")
        _add_fmap(pdir)
        _add_dwi(pdir)
        result = post_process_heudiconv_output(bids, "01", session="pre")
        assert "verification" in result

    def test_missing_participant_dir(self, tmp_path):
        bids = tmp_path / "bids"
        bids.mkdir()
        result = post_process_heudiconv_output(bids, "99")
        assert result["success"] is False
        assert any("not found" in e for e in result["errors"])

    def test_exception_in_verification(self, tmp_path):
        bids, pdir = _make_participant(tmp_path)
        with patch(
            "voxelops.utils.bids.verify_fmap_epi_files",
            side_effect=RuntimeError("verify boom"),
        ):
            result = post_process_heudiconv_output(bids, "01")
        assert result["success"] is False
        assert any("Verification failed" in e for e in result["errors"])

    def test_exception_in_intended_for(self, tmp_path):
        bids, pdir = _make_participant(tmp_path)
        with patch(
            "voxelops.utils.bids.add_intended_for_to_fmaps",
            side_effect=RuntimeError("intended boom"),
        ):
            result = post_process_heudiconv_output(bids, "01")
        assert result["success"] is False
        print(result["errors"])
        assert any("Intended" in e for e in result["errors"])

    def test_exception_in_cleanup(self, tmp_path):
        bids, pdir = _make_participant(tmp_path)
        with patch(
            "voxelops.utils.bids.remove_bval_bvec_from_fmaps",
            side_effect=RuntimeError("cleanup boom"),
        ):
            result = post_process_heudiconv_output(bids, "01")
        assert result["success"] is False
        assert any("Cleanup failed" in e for e in result["errors"])

    def test_verification_errors_propagated(self, tmp_path):
        bids, pdir = _make_participant(tmp_path)
        with patch(
            "voxelops.utils.bids.verify_fmap_epi_files",
            return_value={"success": False, "errors": ["no fmap"]},
        ):
            result = post_process_heudiconv_output(bids, "01")
        assert "no fmap" in result["errors"]

    def test_intended_for_errors_propagated(self, tmp_path):
        bids, pdir = _make_participant(tmp_path)
        with patch(
            "voxelops.utils.bids.add_intended_for_to_fmaps",
            return_value={"success": False, "errors": ["json err"]},
        ):
            result = post_process_heudiconv_output(bids, "01")
        assert "json err" in result["errors"]

    def test_cleanup_errors_propagated(self, tmp_path):
        bids, pdir = _make_participant(tmp_path)
        with patch(
            "voxelops.utils.bids.remove_bval_bvec_from_fmaps",
            return_value={"success": False, "errors": ["rename err"]},
        ):
            result = post_process_heudiconv_output(bids, "01")
        assert "rename err" in result["errors"]


# ---------------------------------------------------------------------------
# verify_fmap_epi_files
# ---------------------------------------------------------------------------


class TestVerifyFmapEpiFiles:
    def test_no_fmap_dir(self, tmp_path):
        result = verify_fmap_epi_files(tmp_path)
        assert result["success"] is False
        assert any("not found" in e for e in result["errors"])

    def test_both_found(self, tmp_path):
        _add_fmap(tmp_path)
        result = verify_fmap_epi_files(tmp_path)
        assert result["success"] is True
        assert len(result["found_files"]) == 2

    def test_nii_missing(self, tmp_path):
        _add_fmap(tmp_path, nii=False)
        result = verify_fmap_epi_files(tmp_path)
        assert result["success"] is False
        assert any("NIfTI" in e for e in result["errors"])

    def test_json_missing(self, tmp_path):
        _add_fmap(tmp_path, json_file=False)
        result = verify_fmap_epi_files(tmp_path)
        assert result["success"] is False
        assert any("JSON" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# add_intended_for_to_fmaps
# ---------------------------------------------------------------------------


class TestAddIntendedForToFmaps:
    def test_no_fmap_dir(self, tmp_path):
        result = add_intended_for_to_fmaps(tmp_path)
        assert result["success"] is False

    def test_no_jsons(self, tmp_path):
        fmap = tmp_path / "fmap"
        fmap.mkdir()
        result = add_intended_for_to_fmaps(tmp_path)
        assert result["success"] is False

    def test_dwi_acq(self, tmp_path):
        _add_fmap(tmp_path)
        _add_dwi(tmp_path)
        result = add_intended_for_to_fmaps(tmp_path)
        assert result["success"] is True
        assert len(result["updated_files"]) == 1
        assert result["updated_files"][0]["type"] == "DWI"

    def test_func_acq(self, tmp_path):
        _add_fmap(tmp_path, acq="func")
        _add_func(tmp_path)
        result = add_intended_for_to_fmaps(tmp_path)
        assert result["success"] is True
        assert result["updated_files"][0]["type"] == "functional"

    def test_unknown_acq(self, tmp_path):
        fmap = tmp_path / "fmap"
        fmap.mkdir()
        (fmap / "sub-01_acq-unknown_epi.json").write_text("{}")
        result = add_intended_for_to_fmaps(tmp_path)
        assert any("Unknown acquisition" in e for e in result["errors"])

    def test_no_targets(self, tmp_path):
        _add_fmap(tmp_path, nii=False, bvec=False, bval=False)
        # dwi dir does not exist
        result = add_intended_for_to_fmaps(tmp_path)
        assert any("No target files" in e for e in result["errors"])

    def test_update_success(self, tmp_path):
        _add_fmap(tmp_path)
        _add_dwi(tmp_path)
        _ = add_intended_for_to_fmaps(tmp_path)
        # Verify JSON was updated
        fmap_json = tmp_path / "fmap" / "sub-01_acq-dwi_epi.json"
        data = json.loads(fmap_json.read_text())
        assert "IntendedFor" in data

    def test_update_fail(self, tmp_path):
        _add_fmap(tmp_path)
        _add_dwi(tmp_path)
        with patch("voxelops.utils.bids._update_json_sidecar", return_value=False):
            result = add_intended_for_to_fmaps(tmp_path)
        assert any("Failed to update" in e for e in result["errors"])

    def test_dry_run(self, tmp_path):
        _add_fmap(tmp_path)
        _add_dwi(tmp_path)
        result = add_intended_for_to_fmaps(tmp_path, dry_run=True)
        assert result["dry_run"] is True
        assert result["updated_files"][0].get("note", "").startswith("Dry run")
        # Verify JSON was NOT updated
        fmap_json = tmp_path / "fmap" / "sub-01_acq-dwi_epi.json"
        data = json.loads(fmap_json.read_text())
        assert "IntendedFor" not in data

    def test_exception_in_loop(self, tmp_path):
        _add_fmap(tmp_path)
        with patch(
            "voxelops.utils.bids._find_dwi_targets",
            side_effect=RuntimeError("oops"),
        ):
            result = add_intended_for_to_fmaps(tmp_path)
        assert result["success"] is False
        assert any("Error processing" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# remove_bval_bvec_from_fmaps
# ---------------------------------------------------------------------------


class TestRemoveBvalBvecFromFmaps:
    def test_no_fmap_dir(self, tmp_path):
        result = remove_bval_bvec_from_fmaps(tmp_path)
        assert result["success"] is False

    def test_no_files(self, tmp_path):
        fmap = tmp_path / "fmap"
        fmap.mkdir()
        result = remove_bval_bvec_from_fmaps(tmp_path)
        assert result["success"] is True
        assert result["hidden_files"] == []

    def test_already_hidden(self, tmp_path):
        fmap = tmp_path / "fmap"
        fmap.mkdir()
        (fmap / ".sub-01_acq-dwi_epi.bvec").write_text("")
        result = remove_bval_bvec_from_fmaps(tmp_path)
        assert result["hidden_files"] == []

    def test_rename(self, tmp_path):
        _add_fmap(tmp_path)
        result = remove_bval_bvec_from_fmaps(tmp_path)
        assert result["success"] is True
        assert len(result["hidden_files"]) == 2
        fmap = tmp_path / "fmap"
        # Original files gone, hidden files present
        assert not [
            f for f in list(fmap.glob("*_epi.bvec")) if not f.name.startswith(".")
        ]
        assert not [
            f for f in list(fmap.glob("*_epi.bval")) if not f.name.startswith(".")
        ]
        assert list(fmap.glob(".*_epi.bvec"))
        assert list(fmap.glob(".*_epi.bval"))

    def test_dry_run(self, tmp_path):
        _add_fmap(tmp_path)
        result = remove_bval_bvec_from_fmaps(tmp_path, dry_run=True)
        assert result["dry_run"] is True
        assert len(result["hidden_files"]) == 2
        assert result["hidden_files"][0].get("note", "").startswith("Dry run")
        # Files still present
        fmap = tmp_path / "fmap"
        assert list(fmap.glob("*_epi.bvec"))

    def test_exception_during_rename(self, tmp_path):
        _add_fmap(tmp_path)
        with patch.object(Path, "rename", side_effect=OSError("perm")):
            result = remove_bval_bvec_from_fmaps(tmp_path)
        assert result["success"] is False
        assert any("Failed to hide" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# _find_dwi_targets / _find_func_targets
# ---------------------------------------------------------------------------


class TestFindDwiTargets:
    def test_dir_missing(self, tmp_path):
        assert _find_dwi_targets(tmp_path) == []

    def test_found(self, tmp_path):
        _add_dwi(tmp_path)
        targets = _find_dwi_targets(tmp_path)
        assert len(targets) == 1
        assert targets[0].name == "sub-01_dwi.nii.gz"

    def test_empty(self, tmp_path):
        (tmp_path / "dwi").mkdir()
        assert _find_dwi_targets(tmp_path) == []


class TestFindFuncTargets:
    def test_dir_missing(self, tmp_path):
        assert _find_func_targets(tmp_path) == []

    def test_found(self, tmp_path):
        _add_func(tmp_path)
        targets = _find_func_targets(tmp_path)
        assert len(targets) == 1
        assert targets[0].name == "sub-01_bold.nii.gz"

    def test_empty(self, tmp_path):
        (tmp_path / "func").mkdir()
        assert _find_func_targets(tmp_path) == []


# ---------------------------------------------------------------------------
# _build_intended_for_path
# ---------------------------------------------------------------------------


class TestBuildIntendedForPath:
    def test_no_session(self, tmp_path):
        dwi = tmp_path / "dwi" / "sub-01_dwi.nii.gz"
        dwi.parent.mkdir()
        dwi.write_bytes(b"")
        result = _build_intended_for_path(dwi, tmp_path)
        assert result == "dwi/sub-01_dwi.nii.gz"

    def test_with_session(self, tmp_path):
        dwi = tmp_path / "dwi" / "sub-01_dwi.nii.gz"
        dwi.parent.mkdir()
        dwi.write_bytes(b"")
        result = _build_intended_for_path(dwi, tmp_path, session="pre")
        assert result == "ses-pre/dwi/sub-01_dwi.nii.gz"

    def test_relative_to_fails(self, tmp_path):
        """When relative_to raises ValueError, fall back to filename only."""
        target = Path("/completely/different/file.nii.gz")
        result = _build_intended_for_path(target, tmp_path)
        assert result == "file.nii.gz"


# ---------------------------------------------------------------------------
# _update_json_sidecar
# ---------------------------------------------------------------------------


class TestUpdateJsonSidecar:
    def test_writable(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text(json.dumps({"A": 1}))
        result = _update_json_sidecar(f, ["dwi/file.nii.gz"])
        assert result is True
        data = json.loads(f.read_text())
        assert data["IntendedFor"] == ["dwi/file.nii.gz"]
        assert data["A"] == 1  # preserved

    def test_readonly(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text(json.dumps({"A": 1}))
        f.chmod(stat.S_IRUSR | stat.S_IRGRP)
        result = _update_json_sidecar(f, ["dwi/file.nii.gz"])
        assert result is True
        data = json.loads(f.read_text())
        assert "IntendedFor" in data

    def test_read_returns_none(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("not json")
        result = _update_json_sidecar(f, ["a"])
        assert result is False

    def test_exception(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text(json.dumps({"A": 1}))
        with patch("voxelops.utils.bids._read_json_sidecar", return_value={"A": 1}):
            with patch("builtins.open", side_effect=OSError("disk full")):
                result = _update_json_sidecar(f, ["a"])
        assert result is False


# ---------------------------------------------------------------------------
# _read_json_sidecar
# ---------------------------------------------------------------------------


class TestReadJsonSidecar:
    def test_valid_json(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text(json.dumps({"key": "val"}))
        data = _read_json_sidecar(f)
        assert data == {"key": "val"}

    def test_invalid_json(self, tmp_path):
        f = tmp_path / "bad.json"
        f.write_text("{broken")
        data = _read_json_sidecar(f)
        assert data is None

    def test_file_not_found(self, tmp_path):
        data = _read_json_sidecar(tmp_path / "nope.json")
        assert data is None


# -- Helper Functions Tests --------------------------------------------------


class TestBidsHelpers:
    def test_run_post_processing_step_success(self):
        mock_step_func = Mock(return_value={"success": True, "results": "ok"})
        results = {"errors": [], "success": True}
        _run_post_processing_step(mock_step_func, "test_step", results, 1, kw="a")
        mock_step_func.assert_called_once_with(1, kw="a")
        assert results["test_step"] == {"success": True, "results": "ok"}
        assert results["errors"] == []
        assert results["success"] is True

    def test_run_post_processing_step_failure_from_step_func(self):
        mock_step_func = Mock(return_value={"success": False, "errors": ["step error"]})
        results = {"errors": [], "success": True}
        _run_post_processing_step(mock_step_func, "test_step", results, 1, kw="a")
        assert results["test_step"] == {"success": False, "errors": ["step error"]}
        assert results["errors"] == ["step error"]
        assert results["success"] is False

    def test_run_post_processing_step_exception(self):
        mock_step_func = Mock(side_effect=RuntimeError("boom"))
        results = {"errors": [], "success": True}
        _run_post_processing_step(mock_step_func, "test_step", results, 1, kw="a")
        assert "Test step failed: boom" in results["errors"][0]
        assert results["success"] is False

    def test_process_single_fmap_json_dwi(self, tmp_path):
        participant_dir = tmp_path / "sub-01"
        fmap_dir = participant_dir / "fmap"
        fmap_dir.mkdir(parents=True)
        dwi_dir = participant_dir / "dwi"
        dwi_dir.mkdir(parents=True)
        (dwi_dir / "sub-01_dwi.nii.gz").touch()
        fmap_json = fmap_dir / "sub-01_acq-dwi_epi.json"
        fmap_json.write_text("{}")

        results = {"errors": [], "updated_files": []}
        with patch(
            "voxelops.utils.bids._update_json_sidecar", return_value=True
        ) as mock_update:
            _process_single_fmap_json(fmap_json, participant_dir, None, False, results)
            mock_update.assert_called_once()
            assert results["updated_files"][0]["type"] == "DWI"
            assert results["errors"] == []

    def test_process_single_fmap_json_func(self, tmp_path):
        participant_dir = tmp_path / "sub-01"
        fmap_dir = participant_dir / "fmap"
        fmap_dir.mkdir(parents=True)
        func_dir = participant_dir / "func"
        func_dir.mkdir(parents=True)
        (func_dir / "sub-01_bold.nii.gz").touch()
        fmap_json = fmap_dir / "sub-01_acq-func_epi.json"
        fmap_json.write_text("{}")

        results = {"errors": [], "updated_files": []}
        with patch(
            "voxelops.utils.bids._update_json_sidecar", return_value=True
        ) as mock_update:
            _process_single_fmap_json(fmap_json, participant_dir, None, False, results)
            mock_update.assert_called_once()
            assert results["updated_files"][0]["type"] == "functional"
            assert results["errors"] == []

    def test_process_single_fmap_json_unknown_acq(self, tmp_path):
        participant_dir = tmp_path / "sub-01"
        fmap_dir = participant_dir / "fmap"
        fmap_dir.mkdir(parents=True)
        fmap_json = fmap_dir / "sub-01_acq-unknown_epi.json"
        fmap_json.write_text("{}")

        results = {"errors": [], "updated_files": []}
        _process_single_fmap_json(fmap_json, participant_dir, None, False, results)
        assert "Unknown acquisition type" in results["errors"][0]

    def test_process_single_fmap_json_no_targets(self, tmp_path):
        participant_dir = tmp_path / "sub-01"
        fmap_dir = participant_dir / "fmap"
        fmap_dir.mkdir(parents=True)
        fmap_json = fmap_dir / "sub-01_acq-dwi_epi.json"
        fmap_json.write_text("{}")  # No dwi dir

        results = {"errors": [], "updated_files": []}
        _process_single_fmap_json(fmap_json, participant_dir, None, False, results)
        assert "No target files found" in results["errors"][0]

    def test_process_single_fmap_json_update_fail(self, tmp_path):
        participant_dir = tmp_path / "sub-01"
        fmap_dir = participant_dir / "fmap"
        fmap_dir.mkdir(parents=True)
        dwi_dir = participant_dir / "dwi"
        dwi_dir.mkdir(parents=True)
        (dwi_dir / "sub-01_dwi.nii.gz").touch()
        fmap_json = fmap_dir / "sub-01_acq-dwi_epi.json"
        fmap_json.write_text("{}")

        results = {"errors": [], "updated_files": []}
        with patch("voxelops.utils.bids._update_json_sidecar", return_value=False):
            _process_single_fmap_json(fmap_json, participant_dir, None, False, results)
            assert "Failed to update" in results["errors"][0]

    def test_process_single_fmap_json_dry_run(self, tmp_path):
        participant_dir = tmp_path / "sub-01"
        fmap_dir = participant_dir / "fmap"
        fmap_dir.mkdir(parents=True)
        dwi_dir = participant_dir / "dwi"
        dwi_dir.mkdir(parents=True)
        (dwi_dir / "sub-01_dwi.nii.gz").touch()
        fmap_json = fmap_dir / "sub-01_acq-dwi_epi.json"
        fmap_json.write_text("{}")

        results = {"errors": [], "updated_files": []}
        with patch("voxelops.utils.bids._update_json_sidecar") as mock_update:
            _process_single_fmap_json(fmap_json, participant_dir, None, True, results)
            mock_update.assert_not_called()
            assert "Dry run" in results["updated_files"][0]["note"]
