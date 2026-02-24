"""Shared argparse argument-group factories for voxelops CLI subcommands."""

from __future__ import annotations

import argparse
from pathlib import Path


def add_participant_args(parser: argparse.ArgumentParser) -> None:
    """Add ``--participants`` / ``--csv`` mutually exclusive group.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The subcommand parser to extend.
    """
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--participants",
        nargs="+",
        metavar="LABEL",
        help="One or more participant labels (without 'sub-' prefix)",
    )
    group.add_argument(
        "--csv",
        type=Path,
        metavar="CSV",
        help="CSV file with 'SubjectCode' and 'ScanID' columns",
    )


def add_output_args(
    parser: argparse.ArgumentParser,
    work_dir: bool = True,
) -> None:
    """Add ``--output-dir`` (required) and optionally ``--work-dir``.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The subcommand parser to extend.
    work_dir : bool
        Whether to add the ``--work-dir`` optional argument.
    """
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Output directory",
    )
    if work_dir:
        parser.add_argument(
            "--work-dir",
            type=Path,
            help="Working directory for tool intermediates",
        )


def add_execution_args(
    parser: argparse.ArgumentParser,
    default_workers: int = 4,
) -> None:
    """Add ``--workers``, ``--log-dir``, ``--log-level``, and ``--force``.

    Parameters
    ----------
    parser : argparse.ArgumentParser
        The subcommand parser to extend.
    default_workers : int
        Default number of parallel worker threads.
    """
    parser.add_argument(
        "--workers",
        type=int,
        default=default_workers,
        help="Number of runs to process concurrently",
    )
    parser.add_argument(
        "--log-dir",
        type=Path,
        help="Directory to save execution logs (one JSON per run)",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-run even if outputs already exist",
    )


def parse_key_value_pairs(
    raw: list[str] | None,
    flag_name: str = "--option",
) -> dict[str, str] | None:
    """Parse ``KEY=VALUE`` strings into a ``{key: value}`` dict.

    Returns ``{}`` when *raw* is an empty list (flag supplied with no args),
    which signals "use any file of this type without further filtering".
    Returns ``None`` when *raw* is ``None`` (flag not supplied at all).

    Parameters
    ----------
    raw : list[str] | None
        Raw argument values from argparse.
    flag_name : str
        Name of the CLI flag (used in the error message).

    Returns
    -------
    dict[str, str] | None
        Parsed key-value pairs, or None if the flag was not supplied.

    Raises
    ------
    argparse.ArgumentTypeError
        If any entry does not contain ``=``.
    """
    if raw is None:
        return None
    result: dict[str, str] = {}
    for item in raw:
        if "=" not in item:
            raise argparse.ArgumentTypeError(
                f"{flag_name} entries must be KEY=VALUE, got: {item!r}"
            )
        key, _, value = item.partition("=")
        result[key.strip()] = value.strip()
    return result
