"""Tests for the top-level voxelops CLI entry point."""

from __future__ import annotations

import pytest

from voxelops.cli._main import main


def test_help_exits_zero():
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0


def test_version_exits_zero():
    with pytest.raises(SystemExit) as exc:
        main(["--version"])
    assert exc.value.code == 0


def test_no_subcommand_exits_nonzero():
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code != 0


def test_unknown_subcommand_exits_nonzero():
    with pytest.raises(SystemExit) as exc:
        main(["unknownprocedure"])
    assert exc.value.code != 0


@pytest.mark.parametrize(
    "subcommand",
    ["heudiconv", "qsiprep", "qsirecon", "qsiparc", "freesurfer"],
)
def test_subcommand_help_exits_zero(subcommand: str):
    with pytest.raises(SystemExit) as exc:
        main([subcommand, "--help"])
    assert exc.value.code == 0
