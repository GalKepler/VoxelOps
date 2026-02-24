"""voxelops freesurfer — cortical reconstruction CLI subcommand."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from voxelops import FreeSurferDefaults, FreeSurferInputs, run_procedure
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
    parse_key_value_pairs,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CSV loading (freesurfer-specific: checks T1w existence + recon-all.done)
# ---------------------------------------------------------------------------


def _load_participants_from_csv(
    csv_path: Path,
    bids_dir: Path,
    output_dir: Path,
    force: bool,
    t1w_filters: dict[str, str] | None = None,
) -> list[str]:
    """Return participants that need processing.

    Skips participants that have no matching T1w data or whose
    ``recon-all.done`` flag already exists (unless *force*).
    """
    df = load_sessions_from_csv(csv_path)
    if force:
        return sorted(df["subject_code"].unique())

    pending: set[str] = set()
    for subject in df["subject_code"].unique():
        subject_dir = bids_dir / f"sub-{subject}"
        t1w_files = list(subject_dir.glob("**/anat/*_T1w.nii.gz"))
        if t1w_filters:
            t1w_files = [
                p
                for p in t1w_files
                if all(f"{k}-{v}" in p.name for k, v in t1w_filters.items())
            ]
        if not subject_dir.exists() or not t1w_files:
            logger.debug(
                "Skipping sub-%s: no matching T1w data found in BIDS dir", subject
            )
            continue
        done_flag = output_dir / f"sub-{subject}" / "scripts" / "recon-all.done"
        if not done_flag.exists():
            pending.add(subject)
        else:
            logger.debug("Skipping sub-%s: recon-all.done already exists", subject)

    return sorted(pending)


def register_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the ``freesurfer`` subcommand."""
    parser = subparsers.add_parser(
        "freesurfer",
        description="Run FreeSurfer recon-all cortical reconstruction.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help="Cortical reconstruction (FreeSurfer recon-all)",
    )

    parser.add_argument(
        "--bids-dir",
        required=True,
        type=Path,
        help="BIDS dataset directory",
    )
    add_participant_args(parser)
    add_output_args(parser)

    # FreeSurfer options
    parser.add_argument(
        "--fs-license",
        required=True,
        type=Path,
        help="Path to FreeSurfer license file (required)",
    )
    parser.add_argument(
        "--t1w-filters",
        nargs="+",
        metavar="KEY=VALUE",
        help=(
            "BIDS entity filters for T1w image selection (e.g. ce=corrected acq=mprage)"
        ),
    )
    parser.add_argument(
        "--t2w-filters",
        nargs="*",
        metavar="KEY=VALUE",
        help=(
            "BIDS entity filters to narrow T2w image selection. "
            "T2w is used by default; pass KEY=VALUE pairs to restrict. "
            "Use --no-t2w to disable T2w entirely."
        ),
    )
    parser.add_argument(
        "--no-t2w",
        action="store_true",
        help="Disable T2w detection and pial surface refinement",
    )
    parser.add_argument(
        "--flair-filters",
        nargs="*",
        metavar="KEY=VALUE",
        help=(
            "Enable FLAIR-enhanced pial refinement. "
            "Pass with no values to use any FLAIR, or KEY=VALUE to filter. "
            "FLAIR is disabled unless this flag is given."
        ),
    )
    parser.add_argument(
        "--nthreads",
        type=int,
        default=4,
        help="OpenMP threads per recon-all run (-openmp N)",
    )
    parser.add_argument(
        "--hires",
        action="store_true",
        help="Enable sub-millimetre processing (-hires)",
    )
    parser.add_argument(
        "--docker-image",
        default="freesurfer/freesurfer:8.1.0",
        help="FreeSurfer Docker image",
    )

    add_execution_args(parser, default_workers=2)
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the freesurfer subcommand."""
    configure_logging(args.log_level)

    bids_dir = Path(args.bids_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    log_dir = Path(args.log_dir).resolve() if args.log_dir else None
    work_dir = Path(args.work_dir).resolve() if args.work_dir else None

    t1w_filters = parse_key_value_pairs(args.t1w_filters, "--t1w-filters")

    # T2w: enabled by default (empty dict = auto-detect), disabled by --no-t2w
    if args.no_t2w:
        t2w_filters: dict[str, str] | None = None
    elif args.t2w_filters is not None:
        t2w_filters = parse_key_value_pairs(args.t2w_filters, "--t2w-filters") or {}
    else:
        t2w_filters = {}  # auto-detect any T2w

    # FLAIR: opt-in only
    flair_filters = parse_key_value_pairs(args.flair_filters, "--flair-filters")

    if t1w_filters:
        logger.info("Applying T1w filters: %s", t1w_filters)
    if t2w_filters is None:
        logger.info("T2w disabled (--no-t2w)")
    elif t2w_filters:
        logger.info("T2w enabled with filters: %s", t2w_filters)
    else:
        logger.info("T2w enabled (any T2w found will be used)")
    if flair_filters is not None:
        logger.info(
            "FLAIR enabled%s",
            f" with filters {flair_filters}" if flair_filters else "",
        )

    if args.csv:
        participants = _load_participants_from_csv(
            args.csv, bids_dir, output_dir, args.force, t1w_filters
        )
    else:
        participants = args.participants

    logger.info("Loaded %d participant(s) to process", len(participants))

    config = FreeSurferDefaults(
        nthreads=args.nthreads,
        hires=args.hires,
        fs_license=Path(args.fs_license).resolve(),
        docker_image=args.docker_image,
        force=args.force,
        use_t2pial=True,
        use_flairpial=True,
    )

    def process(participant: str) -> dict:
        logger.info("Starting sub-%s", participant)
        inputs = FreeSurferInputs(
            bids_dir=bids_dir,
            participant=participant,
            output_dir=output_dir,
            work_dir=work_dir,
            t1w_filters=t1w_filters,
            t2w_filters=t2w_filters,
            flair_filters=flair_filters,
        )
        if not args.force and check_last_execution_log(
            "freesurfer", participant, None, log_dir, inputs
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
            procedure="freesurfer",
            inputs=inputs,
            config=config,
            log_dir=log_dir,
        )
        subject_dir = None
        if result.execution:
            outputs = result.execution.get("expected_outputs")
            subject_dir = str(getattr(outputs, "subject_dir", "") or "")
        return {
            "participant": participant,
            "success": result.success,
            "duration_human": (
                result.execution.get("duration_human") if result.execution else None
            ),
            "output": subject_dir,
            "error": result.get_failure_reason(),
        }

    results = run_parallel(
        items=participants,
        process_fn=process,
        max_workers=args.workers,
        label_fn=lambda p: f"sub-{p}",
    )
    return print_result_summary(results, id_fields=("participant",))
