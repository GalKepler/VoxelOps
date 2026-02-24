"""Tests for voxelops.cli._common shared utilities."""

from __future__ import annotations

import csv
import logging
from pathlib import Path

import pytest

from voxelops.cli._common import (
    configure_logging,
    load_sessions_from_csv,
    print_result_summary,
    run_parallel,
    sanitize_session_id,
    sanitize_subject_code,
)

# ---------------------------------------------------------------------------
# sanitize_subject_code
# ---------------------------------------------------------------------------


def test_sanitize_subject_code_pads_to_4():
    assert sanitize_subject_code("7") == "0007"


def test_sanitize_subject_code_strips_non_alnum():
    assert sanitize_subject_code("AB-CD") == "ABCD"


def test_sanitize_subject_code_already_correct():
    assert sanitize_subject_code("0042") == "0042"


def test_sanitize_subject_code_long_code():
    # Longer than 4 chars — should NOT be truncated
    assert sanitize_subject_code("12345") == "12345"


# ---------------------------------------------------------------------------
# sanitize_session_id
# ---------------------------------------------------------------------------


def test_sanitize_session_id_int():
    assert sanitize_session_id(1) == "000000000001"


def test_sanitize_session_id_float():
    # Float like 1.0 → int 1 → "000000000001"
    assert sanitize_session_id(1.0) == "000000000001"


def test_sanitize_session_id_nan():
    result = sanitize_session_id(float("nan"))
    assert result == ""


def test_sanitize_session_id_string():
    assert sanitize_session_id("42") == "000000000042"


def test_sanitize_session_id_long_string():
    long_id = "20240101120000"
    result = sanitize_session_id(long_id)
    assert result == long_id  # longer than 12 — not truncated


# ---------------------------------------------------------------------------
# load_sessions_from_csv
# ---------------------------------------------------------------------------


def _write_csv(path: Path, rows: list[dict]) -> None:
    if not rows:
        return
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_load_sessions_from_csv_basic(tmp_path):
    csv_path = tmp_path / "sessions.csv"
    _write_csv(
        csv_path,
        [
            {"SubjectCode": "1", "ScanID": "2"},
            {"SubjectCode": "3", "ScanID": "4"},
        ],
    )
    df = load_sessions_from_csv(csv_path)
    assert "subject_code" in df.columns
    assert "session_id" in df.columns
    assert len(df) == 2
    assert df["subject_code"].iloc[0] == "0001"


def test_load_sessions_from_csv_deduplicates(tmp_path):
    csv_path = tmp_path / "sessions.csv"
    _write_csv(
        csv_path,
        [
            {"SubjectCode": "1", "ScanID": "2"},
            {"SubjectCode": "1", "ScanID": "2"},
        ],
    )
    df = load_sessions_from_csv(csv_path)
    assert len(df) == 1


def test_load_sessions_from_csv_missing_columns(tmp_path):
    csv_path = tmp_path / "sessions.csv"
    _write_csv(csv_path, [{"BadCol": "x"}])
    with pytest.raises(KeyError):
        load_sessions_from_csv(csv_path)


# ---------------------------------------------------------------------------
# run_parallel
# ---------------------------------------------------------------------------


def test_run_parallel_returns_results():
    items = [1, 2, 3]

    def process(x):
        return {"value": x * 2, "success": True}

    results = run_parallel(items, process, max_workers=2)
    assert len(results) == 3
    values = sorted(r["value"] for r in results)
    assert values == [2, 4, 6]


def test_run_parallel_captures_exceptions():
    def process(x):
        if x == 2:
            raise ValueError("bad item")
        return {"value": x, "success": True}

    results = run_parallel([1, 2, 3], process, max_workers=1)
    assert len(results) == 3
    failed = [r for r in results if not r.get("success")]
    assert len(failed) == 1
    assert "bad item" in failed[0]["error"]


def test_run_parallel_label_fn():
    def process(x):
        return {"value": x, "success": True}

    run_parallel([10], process, label_fn=lambda x: f"item-{x}")


# ---------------------------------------------------------------------------
# print_result_summary
# ---------------------------------------------------------------------------


def test_print_result_summary_all_success():
    results = [{"participant": "A", "success": True}]
    code = print_result_summary(results, id_fields=("participant",))
    assert code == 0


def test_print_result_summary_some_failures():
    results = [
        {"participant": "A", "success": True},
        {"participant": "B", "success": False, "error": "oops"},
    ]
    code = print_result_summary(results, id_fields=("participant",))
    assert code != 0


def test_print_result_summary_empty():
    code = print_result_summary([], id_fields=("participant",))
    assert code == 0


# ---------------------------------------------------------------------------
# configure_logging
# ---------------------------------------------------------------------------


def test_configure_logging_sets_level():
    configure_logging("DEBUG")
    assert logging.getLogger().level == logging.DEBUG

    configure_logging("WARNING")
    assert logging.getLogger().level == logging.WARNING
