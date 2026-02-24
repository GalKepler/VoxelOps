"""voxelops qsirecon — diffusion reconstruction & connectivity CLI subcommand."""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

from voxelops import QSIReconDefaults, QSIReconInputs, run_procedure
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
# CSV loading (qsirecon-specific: needs QSIPrep-dir check + output-dir skip)
# ---------------------------------------------------------------------------


def _load_pairs_from_csv(
    csv_path: Path,
    qsiprep_dir: Path,
    output_dir: Path,
    force: bool,
) -> list[tuple[str, str]]:
    """Return (participant, session) pairs that need processing.

    Only returns pairs whose QSIPrep subject directory exists.  Pairs whose
    QSIRecon session directory already exists are skipped unless *force*.
    """
    df = load_sessions_from_csv(csv_path)
    pending: list[tuple[str, str]] = []

    for _, row in df.iterrows():
        subject = row["subject_code"]
        session = row["session_id"]

        if not (qsiprep_dir / f"sub-{subject}").exists():
            logger.debug("Skipping sub-%s: no QSIPrep output found", subject)
            continue

        if force:
            pending.append((subject, session))
            continue

        session_dir = output_dir / f"sub-{subject}" / f"ses-{session}"
        if not session_dir.exists():
            pending.append((subject, session))
        else:
            logger.debug(
                "Skipping sub-%s ses-%s: QSIRecon output already exists",
                subject,
                session,
            )

    return sorted(pending)


def register_parser(subparsers: argparse._SubParsersAction) -> None:  # type: ignore[type-arg]
    """Register the ``qsirecon`` subcommand."""
    parser = subparsers.add_parser(
        "qsirecon",
        description="Run QSIRecon diffusion reconstruction and connectivity.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        help="Diffusion reconstruction & connectivity (QSIRecon)",
    )

    parser.add_argument(
        "--qsiprep-dir",
        required=True,
        type=Path,
        help="QSIPrep derivatives directory",
    )
    add_participant_args(parser)

    # Session filter (only meaningful with --participants)
    parser.add_argument(
        "--session",
        metavar="SESSION_ID",
        default=None,
        help=(
            "Session label (without 'ses-' prefix). "
            "Passed as --session-id to QSIRecon. "
            "When omitted, all sessions are processed together. "
            "Ignored when --csv is used (session comes from the CSV)."
        ),
    )

    add_output_args(parser)

    # QSIRecon options
    parser.add_argument(
        "--recon-spec",
        type=Path,
        help="Path to reconstruction spec YAML file",
    )
    parser.add_argument(
        "--recon-spec-aux-files",
        type=Path,
        metavar="DIR",
        help=(
            "Directory containing auxiliary files referenced by the recon spec "
            "(e.g. MRtrix3 response functions). "
            "Mounted into the container at /<dirname>."
        ),
    )
    parser.add_argument(
        "--datasets",
        nargs="+",
        metavar="NAME=PATH",
        help="Extra datasets to mount, e.g. atlases=/path/to/atlases",
    )
    parser.add_argument(
        "--atlases",
        nargs="+",
        metavar="ATLAS",
        help="Atlas names to pass via --atlases (overrides QSIReconInputs defaults)",
    )
    parser.add_argument(
        "--fs-license",
        type=Path,
        help="Path to FreeSurfer license file",
    )
    parser.add_argument(
        "--fs-subjects-dir",
        type=Path,
        metavar="DIR",
        help="FreeSurfer subjects directory",
    )
    parser.add_argument(
        "--nprocs",
        type=int,
        default=8,
        help="Number of parallel processes per QSIRecon run",
    )
    parser.add_argument(
        "--mem-mb",
        type=int,
        default=16000,
        help="Memory limit in MB per QSIRecon run",
    )
    parser.add_argument(
        "--docker-image",
        default="pennlinc/qsirecon:1.2.0",
        help="QSIRecon Docker image",
    )

    add_execution_args(parser, default_workers=4)
    parser.set_defaults(func=run)


def run(args: argparse.Namespace) -> int:
    """Execute the qsirecon subcommand."""
    configure_logging(args.log_level)

    qsiprep_dir = Path(args.qsiprep_dir).resolve()
    output_dir = Path(args.output_dir).resolve()
    log_dir = Path(args.log_dir).resolve() if args.log_dir else None
    work_dir = Path(args.work_dir).resolve() if args.work_dir else None
    recon_spec = Path(args.recon_spec).resolve() if args.recon_spec else None
    recon_spec_aux = (
        Path(args.recon_spec_aux_files).resolve() if args.recon_spec_aux_files else None
    )

    datasets_raw = parse_key_value_pairs(args.datasets, "--datasets")
    datasets = (
        {k: Path(v).resolve() for k, v in datasets_raw.items()}
        if datasets_raw
        else None
    )

    if args.csv:
        pairs = _load_pairs_from_csv(args.csv, qsiprep_dir, output_dir, args.force)
    else:
        pairs = [(p, args.session) for p in args.participants]

    logger.info("Loaded %d pair(s) to process", len(pairs))

    config = QSIReconDefaults(
        nprocs=args.nprocs,
        mem_mb=args.mem_mb,
        fs_license=args.fs_license,
        fs_subjects_dir=args.fs_subjects_dir,
        docker_image=args.docker_image,
        force=args.force,
    )

    def process(pair: tuple[str, str | None]) -> dict:
        participant, session = pair
        label = f"sub-{participant}" + (f" ses-{session}" if session else "")
        logger.info("Starting %s", label)

        inputs_kwargs: dict = {
            "qsiprep_dir": qsiprep_dir,
            "participant": participant,
            "session": session,
            "output_dir": output_dir,
            "work_dir": work_dir,
            "recon_spec": recon_spec,
            "recon_spec_aux_files": recon_spec_aux,
            "datasets": datasets,
        }
        if args.atlases is not None:
            inputs_kwargs["atlases"] = args.atlases

        inputs = QSIReconInputs(**inputs_kwargs)

        if not args.force and check_last_execution_log(
            "qsirecon", participant, session, log_dir, inputs
        ):
            logger.info("Skipping %s (already executed successfully)", label)
            return {
                "participant": participant,
                "session": session,
                "success": True,
                "duration_human": None,
                "output": None,
                "error": "Skipped (already executed successfully)",
            }
        result = run_procedure(
            procedure="qsirecon",
            inputs=inputs,
            config=config,
            log_dir=log_dir,
        )
        qsirecon_dir = None
        if result.execution:
            outputs = result.execution.get("expected_outputs")
            qsirecon_dir = str(getattr(outputs, "qsirecon_dir", "") or "")
        return {
            "participant": participant,
            "session": session,
            "success": result.success,
            "duration_human": (
                result.execution.get("duration_human") if result.execution else None
            ),
            "output": qsirecon_dir,
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
