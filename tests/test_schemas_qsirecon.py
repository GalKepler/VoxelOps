"""Tests for voxelops.schemas.qsirecon -- QSIReconInputs/Outputs/Defaults."""

from pathlib import Path

from voxelops.schemas.qsirecon import (
    QSIReconInputs,
    QSIReconOutputs,
    QSIReconDefaults,
)


# -- QSIReconInputs ----------------------------------------------------------


class TestQSIReconInputs:
    def test_string_to_path(self):
        inp = QSIReconInputs(qsiprep_dir="/d", participant="01")
        assert isinstance(inp.qsiprep_dir, Path)

    def test_output_dir_converted(self):
        inp = QSIReconInputs(
            qsiprep_dir="/d", participant="01", output_dir="/out"
        )
        assert isinstance(inp.output_dir, Path)

    def test_output_dir_none(self):
        inp = QSIReconInputs(qsiprep_dir="/d", participant="01")
        assert inp.output_dir is None

    def test_work_dir_converted(self):
        inp = QSIReconInputs(
            qsiprep_dir="/d", participant="01", work_dir="/w"
        )
        assert isinstance(inp.work_dir, Path)

    def test_work_dir_none(self):
        inp = QSIReconInputs(qsiprep_dir="/d", participant="01")
        assert inp.work_dir is None

    def test_recon_spec_converted(self):
        inp = QSIReconInputs(
            qsiprep_dir="/d", participant="01", recon_spec="/r.yaml"
        )
        assert isinstance(inp.recon_spec, Path)

    def test_recon_spec_none(self):
        inp = QSIReconInputs(qsiprep_dir="/d", participant="01")
        assert inp.recon_spec is None

    def test_datasets_path_conversion(self):
        inp = QSIReconInputs(
            qsiprep_dir="/d",
            participant="01",
            datasets={"freesurfer": "/fs", "anat": "/anat"},
        )
        assert isinstance(inp.datasets["freesurfer"], Path)
        assert isinstance(inp.datasets["anat"], Path)

    def test_datasets_none(self):
        inp = QSIReconInputs(qsiprep_dir="/d", participant="01")
        assert inp.datasets is None

    def test_atlases_stored(self):
        inp = QSIReconInputs(
            qsiprep_dir="/d", participant="01", atlases=["AAL116"]
        )
        assert inp.atlases == ["AAL116"]

    def test_atlases_none(self):
        inp = QSIReconInputs(qsiprep_dir="/d", participant="01")
        assert inp.atlases is None


# -- QSIReconOutputs ---------------------------------------------------------


class TestQSIReconOutputs:
    def test_from_inputs(self):
        inp = QSIReconInputs(qsiprep_dir="/d", participant="01")
        out = QSIReconOutputs.from_inputs(inp, Path("/out"), Path("/work"))
        assert out.qsirecon_dir == Path("/out/qsirecon")
        assert out.participant_dir == Path("/out/qsirecon/sub-01")
        assert out.html_report == Path("/out/qsirecon/sub-01.html")
        assert out.work_dir == Path("/work")


# -- QSIReconDefaults --------------------------------------------------------


class TestQSIReconDefaults:
    def test_default_values(self):
        d = QSIReconDefaults()
        assert d.nprocs == 8
        assert d.mem_mb == 16000
        assert len(d.atlases) == 14
        assert "4S156Parcels" in d.atlases
        assert "Gordon333Ext" in d.atlases
        assert d.fs_subjects_dir is None
        assert d.fs_license is None
        assert d.docker_image == "pennlinc/qsirecon:latest"

    def test_fs_subjects_dir_converted(self):
        d = QSIReconDefaults(fs_subjects_dir="/subj")
        assert isinstance(d.fs_subjects_dir, Path)

    def test_fs_subjects_dir_none(self):
        d = QSIReconDefaults()
        assert d.fs_subjects_dir is None

    def test_fs_license_converted(self):
        d = QSIReconDefaults(fs_license="/lic.txt")
        assert isinstance(d.fs_license, Path)

    def test_fs_license_none(self):
        d = QSIReconDefaults()
        assert d.fs_license is None
