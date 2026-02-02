"""Tests for voxelops.schemas.qsiparc -- QSIParcInputs/Outputs/Defaults."""

from pathlib import Path

from voxelops.schemas.qsiparc import (
    QSIParcInputs,
    QSIParcOutputs,
    QSIParcDefaults,
)


# -- QSIParcInputs -----------------------------------------------------------


class TestQSIParcInputs:
    def test_string_to_path(self):
        inp = QSIParcInputs(qsirecon_dir="/d", participant="01")
        assert isinstance(inp.qsirecon_dir, Path)

    def test_output_dir_converted(self):
        inp = QSIParcInputs(
            qsirecon_dir="/d", participant="01", output_dir="/out"
        )
        assert isinstance(inp.output_dir, Path)

    def test_output_dir_none(self):
        inp = QSIParcInputs(qsirecon_dir="/d", participant="01")
        assert inp.output_dir is None

    def test_session_stored(self):
        inp = QSIParcInputs(
            qsirecon_dir="/d", participant="01", session="pre"
        )
        assert inp.session == "pre"

    def test_atlases_stored(self):
        from conftest import MockAtlasDefinition

        atlas = MockAtlasDefinition(name="test")
        inp = QSIParcInputs(
            qsirecon_dir="/d", participant="01", atlases=[atlas]
        )
        assert inp.atlases == [atlas]

    def test_n_jobs_stored(self):
        inp = QSIParcInputs(
            qsirecon_dir="/d", participant="01", n_jobs=4
        )
        assert inp.n_jobs == 4


# -- QSIParcOutputs ----------------------------------------------------------


class TestQSIParcOutputs:
    def test_from_inputs(self):
        inp = QSIParcInputs(qsirecon_dir="/d", participant="01")
        out = QSIParcOutputs.from_inputs(inp, Path("/out"))
        assert out.output_dir == Path("/out")


# -- QSIParcDefaults ---------------------------------------------------------


class TestQSIParcDefaults:
    def test_default_values(self):
        d = QSIParcDefaults()
        assert d.mask == "gm"
        assert d.force is False
        assert d.background_label == 0
        assert d.resampling_target == "data"
        assert d.log_level == "INFO"
        assert d.n_jobs == 1
        assert d.n_procs == 1
