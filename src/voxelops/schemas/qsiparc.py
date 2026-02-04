"""QSIParc schemas: inputs, outputs, and defaults."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from parcellate.interfaces.models import AtlasDefinition


@dataclass
class QSIParcInputs:
    """Required inputs for QSIParc parcellation.

    Parameters
    ----------
    qsirecon_dir : Path
        QSIRecon output directory.
    participant : str
        Participant label (without 'sub-' prefix).
    output_dir : Optional[Path], optional
        Output directory, by default None.
        If None, defaults to qsirecon_dir parent.
    session : Optional[str], optional
        Session label (without 'ses-' prefix), by default None.
    atlases : Optional[list[AtlasDefinition]], optional
        List of atlas definitions, by default None.
    n_jobs : Optional[int], optional
        Number of jobs to run in parallel, by default None.
    n_procs : Optional[int], optional
        Number of processors to use, by default None.
    """

    qsirecon_dir: Path
    participant: str
    output_dir: Path | None = None
    session: str | None = None
    atlases: list[AtlasDefinition] | None = None
    n_jobs: int | None = None
    n_procs: int | None = None

    def __post_init__(self):
        """Ensure paths are Path objects."""
        self.qsirecon_dir = Path(self.qsirecon_dir)
        if self.output_dir:
            self.output_dir = Path(self.output_dir)


@dataclass
class QSIParcOutputs:
    """Expected outputs from QSIParc.

    Parameters
    ----------
    output_dir : Path
        Parcellation output directory.
    workflow_dirs : Dict[str, Dict[Optional[str], Path]]
        Nested dictionary of expected dwi directories:
        {workflow_name: {session_id: dwi_dir_path}}.
        For datasets without sessions, session_id will be None.
    """

    output_dir: Path
    workflow_dirs: dict[str, dict[str | None, Path]]

    def exist(self) -> bool:
        """Check if key outputs exist.

        Returns
        -------
        bool
            True if all expected workflow dwi directories exist.
        """
        # Check if at least the main output directory exists
        if not self.output_dir.exists():
            return False

        # Check if all workflow dwi directories exist
        for workflow_dirs in self.workflow_dirs.values():
            for dwi_dir in workflow_dirs.values():
                if not dwi_dir.exists():
                    return False

        return True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns
        -------
        Dict[str, Any]
            Dictionary with Path objects converted to strings.
        """
        return {
            "output_dir": str(self.output_dir),
            "workflow_dirs": {
                workflow: {session: str(path) for session, path in sessions.items()}
                for workflow, sessions in self.workflow_dirs.items()
            },
        }

    @classmethod
    def from_inputs(cls, inputs: QSIParcInputs, output_dir: Path):
        """Generate expected output paths from inputs.

        Parameters
        ----------
        inputs : QSIParcInputs
            QSIParcInputs instance.
        output_dir : Path
            Resolved output directory (qsiparc output directory).

        Returns
        -------
        QSIParcOutputs
            QSIParcOutputs with expected paths.
        """
        # Discover sessions from qsirecon output
        sessions = _discover_sessions(inputs.qsirecon_dir, inputs.participant)

        # If a specific session is requested, filter to only that session
        if inputs.session:
            sessions = [inputs.session] if inputs.session in sessions else []

        # Extract workflow names from qsirecon directory
        workflows = _discover_workflows(inputs.qsirecon_dir)

        # Generate expected dwi directories for each workflow × session
        workflow_dirs = {}
        for workflow_name in workflows:
            workflow_dirs[workflow_name] = {}

            if sessions:
                # Multi-session dataset
                for session in sessions:
                    dwi_dir = (
                        output_dir
                        / f"qsirecon-{workflow_name}"
                        / f"sub-{inputs.participant}"
                        / f"ses-{session}"
                        / "dwi"
                    )
                    workflow_dirs[workflow_name][session] = dwi_dir
            else:
                # Single-session dataset (no session subdirectories)
                dwi_dir = (
                    output_dir
                    / f"qsirecon-{workflow_name}"
                    / f"sub-{inputs.participant}"
                    / "dwi"
                )
                workflow_dirs[workflow_name][None] = dwi_dir

        return cls(
            output_dir=output_dir,
            workflow_dirs=workflow_dirs,
        )


@dataclass
class QSIParcDefaults:
    """Default configuration for QSIParc (brain bank standards).

    Parameters
    ----------
    mask : Optional[str], optional
        Mask to apply during parcellation ("gm", "wm", "brain", or path), by default "gm".
    force : bool, optional
        Whether to overwrite existing outputs, by default False.
    background_label : int, optional
        Label value for background voxels, by default 0.
    resampling_target : Optional[str], optional
        Resampling strategy ("data", "labels", "atlas", or None), by default "data".
    log_level : str, optional
        Logging verbosity (e.g., "INFO", "DEBUG"), by default "INFO".
    n_jobs : Optional[int], optional
        Number of jobs to run in parallel, by default 1.
    n_procs : Optional[int], optional
        Number of processors to use, by default 1.
    """

    mask: str | None = "gm"
    force: bool = False
    background_label: int = 0
    resampling_target: str | None = "data"
    log_level: str = "INFO"
    n_jobs: int | None = 1
    n_procs: int | None = 1


def _discover_sessions(qsirecon_dir: Path, participant: str) -> list[str]:
    """Discover session IDs from QSIRecon output directory.

    Parameters
    ----------
    qsirecon_dir : Path
        QSIRecon output directory.
    participant : str
        Participant label (without 'sub-' prefix).

    Returns
    -------
    List[str]
        List of session IDs (without 'ses-' prefix), or empty list if no sessions.
    """
    derivatives_dir = qsirecon_dir / "derivatives"

    if not derivatives_dir.exists():
        return []

    # Look for session directories in any qsirecon workflow directory
    workflow_dirs = [
        d
        for d in derivatives_dir.iterdir()
        if d.is_dir() and d.name.startswith("qsirecon-")
    ]

    if not workflow_dirs:
        return []

    # Check first workflow directory for participant/session structure
    participant_dir = workflow_dirs[0] / f"sub-{participant}"

    if not participant_dir.exists():
        return []

    # Look for session subdirectories
    session_dirs = [
        d for d in participant_dir.iterdir() if d.is_dir() and d.name.startswith("ses-")
    ]

    if session_dirs:
        # Multi-session dataset
        return sorted([d.name.replace("ses-", "") for d in session_dirs])
    else:
        # Single-session dataset (no session subdirectories)
        return []


def _discover_workflows(qsirecon_dir: Path) -> list[str]:
    """Discover workflow names from QSIRecon output directory.

    Parameters
    ----------
    qsirecon_dir : Path
        QSIRecon output directory.

    Returns
    -------
    List[str]
        List of workflow suffixes found in the derivatives directory.
    """
    derivatives_dir = qsirecon_dir / "derivatives"

    if not derivatives_dir.exists():
        return []

    # Find all qsirecon-* directories
    workflow_dirs = [
        d.name.replace("qsirecon-", "")
        for d in derivatives_dir.iterdir()
        if d.is_dir() and d.name.startswith("qsirecon-")
    ]

    return sorted(workflow_dirs) if workflow_dirs else []
