"""Tests for voxelops.cli._parsers shared argument factories."""

from __future__ import annotations

import argparse

import pytest

from voxelops.cli._parsers import (
    add_execution_args,
    add_output_args,
    add_participant_args,
    parse_key_value_pairs,
)


def _make_parser() -> argparse.ArgumentParser:
    return argparse.ArgumentParser()


# ---------------------------------------------------------------------------
# add_participant_args
# ---------------------------------------------------------------------------


def test_add_participant_args_participants():
    p = _make_parser()
    add_participant_args(p)
    args = p.parse_args(["--participants", "A", "B"])
    assert args.participants == ["A", "B"]
    assert args.csv is None


def test_add_participant_args_csv(tmp_path):
    csv_path = tmp_path / "s.csv"
    csv_path.touch()
    p = _make_parser()
    add_participant_args(p)
    args = p.parse_args(["--csv", str(csv_path)])
    assert str(args.csv) == str(csv_path)
    assert args.participants is None


def test_add_participant_args_mutually_exclusive():
    p = _make_parser()
    add_participant_args(p)
    with pytest.raises(SystemExit):
        p.parse_args(["--participants", "A", "--csv", "file.csv"])


def test_add_participant_args_required():
    p = _make_parser()
    add_participant_args(p)
    with pytest.raises(SystemExit):
        p.parse_args([])


# ---------------------------------------------------------------------------
# add_output_args
# ---------------------------------------------------------------------------


def test_add_output_args_output_dir_required():
    p = _make_parser()
    add_output_args(p)
    with pytest.raises(SystemExit):
        p.parse_args([])


def test_add_output_args_sets_output_dir(tmp_path):
    p = _make_parser()
    add_output_args(p)
    args = p.parse_args(["--output-dir", str(tmp_path)])
    assert str(args.output_dir) == str(tmp_path)
    assert args.work_dir is None


def test_add_output_args_no_work_dir():
    p = _make_parser()
    add_output_args(p, work_dir=False)
    with pytest.raises(SystemExit):
        p.parse_args(["--output-dir", "/x", "--work-dir", "/y"])


# ---------------------------------------------------------------------------
# add_execution_args
# ---------------------------------------------------------------------------


def test_add_execution_args_defaults():
    p = _make_parser()
    add_execution_args(p, default_workers=3)
    args = p.parse_args([])
    assert args.workers == 3
    assert args.log_dir is None
    assert args.log_level == "INFO"
    assert args.force is False


def test_add_execution_args_force_flag():
    p = _make_parser()
    add_execution_args(p)
    args = p.parse_args(["--force"])
    assert args.force is True


def test_add_execution_args_log_level_choices():
    p = _make_parser()
    add_execution_args(p)
    with pytest.raises(SystemExit):
        p.parse_args(["--log-level", "VERBOSE"])


# ---------------------------------------------------------------------------
# parse_key_value_pairs
# ---------------------------------------------------------------------------


def test_parse_key_value_pairs_none():
    assert parse_key_value_pairs(None, "--flag") is None


def test_parse_key_value_pairs_empty_list():
    assert parse_key_value_pairs([], "--flag") == {}


def test_parse_key_value_pairs_single():
    result = parse_key_value_pairs(["key=value"], "--flag")
    assert result == {"key": "value"}


def test_parse_key_value_pairs_multiple():
    result = parse_key_value_pairs(["a=1", "b=2"], "--flag")
    assert result == {"a": "1", "b": "2"}


def test_parse_key_value_pairs_value_with_equals():
    result = parse_key_value_pairs(["path=/some/dir/with=eq"], "--flag")
    assert result == {"path": "/some/dir/with=eq"}


def test_parse_key_value_pairs_missing_equals():
    with pytest.raises(argparse.ArgumentTypeError):
        parse_key_value_pairs(["badvalue"], "--flag")
