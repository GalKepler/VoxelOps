"""Shared utilities for all voxelops CLI subcommands."""

from __future__ import annotations

import json
import logging
import re
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pandas as pd

from voxelops.runners._base import _get_default_log_dir

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sanitizers
# ---------------------------------------------------------------------------


def sanitize_subject_code(subject_code: str) -> str:
    """Remove special characters and zero-pad to 4 digits."""
    return re.sub(r"[-_\s]", "", str(subject_code)).zfill(4)


def sanitize_session_id(session_id: str | int | float) -> str:
    """Convert to string, clean, and zero-pad to 12 digits."""
    if isinstance(session_id, float):
        if pd.isna(session_id):
            return ""
        session_str = str(int(session_id))
    else:
        session_str = str(session_id)
    return re.sub(r"[-_\s]", "", session_str).zfill(12)


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------


def load_sessions_from_csv(csv_path: str | Path) -> pd.DataFrame:
    """Load and sanitize a linked_sessions CSV.

    Expects columns ``SubjectCode`` and ``ScanID``.
    Returns a deduplicated DataFrame with ``subject_code`` and ``session_id``
    columns, plus any additional columns from the original CSV.

    Parameters
    ----------
    csv_path : str | Path
        Path to the linked_sessions CSV file.

    Returns
    -------
    pd.DataFrame
        Sanitized, deduplicated session DataFrame.
    """
    df = pd.read_csv(csv_path)
    df["subject_code"] = df["SubjectCode"].apply(sanitize_subject_code)
    df["session_id"] = df["ScanID"].apply(sanitize_session_id)
    return df.drop_duplicates(subset=["subject_code", "session_id"]).reset_index(
        drop=True
    )


# ---------------------------------------------------------------------------
# Last-execution check
# ---------------------------------------------------------------------------


def check_last_execution_log(
    procedure: str,
    participant: str,
    session: str | None,
    log_dir: Path | None,
    inputs: Any,
) -> bool:
    """Return True if the last execution log for this run shows success.

    Parameters
    ----------
    procedure : str
        Procedure name (e.g. "qsiprep", "freesurfer").
    participant : str
        Participant label (without 'sub-' prefix).
    session : str | None
        Session label (without 'ses-' prefix), or None.
    log_dir : Path | None
        Directory containing execution logs. Falls back to
        ``_get_default_log_dir(inputs)`` when None or non-existent.
    inputs : Any
        Procedure inputs object (used to derive default log dir).

    Returns
    -------
    bool
        True if the last matching log shows ``"success": true``.
    """
    if log_dir is None or not log_dir.exists():
        log_dir = _get_default_log_dir(inputs)

    session_part = f"_ses-{session}" if session else ""
    prefix = f"{procedure}_sub-{participant}{session_part}"
    log_files = list(log_dir.glob(f"{prefix}_*.json"))
    if not log_files:
        return False

    last = sorted(log_files, key=lambda f: f.stat().st_mtime)[-1]
    with open(last) as f:
        return bool(json.load(f).get("success"))


# ---------------------------------------------------------------------------
# Generic parallel runner
# ---------------------------------------------------------------------------


def run_parallel(
    items: list[Any],
    process_fn: Callable[[Any], dict],
    max_workers: int = 4,
    label_fn: Callable[[Any], str] | None = None,
) -> list[dict]:
    """Execute *process_fn* over *items* using a thread pool.

    Each Docker invocation spawns a subprocess so threads are appropriate —
    the GIL is released while waiting for the child process.

    Parameters
    ----------
    items : list
        Work items (participant strings, (participant, session) tuples,
        DataFrame rows, etc.).
    process_fn : Callable[[item], dict]
        Function that processes one item and returns a result dict with at
        least ``"success"`` (bool) and ``"error"`` (str | None).
    max_workers : int
        Number of items to process concurrently.
    label_fn : Callable[[item], str] | None
        Optional function that converts an item to a human-readable label
        for log messages.  Defaults to ``str(item)``.

    Returns
    -------
    list[dict]
        One result dict per item, in completion order.
    """
    if label_fn is None:
        label_fn = str

    results: list[dict] = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(process_fn, item): item for item in items}
        for future in as_completed(futures):
            item = futures[future]
            label = label_fn(item)
            try:
                result = future.result()
            except Exception as exc:
                logger.error("Unexpected error for %s: %s", label, exc)
                result = {"success": False, "error": str(exc)}
            results.append(result)
            status = "OK" if result["success"] else "FAILED"
            logger.info(
                "[%s] %s  duration=%s  error=%s",
                status,
                label,
                result.get("duration_human"),
                result.get("error"),
            )

    return results


# ---------------------------------------------------------------------------
# Result summary
# ---------------------------------------------------------------------------


def print_result_summary(
    results: list[dict],
    id_fields: tuple[str, ...] = ("participant",),
) -> int:
    """Log success/failure counts and list failed runs.

    Parameters
    ----------
    results : list[dict]
        Result dicts from :func:`run_parallel`.
    id_fields : tuple[str, ...]
        Keys to include in the failure label (e.g. ``("participant", "session")``).

    Returns
    -------
    int
        Exit code: 0 if all succeeded, 1 if any failed.
    """
    n_ok = sum(r["success"] for r in results)
    n_fail = len(results) - n_ok
    logger.info("Done: %d succeeded, %d failed", n_ok, n_fail)

    if n_fail:
        logger.warning("Failed runs:")
        for r in results:
            if not r["success"]:
                label = " ".join(
                    f"{k}={r.get(k)}" for k in id_fields if r.get(k) is not None
                )
                logger.warning("  %s: %s", label, r.get("error"))

    return 1 if n_fail else 0


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------


def configure_logging(level: str) -> None:
    """Configure the root logger.

    Parameters
    ----------
    level : str
        One of DEBUG, INFO, WARNING, ERROR.
    """
    root = logging.getLogger()
    root.setLevel(level)
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)-8s %(message)s",
                datefmt="%Y-%m-%dT%H:%M:%S",
            )
        )
        root.addHandler(handler)
