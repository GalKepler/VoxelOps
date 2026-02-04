"""Tests for voxelops.schemas.heudiconv -- HeudiconvInputs/Outputs/Defaults."""

from pathlib import Path

from voxelops.schemas.heudiconv import (
    HeudiconvDefaults,
    HeudiconvInputs,
    HeudiconvOutputs,
)

# -- HeudiconvInputs ---------------------------------------------------------


class TestHeudiconvInputs:
    def test_string_to_path_conversion(self):
        inp = HeudiconvInputs(dicom_dir="/data/dicoms", participant="01")
        assert isinstance(inp.dicom_dir, Path)
        assert inp.dicom_dir == Path("/data/dicoms")

    def test_output_dir_converted(self):
        inp = HeudiconvInputs(
            dicom_dir="/d", participant="01", output_dir="/out"
        )
        assert isinstance(inp.output_dir, Path)

    def test_output_dir_none_stays_none(self):
        inp = HeudiconvInputs(dicom_dir="/d", participant="01")
        assert inp.output_dir is None

    def test_session_stored(self):
        inp = HeudiconvInputs(
            dicom_dir="/d", participant="01", session="pre"
        )
        assert inp.session == "pre"

    def test_heuristic_not_converted_when_none(self):
        inp = HeudiconvInputs(dicom_dir="/d", participant="01")
        assert inp.heuristic is None


# -- HeudiconvOutputs --------------------------------------------------------


class TestHeudiconvOutputs:
    def test_from_inputs_no_session(self):
        inp = HeudiconvInputs(dicom_dir="/d", participant="01")
        out = HeudiconvOutputs.from_inputs(inp, Path("/bids"))
        assert out.bids_dir == Path("/bids")
        assert out.participant_dir == Path("/bids/sub-01")
        assert out.dataset_description == Path("/bids/dataset_description.json")

    def test_from_inputs_with_session(self):
        inp = HeudiconvInputs(dicom_dir="/d", participant="01", session="pre")
        out = HeudiconvOutputs.from_inputs(inp, Path("/bids"))
        assert out.participant_dir == Path("/bids/sub-01/ses-pre")


# -- HeudiconvDefaults -------------------------------------------------------


class TestHeudiconvDefaults:
    def test_default_values(self):
        d = HeudiconvDefaults()
        assert d.heuristic is None
        assert d.bids_validator is True
        assert d.overwrite is False
        assert d.converter == "dcm2niix"
        assert d.bids == "notop"
        assert d.grouping == "all"
        assert d.docker_image == "nipy/heudiconv:1.3.4"
        assert d.post_process is True
        assert d.post_process_dry_run is False

    def test_heuristic_path_conversion(self):
        d = HeudiconvDefaults(heuristic="/path/h.py")
        assert isinstance(d.heuristic, Path)

    def test_heuristic_none_stays_none(self):
        d = HeudiconvDefaults()
        assert d.heuristic is None
