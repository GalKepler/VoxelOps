"""voxelops qsiprep — diffusion MRI preprocessing CLI subcommand."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from voxelops import QSIPrepDefaults, QSIPrepInputs, run_procedure
from voxelops.cli._common import (
    check_last_execution_log,
    configure_logging,
    load_sessions_from_csv,
    print_result_summary,
    run_parallel,
)
from voxelops.cli._parsers import (
    add_execution_args,
    add_output_args,
    add_participant_args,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CSV loading (qsiprep-specific: checks output-dir existence for skip logic)
# ---------------------------------------------------------------------------


def _load_participants_from_csv(
    csv_path: Path,
    output_dir: Path,
    force: bool,
) -> list[str]:
    """Return participants that need processing.

    Skips participants whose QSIPrep subject directory already exists in
    *output_dir* unless *force* is True.
    """
    df = load_sessions_from_csv(csv_path)
    if force:
        return sorted(df["subject_code"].unique())

    pending: list[str] = []
    for subject in df["subject_code"].unique():
        subject_dir = output_dir / "qsiprep" / f"sub-{subject}"
        if not subject_dir.exists():
            pending.append(subject)
        else:
            logger.debug("Skipping sub-%s: QSIPrep output already exists", subject)
    return sorted(pending)


def register_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the ``qsiprep`` subcommand."""
    parser = subparsers.add_parser(
        "qsiprep",
        description="Run QSIPrep diffusion MRI preprocessing.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help="Diffusion MRI preprocessing (QSIPrep)",
    )

    parser.add_argument(
        "--bids-dir",
        required=True,
        type=Path,
        help="BIDS dataset directory",
    )
    add_participant_args(parser)
    add_output_args(parser)

    # QSIPrep options
    parser.add_argument(
        "--bids-filters",
        type=Path,
        help="Path to BIDS filters JSON file",
    )
    parser.add_argument(
        "--fs-license",
        type=Path,
        help="Path to FreeSurfer license file",
    )
    parser.add_argument(
        "--output-resolution",
        type=float,
        default=1.6,
        help="Output resolution in mm",
    )
    parser.add_argument(
        "--nprocs",
        type=int,
        default=8,
        help="Number of parallel processes per QSIPrep run",
    )
    parser.add_argument(
        "--mem-mb",
        type=int,
        default=16000,
        help="Memory limit in MB per QSIPrep run",
    )
    parser.add_argument(
        "--skip-bids-validation",
        action="store_true",
        help="Skip BIDS validation inside QSIPrep",
    )
    parser.add_argument(
        "--docker-image",
        default="pennlinc/qsiprep:1.1.1",
        help="QSIPrep Docker image",
    )

    add_execution_args(parser, default_workers=4)
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the qsiprep subcommand."""
    configure_logging(args.log_level)

    bids_dir = Path(args.bids_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    log_dir = Path(args.log_dir).resolve() if args.log_dir else None
    work_dir = Path(args.work_dir).resolve() if args.work_dir else None

    if args.csv:
        participants = _load_participants_from_csv(args.csv, output_dir, args.force)
    else:
        participants = args.participants

    logger.info("Loaded %d participant(s) to process", len(participants))

    config = QSIPrepDefaults(
        nprocs=args.nprocs,
        mem_mb=args.mem_mb,
        output_resolution=args.output_resolution,
        skip_bids_validation=args.skip_bids_validation,
        fs_license=args.fs_license,
        docker_image=args.docker_image,
        force=args.force,
    )

    def process(participant: str) -> dict:
        logger.info("Starting sub-%s", participant)
        inputs = QSIPrepInputs(
            bids_dir=bids_dir,
            participant=participant,
            output_dir=output_dir,
            work_dir=work_dir,
            bids_filters=Path(args.bids_filters).resolve()
            if args.bids_filters
            else None,
        )
        if not args.force and check_last_execution_log(
            "qsiprep", participant, None, log_dir, inputs
        ):
            logger.info("Skipping sub-%s (already executed successfully)", participant)
            return {
                "participant": participant,
                "success": True,
                "duration_human": None,
                "output": None,
                "error": "Skipped (already executed successfully)",
            }
        result = run_procedure(
            procedure="qsiprep",
            inputs=inputs,
            config=config,
            log_dir=log_dir,
        )
        qsiprep_dir = None
        if result.execution:
            outputs = result.execution.get("expected_outputs")
            qsiprep_dir = str(getattr(outputs, "qsiprep_dir", "") or "")
        return {
            "participant": participant,
            "success": result.success,
            "duration_human": (
                result.execution.get("duration_human") if result.execution else None
            ),
            "output": qsiprep_dir,
            "error": result.get_failure_reason(),
        }

    results = run_parallel(
        items=participants,
        process_fn=process,
        max_workers=args.workers,
        label_fn=lambda p: f"sub-{p}",
    )
    return print_result_summary(results, id_fields=("participant",))
