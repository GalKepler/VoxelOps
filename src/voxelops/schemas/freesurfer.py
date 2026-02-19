"""FreeSurfer schemas: inputs, outputs, and defaults."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class FreeSurferInputs:
    """Required inputs for FreeSurfer cortical reconstruction (recon-all).

    Parameters
    ----------
    bids_dir : Path
        BIDS dataset directory.  T1w and optionally T2w/FLAIR images are
        discovered automatically under
        ``sub-{participant}/**/anat/*_T1w.nii.gz``.
    participant : str
        Participant label (without 'sub-' prefix).
    session : str, optional
        Session label (without 'ses-' prefix).  When provided:

        - Image discovery is narrowed to
          ``sub-{participant}/ses-{session}/anat/``.
        - The FreeSurfer subject label becomes
          ``sub-{participant}_ses-{session}`` so each timepoint gets its
          own entry in SUBJECTS_DIR — a prerequisite for the longitudinal
          base-template step.

        Leave ``None`` for single-session / cross-sectional datasets.
    output_dir : Path, optional
        FreeSurfer subjects directory (SUBJECTS_DIR).  Defaults to
        ``bids_dir/../derivatives/freesurfer``.
    work_dir : Path, optional
        Scratch / working directory (not used by recon-all itself, kept
        for framework consistency).  Defaults to
        ``output_dir/../work/freesurfer``.
    t1w_filters : dict[str, str], optional
        BIDS entity filters for T1w discovery.  Each key-value pair must
        appear as ``key-value`` in the filename.  Example:
        ``{"ce": "corrected"}`` selects only ``*_ce-corrected_T1w.nii.gz``
        files.
    t2w_filters : dict[str, str], optional
        BIDS entity filters for T2w discovery.  Same format as
        ``t1w_filters``.  When T2w images are found they are passed to
        recon-all via ``-T2``; only the first match is used.  Set to
        ``{}`` (empty dict) to use any T2w without filtering.
        ``None`` (default) disables T2w entirely.
    flair_filters : dict[str, str], optional
        BIDS entity filters for FLAIR discovery (``*_FLAIR.nii.gz``).
        Same opt-in semantics as ``t2w_filters``: ``None`` disables FLAIR,
        ``{}`` uses the first FLAIR found, a non-empty dict further
        narrows by entity (e.g. ``{"acq": "sag"}``).  Passed to
        recon-all via ``-FLAIR``.  Prefer T2w over FLAIR when both are
        available — FreeSurfer recommends using only one for pial
        refinement.
    """

    bids_dir: Path
    participant: str
    session: str | None = None
    output_dir: Path | None = None
    work_dir: Path | None = None
    t1w_filters: dict[str, str] | None = None
    t2w_filters: dict[str, str] | None = None
    flair_filters: dict[str, str] | None = None

    def __post_init__(self):
        """Ensure paths are Path objects."""
        self.bids_dir = Path(self.bids_dir)
        if self.output_dir:
            self.output_dir = Path(self.output_dir)
        if self.work_dir:
            self.work_dir = Path(self.work_dir)

    @property
    def subject_label(self) -> str:
        """FreeSurfer subject label used in SUBJECTS_DIR.

        Returns ``sub-{participant}_ses-{session}`` when a session is set,
        otherwise ``sub-{participant}``.
        """
        # if self.session:
        #     return f"sub-{self.participant}_ses-{self.session}"
        return f"sub-{self.participant}"


@dataclass
class FreeSurferOutputs:
    """Expected outputs from a FreeSurfer recon-all run.

    Parameters
    ----------
    subjects_dir : Path
        FreeSurfer SUBJECTS_DIR (equals ``output_dir`` from inputs).
    subject_dir : Path
        Per-subject directory: ``subjects_dir/{subject_label}``.
    mri_dir : Path
        ``subject_dir/mri`` — volumetric reconstructions.
    surf_dir : Path
        ``subject_dir/surf`` — surface files.
    stats_dir : Path
        ``subject_dir/stats`` — parcellation statistics.
    recon_done_flag : Path
        ``subject_dir/scripts/recon-all.done`` — written by FreeSurfer
        only after a fully successful run.
    """

    subjects_dir: Path
    subject_dir: Path
    mri_dir: Path
    surf_dir: Path
    stats_dir: Path
    recon_done_flag: Path

    def exist(self) -> bool:
        """Return True when the run completed successfully.

        Checks for the ``recon-all.done`` flag **and** the ``mri/``
        directory.
        """
        return self.recon_done_flag.exists() and self.mri_dir.exists()

    def to_dict(self) -> dict[str, Any]:
        """Convert to a JSON-serialisable dictionary."""
        return {
            "subjects_dir": str(self.subjects_dir),
            "subject_dir": str(self.subject_dir),
            "mri_dir": str(self.mri_dir),
            "surf_dir": str(self.surf_dir),
            "stats_dir": str(self.stats_dir),
            "recon_done_flag": str(self.recon_done_flag),
        }

    @classmethod
    def from_inputs(
        cls, inputs: "FreeSurferInputs", output_dir: Path, work_dir: Path
    ) -> "FreeSurferOutputs":
        """Generate expected output paths from inputs."""
        subjects_dir = output_dir
        subject_dir = subjects_dir / inputs.subject_label
        return cls(
            subjects_dir=subjects_dir,
            subject_dir=subject_dir,
            mri_dir=subject_dir / "mri",
            surf_dir=subject_dir / "surf",
            stats_dir=subject_dir / "stats",
            recon_done_flag=subject_dir / "scripts" / "recon-all.done",
        )


@dataclass
class FreeSurferBaseInputs:
    """Inputs for the FreeSurfer longitudinal base-template step.

    After each session has been processed individually with
    :func:`run_freesurfer` (producing
    ``sub-{participant}_ses-{session}`` entries in SUBJECTS_DIR), this
    creates an unbiased within-subject template by running::

        recon-all -base sub-{participant}_base \\
                  -tp sub-{participant}_ses-{ses1} \\
                  -tp sub-{participant}_ses-{ses2} ... \\
                  -all -sd /output

    Parameters
    ----------
    subjects_dir : Path
        The FreeSurfer SUBJECTS_DIR that already contains the processed
        per-session timepoints.
    participant : str
        Participant label (without 'sub-' prefix).
    sessions : list[str]
        Session labels (without 'ses-' prefix) to include as timepoints.
        Each must correspond to an existing
        ``sub-{participant}_ses-{session}`` directory in
        ``subjects_dir``.
    """

    subjects_dir: Path
    participant: str
    sessions: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.subjects_dir = Path(self.subjects_dir)

    @property
    def output_dir(self) -> Path:
        """Alias for ``subjects_dir`` (for framework log-dir compatibility)."""
        return self.subjects_dir

    @property
    def base_label(self) -> str:
        """FreeSurfer label for the base template subject."""
        return f"sub-{self.participant}_base"

    @property
    def timepoint_labels(self) -> list[str]:
        """FreeSurfer labels for each individual timepoint."""
        return [f"sub-{self.participant}_ses-{s}" for s in self.sessions]


@dataclass
class FreeSurferBaseOutputs:
    """Expected outputs from a FreeSurfer longitudinal base-template run.

    Parameters
    ----------
    subjects_dir : Path
        FreeSurfer SUBJECTS_DIR.
    base_subject_dir : Path
        ``subjects_dir/sub-{participant}_base``.
    mri_dir : Path
        ``base_subject_dir/mri``.
    recon_done_flag : Path
        ``base_subject_dir/scripts/recon-all.done``.
    """

    subjects_dir: Path
    base_subject_dir: Path
    mri_dir: Path
    recon_done_flag: Path

    def exist(self) -> bool:
        """Return True when the base-template run completed successfully."""
        return self.recon_done_flag.exists() and self.mri_dir.exists()

    def to_dict(self) -> dict[str, Any]:
        """Convert to a JSON-serialisable dictionary."""
        return {
            "subjects_dir": str(self.subjects_dir),
            "base_subject_dir": str(self.base_subject_dir),
            "mri_dir": str(self.mri_dir),
            "recon_done_flag": str(self.recon_done_flag),
        }

    @classmethod
    def from_inputs(cls, inputs: "FreeSurferBaseInputs") -> "FreeSurferBaseOutputs":
        """Generate expected output paths from inputs."""
        base_subject_dir = inputs.subjects_dir / inputs.base_label
        return cls(
            subjects_dir=inputs.subjects_dir,
            base_subject_dir=base_subject_dir,
            mri_dir=base_subject_dir / "mri",
            recon_done_flag=base_subject_dir / "scripts" / "recon-all.done",
        )


@dataclass
class FreeSurferDefaults:
    """Default configuration for FreeSurfer recon-all.

    Parameters
    ----------
    nthreads : int, optional
        OpenMP thread count passed via ``-openmp``, by default 4.
    hires : bool, optional
        Enable sub-millimetre processing (``-hires``), by default False.
    use_t2pial : bool, optional
        When a T2w image is found, pass ``-T2pial`` in addition to
        ``-T2`` so FreeSurfer refines the pial surface using the T2w.
        Set to ``False`` to use the T2w for bias-field correction only.
        Default is ``True``.
    use_flairpial : bool, optional
        When a FLAIR image is found, pass ``-FLAIRpial`` in addition to
        ``-FLAIR``.  Same semantics as ``use_t2pial``.  Default is
        ``True``.
    fs_license : Path, optional
        Path to a valid FreeSurfer licence file.  Required — recon-all
        will abort immediately without it.
    docker_image : str, optional
        Docker image, by default ``"freesurfer/freesurfer:8.1.0"``.
    force : bool, optional
        Re-run even when ``recon-all.done`` already exists, by default
        False.

    Notes
    -----
    The container is launched with ``--user uid:gid`` so output files are
    owned by the calling user.  A ``--tmpfs /tmp`` mount is added
    automatically to give FreeSurfer's startup scripts a writable scratch
    space inside the container.
    """

    nthreads: int = 4
    hires: bool = False
    use_t2pial: bool = True
    use_flairpial: bool = True
    fs_license: Path | None = None
    docker_image: str = "freesurfer/freesurfer:8.1.0"
    force: bool = False

    def __post_init__(self):
        """Ensure fs_license is a Path object if provided."""
        if self.fs_license:
            self.fs_license = Path(self.fs_license)
