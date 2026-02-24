"""voxelops qsiparc — parcellation CLI subcommand."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from voxelops import QSIParcDefaults, QSIParcInputs, run_procedure
from voxelops.cli._common import (
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
# CSV loading (qsiparc-specific: extracts (participant, session) pairs)
# ---------------------------------------------------------------------------


def _load_pairs_from_csv(
    csv_path: Path,
    qsirecon_dir: Path,
    output_dir: Path,
    force: bool,
) -> list[tuple[str, str]]:
    """Return (participant, session) pairs that need processing.

    Only includes pairs whose QSIRecon subject directory exists.
    Skips pairs whose parcellation output already exists unless *force*.
    """
    df = load_sessions_from_csv(csv_path)
    pending: list[tuple[str, str]] = []

    for _, row in df.iterrows():
        subject = row["subject_code"]
        session = row["session_id"]

        if not (qsirecon_dir / f"sub-{subject}").exists():
            logger.debug("Skipping sub-%s: no QSIRecon output found", subject)
            continue

        if force:
            pending.append((subject, session))
            continue

        session_dir = output_dir / f"sub-{subject}" / f"ses-{session}"
        if not session_dir.exists():
            pending.append((subject, session))
        else:
            logger.debug(
                "Skipping sub-%s ses-%s: parcellation output already exists",
                subject,
                session,
            )

    return sorted(pending)


def register_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the ``qsiparc`` subcommand."""
    parser = subparsers.add_parser(
        "qsiparc",
        description="Run QSIParc parcellation on QSIRecon outputs.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help="Tractography parcellation (QSIParc)",
    )

    parser.add_argument(
        "--qsirecon-dir",
        required=True,
        type=Path,
        help="QSIRecon derivatives directory",
    )
    add_participant_args(parser)

    parser.add_argument(
        "--session",
        metavar="SESSION_ID",
        default=None,
        help=(
            "Session label (without 'ses-' prefix) to process. "
            "Ignored when --csv is used (session comes from the CSV)."
        ),
    )

    add_output_args(parser, work_dir=False)

    # QSIParc options
    parser.add_argument(
        "--atlases",
        nargs="+",
        metavar="ATLAS",
        help="Atlas names to parcellate (overrides auto-discovery from QSIRecon outputs)",
    )
    parser.add_argument(
        "--mask",
        default="gm",
        help="Mask to apply: 'gm', 'wm', 'brain', or path to a mask file",
    )
    parser.add_argument(
        "--resampling-target",
        default="data",
        choices=["data", "labels", "atlas"],
        help="Resampling strategy",
    )
    parser.add_argument(
        "--n-jobs",
        type=int,
        default=1,
        help="Number of parallel jobs per parcellation run",
    )
    parser.add_argument(
        "--n-procs",
        type=int,
        default=1,
        help="Number of processors per parcellation run",
    )

    add_execution_args(parser, default_workers=4)
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the qsiparc subcommand."""
    configure_logging(args.log_level)

    qsirecon_dir = Path(args.qsirecon_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    log_dir = Path(args.log_dir).resolve() if args.log_dir else None

    if args.csv:
        pairs = _load_pairs_from_csv(args.csv, qsirecon_dir, output_dir, args.force)
    else:
        pairs = [(p, args.session) for p in args.participants]

    logger.info("Loaded %d pair(s) to process", len(pairs))

    config = QSIParcDefaults(
        mask=args.mask,
        resampling_target=args.resampling_target,
        n_jobs=args.n_jobs,
        n_procs=args.n_procs,
        force=args.force,
    )

    def process(pair: tuple[str, str | None]) -> dict:
        participant, session = pair
        label = f"sub-{participant}" + (f" ses-{session}" if session else "")
        logger.info("Starting %s", label)

        inputs = QSIParcInputs(
            qsirecon_dir=qsirecon_dir,
            participant=participant,
            output_dir=output_dir,
            session=session,
            n_jobs=args.n_jobs,
            n_procs=args.n_procs,
        )
        result = run_procedure(
            procedure="qsiparc",
            inputs=inputs,
            config=config,
            log_dir=log_dir,
        )
        output_path = None
        if result.execution:
            outputs = result.execution.get("expected_outputs")
            output_path = str(getattr(outputs, "output_dir", "") or "")
        return {
            "participant": participant,
            "session": session,
            "success": result.success,
            "duration_human": (
                result.execution.get("duration_human") if result.execution else None
            ),
            "output": output_path,
            "error": result.get_failure_reason(),
        }

    def label_fn(pair: tuple[str, str | None]) -> str:
        p, s = pair
        return f"sub-{p}" + (f" ses-{s}" if s else "")

    results = run_parallel(
        items=pairs,
        process_fn=process,
        max_workers=args.workers,
        label_fn=label_fn,
    )
    return print_result_summary(results, id_fields=("participant", "session"))
