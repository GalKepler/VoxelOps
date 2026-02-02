"""Tests for voxelops.schemas.qsiprep -- QSIPrepInputs/Outputs/Defaults."""

from pathlib import Path

from voxelops.schemas.qsiprep import (
    QSIPrepInputs,
    QSIPrepOutputs,
    QSIPrepDefaults,
)


# -- QSIPrepInputs -----------------------------------------------------------


class TestQSIPrepInputs:
    def test_string_to_path(self):
        inp = QSIPrepInputs(bids_dir="/data/bids", participant="01")
        assert isinstance(inp.bids_dir, Path)

    def test_output_dir_converted(self):
        inp = QSIPrepInputs(
            bids_dir="/d", participant="01", output_dir="/out"
        )
        assert isinstance(inp.output_dir, Path)

    def test_output_dir_none(self):
        inp = QSIPrepInputs(bids_dir="/d", participant="01")
        assert inp.output_dir is None

    def test_work_dir_converted(self):
        inp = QSIPrepInputs(
            bids_dir="/d", participant="01", work_dir="/work"
        )
        assert isinstance(inp.work_dir, Path)

    def test_work_dir_none(self):
        inp = QSIPrepInputs(bids_dir="/d", participant="01")
        assert inp.work_dir is None

    def test_bids_filters_converted(self):
        inp = QSIPrepInputs(
            bids_dir="/d", participant="01", bids_filters="/f.json"
        )
        assert isinstance(inp.bids_filters, Path)

    def test_bids_filters_none(self):
        inp = QSIPrepInputs(bids_dir="/d", participant="01")
        assert inp.bids_filters is None


# -- QSIPrepOutputs ----------------------------------------------------------


class TestQSIPrepOutputs:
    def test_from_inputs(self):
        inp = QSIPrepInputs(bids_dir="/d", participant="01")
        out = QSIPrepOutputs.from_inputs(
            inp, Path("/out"), Path("/work")
        )
        assert out.qsiprep_dir == Path("/out/qsiprep")
        assert out.participant_dir == Path("/out/qsiprep/sub-01")
        assert out.html_report == Path("/out/qsiprep/sub-01.html")
        assert out.work_dir == Path("/work")
        assert out.figures_dir == Path("/out/qsiprep/sub-01/figures")


# -- QSIPrepDefaults ---------------------------------------------------------


class TestQSIPrepDefaults:
    def test_default_values(self):
        d = QSIPrepDefaults()
        assert d.nprocs == 8
        assert d.mem_mb == 16000
        assert d.output_resolution == 1.6
        assert d.anatomical_template == ["MNI152NLin2009cAsym"]
        assert d.longitudinal is False
        assert d.subject_anatomical_reference == "unbiased"
        assert d.skip_bids_validation is False
        assert d.fs_license is None
        assert d.docker_image == "pennlinc/qsiprep:latest"

    def test_fs_license_path_conversion(self):
        d = QSIPrepDefaults(fs_license="/lic.txt")
        assert isinstance(d.fs_license, Path)

    def test_fs_license_none(self):
        d = QSIPrepDefaults()
        assert d.fs_license is None
