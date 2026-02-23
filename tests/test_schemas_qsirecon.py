"""Tests for voxelops.schemas.qsirecon -- QSIReconInputs/Outputs/Defaults."""

from pathlib import Path

from voxelops.schemas.qsirecon import (
    QSIReconDefaults,
    QSIReconInputs,
    QSIReconOutputs,
)

# -- QSIReconInputs ----------------------------------------------------------


class TestQSIReconInputs:
    def test_string_to_path(self):
        inp = QSIReconInputs(qsiprep_dir="/d", participant="01")
        assert isinstance(inp.qsiprep_dir, Path)

    def test_output_dir_converted(self):
        inp = QSIReconInputs(qsiprep_dir="/d", participant="01", output_dir="/out")
        assert isinstance(inp.output_dir, Path)

    def test_output_dir_none(self):
        inp = QSIReconInputs(qsiprep_dir="/d", participant="01")
        assert inp.output_dir is None

    def test_work_dir_converted(self):
        inp = QSIReconInputs(qsiprep_dir="/d", participant="01", work_dir="/w")
        assert isinstance(inp.work_dir, Path)

    def test_work_dir_none(self):
        inp = QSIReconInputs(qsiprep_dir="/d", participant="01")
        assert inp.work_dir is None

    def test_recon_spec_converted(self):
        inp = QSIReconInputs(qsiprep_dir="/d", participant="01", recon_spec="/r.yaml")
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
        inp = QSIReconInputs(qsiprep_dir="/d", participant="01", atlases=["AAL116"])
        assert inp.atlases == ["AAL116"]

    def test_atlases_default(self):
        """Test that atlases has a default value."""
        inp = QSIReconInputs(qsiprep_dir="/d", participant="01")
        # atlases has a default_factory, so it's never None
        assert len(inp.atlases) == 14
        assert "AAL116" in inp.atlases

    def test_session_none_by_default(self):
        inp = QSIReconInputs(qsiprep_dir="/d", participant="01")
        assert inp.session is None

    def test_session_stored(self):
        inp = QSIReconInputs(qsiprep_dir="/d", participant="01", session="20240711")
        assert inp.session == "20240711"


# -- QSIReconOutputs ---------------------------------------------------------


class TestQSIReconOutputs:
    def test_from_inputs(self):
        """Test that from_inputs generates expected output paths."""
        inp = QSIReconInputs(qsiprep_dir="/d", participant="01")
        out = QSIReconOutputs.from_inputs(inp, Path("/out"), Path("/work"))
        # output_dir is now the qsirecon_dir directly (not /out/qsirecon)
        assert out.qsirecon_dir == Path("/out")
        assert out.participant_dir == Path("/out/sub-01")
        # workflow_reports replaces html_report
        assert "default" in out.workflow_reports
        assert None in out.workflow_reports["default"]  # No session
        assert out.workflow_reports["default"][None] == Path(
            "/out/derivatives/qsirecon-default/sub-01.html"
        )
        assert out.work_dir == Path("/work")


# -- QSIReconDefaults --------------------------------------------------------


class TestQSIReconDefaults:
    def test_default_values(self):
        """Test default configuration values."""
        d = QSIReconDefaults()
        assert d.nprocs == 8
        assert d.mem_mb == 16000
        # atlases moved to QSIReconInputs
        assert d.fs_subjects_dir is None
        assert d.fs_license is None
        assert d.docker_image == "pennlinc/qsirecon:1.2.0"
        assert d.force is False

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
