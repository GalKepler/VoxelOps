"""Top-level ``voxelops`` CLI entry point."""

from __future__ import annotations

import argparse
import sys

import voxelops
from voxelops.cli import freesurfer, heudiconv, qsiparc, qsiprep, qsirecon

_SUBCOMMANDS = [heudiconv, qsiprep, qsirecon, qsiparc, freesurfer]


def main(argv: list[str] | None = None) -> None:
    """Entry point for the ``voxelops`` command.

    Parameters
    ----------
    argv : list[str] | None
        Argument list (defaults to ``sys.argv[1:]``).  Accepts an explicit
        list to make the function testable without mocking ``sys.argv``.
    """
    parser = argparse.ArgumentParser(
        prog="voxelops",
        description=(
            "VoxelOps: neuroimaging pipeline automation for brain banks.\n\n"
            "Run ``voxelops <procedure> --help`` for procedure-specific options."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {voxelops.__version__}",
    )

    subparsers = parser.add_subparsers(
        dest="procedure",
        required=True,
        metavar="<procedure>",
    )
    for module in _SUBCOMMANDS:
        module.register_parser(subparsers)

    args = parser.parse_args(argv)
    sys.exit(args.func(args))
