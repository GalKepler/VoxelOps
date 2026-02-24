"""voxelops heudiconv — DICOM to BIDS conversion CLI subcommand."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from voxelops import HeudiconvDefaults, HeudiconvInputs, run_procedure
from voxelops.cli._common import (
    check_last_execution_log,
    configure_logging,
    load_sessions_from_csv,
    print_result_summary,
    run_parallel,
)
from voxelops.cli._parsers import add_execution_args, add_output_args

logger = logging.getLogger(__name__)


def register_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the ``heudiconv`` subcommand."""
    parser = subparsers.add_parser(
        "heudiconv",
        description="Convert DICOM files to BIDS format using HeudiConv.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help="DICOM → BIDS conversion (HeudiConv)",
    )

    # Required inputs
    parser.add_argument(
        "--csv",
        required=True,
        type=Path,
        help=("Path to linked_sessions CSV (columns: SubjectCode, ScanID, dicom_path)"),
    )
    add_output_args(parser, work_dir=False)
    parser.add_argument(
        "--heuristic",
        required=True,
        type=Path,
        help="Path to HeudiConv heuristic.py",
    )

    # HeudiConv options
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing BIDS outputs",
    )
    parser.add_argument(
        "--docker-image",
        default="nipy/heudiconv:1.3.4",
        help="HeudiConv Docker image",
    )

    add_execution_args(parser, default_workers=4)
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the heudiconv subcommand."""
    configure_logging(args.log_level)

    sessions = load_sessions_from_csv(args.csv)
    sessions = sessions.dropna(subset=["dicom_path"]).reset_index(drop=True)
    logger.info("Loaded %d session(s) from CSV", len(sessions))

    output_dir = Path(args.output_dir).resolve()
    heuristic = Path(args.heuristic).resolve()
    log_dir = Path(args.log_dir).resolve() if args.log_dir else None

    config = HeudiconvDefaults(
        heuristic=heuristic,
        overwrite=args.overwrite,
        docker_image=args.docker_image,
    )

    def process(row: tuple) -> dict:
        _, r = row
        subject = r["subject_code"]
        session = r["session_id"]
        label = f"sub-{subject} ses-{session}"
        logger.info("Starting %s", label)

        inputs = HeudiconvInputs(
            dicom_dir=Path(r["dicom_path"]),
            participant=subject,
            session=session,
            output_dir=output_dir,
        )
        if not args.force and check_last_execution_log(
            "heudiconv", subject, session, log_dir, inputs
        ):
            logger.info("Skipping %s (already executed successfully)", label)
            return {
                "participant": subject,
                "session": session,
                "success": True,
                "duration_human": None,
                "output": None,
                "error": "Skipped (already executed successfully)",
            }
        result = run_procedure(
            procedure="heudiconv",
            inputs=inputs,
            config=config,
            log_dir=log_dir,
        )
        bids_dir = None
        if result.execution:
            outputs = result.execution.get("expected_outputs")
            bids_dir = str(getattr(outputs, "bids_dir", "") or "")
        return {
            "participant": subject,
            "session": session,
            "success": result.success,
            "duration_human": (
                result.execution.get("duration_human") if result.execution else None
            ),
            "output": bids_dir,
            "error": result.get_failure_reason(),
        }

    def label_fn(row: tuple) -> str:
        _, r = row
        return f"sub-{r['subject_code']} ses-{r['session_id']}"

    results = run_parallel(
        items=list(sessions.iterrows()),
        process_fn=process,
        max_workers=args.workers,
        label_fn=label_fn,
    )
    return print_result_summary(results, id_fields=("participant", "session"))
