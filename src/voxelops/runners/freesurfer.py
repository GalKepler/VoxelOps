"""FreeSurfer cortical reconstruction runner (recon-all)."""

import logging
from pathlib import Path
from typing import Any

from voxelops.runners._base import (
    _get_default_log_dir,
    run_docker,
    validate_input_dir,
    validate_participant,
)
from voxelops.schemas.freesurfer import (
    FreeSurferBaseInputs,
    FreeSurferBaseOutputs,
    FreeSurferDefaults,
    FreeSurferInputs,
    FreeSurferOutputs,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Image discovery helpers
# ---------------------------------------------------------------------------


def _discover_weighted_files(
    bids_dir: Path,
    participant: str,
    suffix: str,
    session: str | None = None,
    filters: dict[str, str] | None = None,
) -> list[Path]:
    """Return NIfTI images for a given BIDS suffix, optionally filtered.

    Parameters
    ----------
    bids_dir : Path
        Root of the BIDS dataset.
    participant : str
        Participant label (without 'sub-' prefix).
    suffix : str
        BIDS suffix, e.g. ``"T1w"`` or ``"T2w"``.
    session : str, optional
        When set, only search under ``ses-{session}/anat/``.
    filters : dict[str, str], optional
        BIDS entity key-value pairs that must appear as ``key-value`` in
        the filename (e.g. ``{"ce": "corrected"}``).

    Returns
    -------
    list[Path]
        Sorted list of matching absolute NIfTI paths.
    """
    if session:
        search_root = bids_dir / f"sub-{participant}" / f"ses-{session}"
    else:
        search_root = bids_dir / f"sub-{participant}"

    candidates = sorted(search_root.glob(f"**/anat/*_{suffix}.nii.gz"))
    if not filters:
        return candidates
    return [
        p
        for p in candidates
        if all(f"{key}-{value}" in p.name for key, value in filters.items())
    ]


def _discover_t1w_files(
    bids_dir: Path,
    participant: str,
    session: str | None = None,
    t1w_filters: dict[str, str] | None = None,
) -> list[Path]:
    """Return T1w images for a participant, optionally filtered."""
    return _discover_weighted_files(bids_dir, participant, "T1w", session, t1w_filters)


def _discover_t2w_files(
    bids_dir: Path,
    participant: str,
    session: str | None = None,
    t2w_filters: dict[str, str] | None = None,
) -> list[Path]:
    """Return T2w images for a participant, optionally filtered.

    Only the first match is used when passed to recon-all (FreeSurfer
    accepts a single T2w).  A warning is logged when more than one file
    is found so the user knows which one was selected.
    """
    return _discover_weighted_files(bids_dir, participant, "T2w", session, t2w_filters)


def _discover_flair_files(
    bids_dir: Path,
    participant: str,
    session: str | None = None,
    flair_filters: dict[str, str] | None = None,
) -> list[Path]:
    """Return FLAIR images for a participant, optionally filtered.

    Only the first match is used (same single-image convention as T2w).
    """
    return _discover_weighted_files(
        bids_dir, participant, "FLAIR", session, flair_filters
    )


# ---------------------------------------------------------------------------
# Docker command builders
# ---------------------------------------------------------------------------


def _base_docker_cmd(config: FreeSurferDefaults) -> list[str]:
    """Return the common ``docker run`` preamble shared by both commands."""
    cmd = [
        "docker",
        "run",
        "--rm",
    ]
    if config.fs_license and config.fs_license.exists():
        cmd.extend(
            [
                "-e",
                "FS_LICENSE=/opt/fs_license.txt",
                "-v",
                f"{config.fs_license}:/opt/fs_license.txt:ro",
            ]
        )
    return cmd


def _build_freesurfer_docker_command(
    inputs: FreeSurferInputs,
    config: FreeSurferDefaults,
    subjects_dir: Path,
    t1w_files: list[Path],
    t2w_file: Path | None,
    flair_file: Path | None,
) -> list[str]:
    """Build the ``docker run recon-all`` command for a single timepoint.

    Parameters
    ----------
    inputs : FreeSurferInputs
    config : FreeSurferDefaults
    subjects_dir : Path
        Resolved FreeSurfer SUBJECTS_DIR (maps to ``/output``).
    t1w_files : list[Path]
        Host paths to T1w images; multiple are averaged by FreeSurfer.
    t2w_file : Path or None
        Host path to the T2w image, or ``None`` to skip T2w processing.
    flair_file : Path or None
        Host path to the FLAIR image, or ``None`` to skip FLAIR processing.

    Raises
    ------
    ValueError
        If no T1w images were found.
    """
    if not t1w_files:
        filter_hint = (
            f" matching filters {inputs.t1w_filters}" if inputs.t1w_filters else ""
        )
        raise ValueError(
            f"No T1w images found{filter_hint} for "
            f"{inputs.subject_label} in {inputs.bids_dir}"
        )

    cmd = _base_docker_cmd(config)
    cmd.extend(
        [
            "-v",
            f"{inputs.bids_dir}:/data:ro",
            "-v",
            f"{subjects_dir}:/output",
            config.docker_image,
            "recon-all",
            "-subject",
            inputs.subject_label,
            "-sd",
            "/output",
            "-all",
            "-parallel",
            "-openmp",
            str(config.nthreads),
        ]
    )

    for t1w in t1w_files:
        relative = t1w.relative_to(inputs.bids_dir)
        cmd.extend(["-i", f"/data/{relative}"])

    if t2w_file is not None:
        relative_t2w = t2w_file.relative_to(inputs.bids_dir)
        cmd.extend(["-T2", f"/data/{relative_t2w}"])
        if config.use_t2pial:
            cmd.append("-T2pial")

    if flair_file is not None:
        relative_flair = flair_file.relative_to(inputs.bids_dir)
        cmd.extend(["-FLAIR", f"/data/{relative_flair}"])
        if config.use_flairpial:
            cmd.append("-FLAIRpial")

    if config.hires:
        cmd.append("-hires")

    return cmd


def _build_freesurfer_base_docker_command(
    inputs: FreeSurferBaseInputs,
    config: FreeSurferDefaults,
) -> list[str]:
    """Build the ``docker run recon-all -base`` command for the longitudinal template.

    FreeSurfer's longitudinal stream creates an unbiased within-subject
    template by averaging all timepoints::

        recon-all -base sub-{participant}_base \\
                  -tp sub-{participant}_ses-{ses1} \\
                  -tp sub-{participant}_ses-{ses2} ... \\
                  -all -sd /output

    Each ``-tp`` argument references an existing subject directory
    inside SUBJECTS_DIR that was produced by a prior ``run_freesurfer``
    call with the matching session label.

    Parameters
    ----------
    inputs : FreeSurferBaseInputs
    config : FreeSurferDefaults

    Raises
    ------
    ValueError
        If no sessions are listed.
    """
    if not inputs.sessions:
        raise ValueError(
            f"No sessions provided for longitudinal base template of {inputs.participant}"
        )

    cmd = _base_docker_cmd(config)
    cmd.extend(
        [
            "-v",
            f"{inputs.subjects_dir}:/output",
            config.docker_image,
            "recon-all",
            "-base",
            inputs.base_label,
            "-sd",
            "/output",
        ]
    )

    for tp_label in inputs.timepoint_labels:
        cmd.extend(["-tp", tp_label])

    cmd.extend(
        [
            "-all",
            "-parallel",
            "-openmp",
            str(config.nthreads),
        ]
    )

    return cmd


# ---------------------------------------------------------------------------
# Public runners
# ---------------------------------------------------------------------------


def run_freesurfer(
    inputs: FreeSurferInputs,
    config: FreeSurferDefaults | None = None,
    log_dir: Path | None = None,
    **overrides,
) -> dict[str, Any]:
    """Run FreeSurfer recon-all for a single participant (or timepoint).

    Parameters
    ----------
    inputs : FreeSurferInputs
        Required inputs.  Set ``inputs.session`` to enable longitudinal
        per-timepoint naming (``sub-{participant}_ses-{session}``).
        Set ``inputs.t2w_filters`` to a dict (even ``{}``) to activate
        T2w discovery and pial-surface refinement.
    config : FreeSurferDefaults, optional
        Configuration; uses defaults when not provided.
    log_dir : Path, optional
        Directory for audit logs.
    **overrides
        Override any ``FreeSurferDefaults`` field by name.

    Returns
    -------
    dict[str, Any]
        Execution record (see source for full key list).

    Examples
    --------
    Cross-sectional, T2w-enhanced::

        inputs = FreeSurferInputs(
            bids_dir=Path("/data/bids"),
            participant="01",
            t2w_filters={"ce": "corrected"},
        )
        result = run_freesurfer(inputs, config)

    Longitudinal timepoint::

        inputs = FreeSurferInputs(
            bids_dir=Path("/data/bids"),
            participant="01",
            session="baseline",
            t1w_filters={"ce": "corrected"},
        )
        result = run_freesurfer(inputs, config)
    """
    log_dir = log_dir or _get_default_log_dir(inputs)
    config = config or FreeSurferDefaults()

    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)

    validate_input_dir(inputs.bids_dir, "BIDS")
    validate_participant(inputs.bids_dir, inputs.participant)

    output_dir = inputs.output_dir or (
        inputs.bids_dir.parent / "derivatives" / "freesurfer"
    )
    work_dir = inputs.work_dir or (output_dir.parent / "work" / "freesurfer")
    output_dir.mkdir(parents=True, exist_ok=True)
    work_dir.mkdir(parents=True, exist_ok=True)

    expected_outputs = FreeSurferOutputs.from_inputs(inputs, output_dir, work_dir)

    if expected_outputs.exist() and not config.force:
        print("\n" + "=" * 80)
        print(f"✓ FreeSurfer outputs already exist for {inputs.subject_label}")
        print(f"  Subject dir: {expected_outputs.subject_dir}")
        print(f"  Done flag:   {expected_outputs.recon_done_flag}")
        print("  Use force=True to re-run")
        print("=" * 80 + "\n")
        return {
            "tool": "freesurfer",
            "participant": inputs.participant,
            "skipped": True,
            "reason": "outputs_exist",
            "success": True,
            "inputs": inputs,
            "config": config,
            "expected_outputs": expected_outputs,
        }

    # Discover T1w images
    t1w_files = _discover_t1w_files(
        inputs.bids_dir, inputs.participant, inputs.session, inputs.t1w_filters
    )

    # Discover T2w image (only when t2w_filters is not None)
    t2w_file: Path | None = None
    if inputs.t2w_filters is not None:
        t2w_files = _discover_t2w_files(
            inputs.bids_dir, inputs.participant, inputs.session, inputs.t2w_filters
        )
        if t2w_files:
            t2w_file = t2w_files[0]
            if len(t2w_files) > 1:
                logger.warning(
                    "Multiple T2w images found for %s; using %s",
                    inputs.subject_label,
                    t2w_file.name,
                )
        else:
            filter_hint = (
                f" matching filters {inputs.t2w_filters}" if inputs.t2w_filters else ""
            )
            logger.warning(
                "No T2w images found%s for %s — running without T2w",
                filter_hint,
                inputs.subject_label,
            )

    # Discover FLAIR image (only when flair_filters is not None)
    flair_file: Path | None = None
    if inputs.flair_filters is not None:
        flair_files = _discover_flair_files(
            inputs.bids_dir, inputs.participant, inputs.session, inputs.flair_filters
        )
        if flair_files:
            flair_file = flair_files[0]
            if len(flair_files) > 1:
                logger.warning(
                    "Multiple FLAIR images found for %s; using %s",
                    inputs.subject_label,
                    flair_file.name,
                )
        else:
            filter_hint = (
                f" matching filters {inputs.flair_filters}"
                if inputs.flair_filters
                else ""
            )
            logger.warning(
                "No FLAIR images found%s for %s — running without FLAIR",
                filter_hint,
                inputs.subject_label,
            )

    cmd = _build_freesurfer_docker_command(
        inputs, config, output_dir, t1w_files, t2w_file, flair_file
    )

    result = run_docker(
        cmd=cmd,
        tool_name="freesurfer",
        participant=inputs.participant,
        log_dir=log_dir,
    )

    result["inputs"] = inputs
    result["config"] = config
    result["expected_outputs"] = expected_outputs
    result["skipped"] = False

    return result


def run_freesurfer_base(
    inputs: FreeSurferBaseInputs,
    config: FreeSurferDefaults | None = None,
    log_dir: Path | None = None,
    **overrides,
) -> dict[str, Any]:
    """Create a FreeSurfer within-subject longitudinal base template.

    This is step 2 of FreeSurfer's longitudinal pipeline.  It must be
    run **after** :func:`run_freesurfer` has been called once per
    session (step 1), and **before** per-timepoint longitudinal
    re-processing (step 3, not yet implemented here).

    The command executed inside the container is::

        recon-all -base sub-{participant}_base \\
                  -tp sub-{participant}_ses-{ses1} \\
                  -tp sub-{participant}_ses-{ses2} ... \\
                  -all -sd /output

    Parameters
    ----------
    inputs : FreeSurferBaseInputs
        ``subjects_dir``, ``participant``, and the list of ``sessions``
        to include as timepoints.
    config : FreeSurferDefaults, optional
        Shared configuration (same image, licence, thread count as the
        per-session runs).
    log_dir : Path, optional
        Directory for audit logs.
    **overrides
        Override any ``FreeSurferDefaults`` field by name.

    Returns
    -------
    dict[str, Any]
        Execution record.  ``expected_outputs`` is a
        :class:`FreeSurferBaseOutputs` instance.

    Examples
    --------
    ::

        base_inputs = FreeSurferBaseInputs(
            subjects_dir=Path("/data/derivatives/freesurfer"),
            participant="01",
            sessions=["baseline", "followup"],
        )
        result = run_freesurfer_base(base_inputs, config)
        print(result["expected_outputs"].base_subject_dir)
    """
    log_dir = log_dir or (inputs.subjects_dir.parent / "logs")
    config = config or FreeSurferDefaults()

    for key, value in overrides.items():
        if hasattr(config, key):
            setattr(config, key, value)

    # Verify all timepoint directories already exist
    missing = [
        tp for tp in inputs.timepoint_labels if not (inputs.subjects_dir / tp).exists()
    ]
    if missing:
        raise ValueError(
            f"Missing timepoint directories for {inputs.participant}: {missing}. "
            "Run run_freesurfer for each session first."
        )

    expected_outputs = FreeSurferBaseOutputs.from_inputs(inputs)

    if expected_outputs.exist() and not config.force:
        print("\n" + "=" * 80)
        print(f"✓ FreeSurfer base template already exists for {inputs.participant}")
        print(f"  Base dir:  {expected_outputs.base_subject_dir}")
        print(f"  Done flag: {expected_outputs.recon_done_flag}")
        print("  Use force=True to re-run")
        print("=" * 80 + "\n")
        return {
            "tool": "freesurfer_base",
            "participant": inputs.participant,
            "skipped": True,
            "reason": "outputs_exist",
            "success": True,
            "inputs": inputs,
            "config": config,
            "expected_outputs": expected_outputs,
        }

    cmd = _build_freesurfer_base_docker_command(inputs, config)

    result = run_docker(
        cmd=cmd,
        tool_name="freesurfer_base",
        participant=inputs.participant,
        log_dir=log_dir,
    )

    result["inputs"] = inputs
    result["config"] = config
    result["expected_outputs"] = expected_outputs
    result["skipped"] = False

    return result
