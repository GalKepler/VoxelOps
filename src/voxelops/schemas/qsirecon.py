"""QSIRecon schemas: inputs, outputs, and defaults."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


@dataclass
class QSIReconInputs:
    """Required inputs for QSIRecon diffusion reconstruction.

    Parameters
    ----------
    qsiprep_dir : Path
        QSIPrep output directory.
    participant : str
        Participant label (without 'sub-' prefix).
    output_dir : Optional[Path], optional
        Output directory, by default None.
        If None, defaults to qsiprep_dir/../qsirecon.
    work_dir : Optional[Path], optional
        Working directory, by default None.
        If None, defaults to output_dir/../work/qsirecon.
    recon_spec : Optional[Path], optional
        Path to reconstruction spec YAML file, by default None.
    datasets : Optional[dict[str, Path]], optional
        Dictionary of dataset names and paths, by default None.
    atlases : Optional[List[str]], optional
        List of atlases for connectivity, by default None.
    """

    qsiprep_dir: Path
    participant: str
    atlases: List[str] = field(
        default_factory=lambda: [
            "4S156Parcels",
            "4S256Parcels",
            "4S356Parcels",
            "4S456Parcels",
            "4S556Parcels",
            "4S656Parcels",
            "4S756Parcels",
            "4S856Parcels",
            "4S956Parcels",
            "4S1056Parcels",
            "AICHA384Ext",
            "Brainnetome246Ext",
            "AAL116",
            "Gordon333Ext",
        ]
    )
    output_dir: Optional[Path] = None
    work_dir: Optional[Path] = None
    recon_spec: Optional[Path] = None
    datasets: Optional[dict[str, Path]] = None

    def __post_init__(self):
        """Ensure paths are Path objects."""
        self.qsiprep_dir = Path(self.qsiprep_dir)
        if self.output_dir:
            self.output_dir = Path(self.output_dir)
        if self.work_dir:
            self.work_dir = Path(self.work_dir)
        if self.recon_spec:
            self.recon_spec = Path(self.recon_spec)
        if self.datasets:
            self.datasets = {k: Path(v) for k, v in self.datasets.items()}


@dataclass
class QSIReconOutputs:
    """Expected outputs from QSIRecon.

    Parameters
    ----------
    qsirecon_dir : Path
        QSIRecon output directory.
    participant_dir : Path
        Participant-specific directory.
    workflow_reports : Dict[str, Dict[str, Path]]
        Nested dictionary of HTML reports: {workflow_name: {session_id: html_path}}.
        For datasets without sessions, session_id will be None.
    work_dir : Path
        Working directory.
    """

    qsirecon_dir: Path
    participant_dir: Path
    workflow_reports: Dict[str, Dict[Optional[str], Path]]
    work_dir: Path

    def exist(self) -> bool:
        """Check if key outputs exist.

        Returns
        -------
        bool
            True if all expected workflow HTML reports exist.
        """
        # Check if at least the main output directory exists
        if not self.qsirecon_dir.exists():
            return False

        # Check if all workflow reports exist
        for workflow_reports in self.workflow_reports.values():
            for html_path in workflow_reports.values():
                if not html_path.exists():
                    return False

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns
        -------
        Dict[str, any]
            Dictionary with Path objects converted to strings.
        """
        return {
            "qsirecon_dir": str(self.qsirecon_dir),
            "participant_dir": str(self.participant_dir),
            "workflow_reports": {
                workflow: {session: str(path) for session, path in sessions.items()}
                for workflow, sessions in self.workflow_reports.items()
            },
            "work_dir": str(self.work_dir),
        }

    @classmethod
    def from_inputs(cls, inputs: QSIReconInputs, output_dir: Path, work_dir: Path):
        """Generate expected output paths from inputs.

        Parameters
        ----------
        inputs : QSIReconInputs
            QSIReconInputs instance.
        output_dir : Path
            Resolved output directory (the qsirecon output directory).
        work_dir : Path
            Resolved work directory.

        Returns
        -------
        QSIReconOutputs
            QSIReconOutputs with expected paths.
        """
        # output_dir is already the qsirecon output directory
        qsirecon_dir = output_dir
        participant_dir = qsirecon_dir / f"sub-{inputs.participant}"

        # Discover sessions from qsiprep output
        sessions = _discover_sessions(inputs.qsiprep_dir, inputs.participant)

        # Extract workflow names from recon spec
        workflows = (
            _extract_workflows(inputs.recon_spec) if inputs.recon_spec else ["default"]
        )

        # Generate expected HTML reports for each workflow × session combination
        workflow_reports = {}
        for workflow_name in workflows:
            workflow_reports[workflow_name] = {}

            if sessions:
                # Multi-session dataset
                for session in sessions:
                    html_path = (
                        qsirecon_dir
                        / "derivatives"
                        / f"qsirecon-{workflow_name}"
                        / f"sub-{inputs.participant}_ses-{session}.html"
                    )
                    workflow_reports[workflow_name][session] = html_path
            else:
                # Single-session dataset (no session subdirectories)
                html_path = (
                    qsirecon_dir
                    / "derivatives"
                    / f"qsirecon-{workflow_name}"
                    / f"sub-{inputs.participant}.html"
                )
                workflow_reports[workflow_name][None] = html_path

        return cls(
            qsirecon_dir=qsirecon_dir,
            participant_dir=participant_dir,
            workflow_reports=workflow_reports,
            work_dir=work_dir,
        )


@dataclass
class QSIReconDefaults:
    """Default configuration for QSIRecon (brain bank standards).

    Parameters
    ----------
    nprocs : int, optional
        Number of parallel processes, by default 8.
    mem_gb : int, optional
        Memory limit in GB, by default 16000.
    atlases : List[str], optional
        List of atlases for connectivity, by default a long list of atlases.
    fs_subjects_dir : Optional[Path], optional
        FreeSurfer subjects directory, by default None.
    fs_license : Optional[Path], optional
        Path to FreeSurfer license file, by default None.
    docker_image : str, optional
        Docker image to use, by default "pennlinc/qsirecon:latest".
    force : bool, optional
        Force re-run even if outputs exist, by default False.
    """

    nprocs: int = 8
    mem_mb: int = 16000
    fs_subjects_dir: Optional[Path] = None
    fs_license: Optional[Path] = None
    docker_image: str = "pennlinc/qsirecon:latest"
    force: bool = False

    def __post_init__(self):
        """Ensure paths are Path objects if provided."""
        if self.fs_subjects_dir:
            self.fs_subjects_dir = Path(self.fs_subjects_dir)
        if self.fs_license:
            self.fs_license = Path(self.fs_license)


def _discover_sessions(qsiprep_dir: Path, participant: str) -> List[str]:
    """Discover session IDs from QSIPrep output directory.

    Parameters
    ----------
    qsiprep_dir : Path
        QSIPrep output directory.
    participant : str
        Participant label (without 'sub-' prefix).

    Returns
    -------
    List[str]
        List of session IDs (without 'ses-' prefix), or empty list if no sessions.
    """
    participant_dir = qsiprep_dir / f"sub-{participant}"

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


def _extract_workflows(recon_spec_path: Path) -> List[str]:
    """Extract workflow suffixes from QSIRecon reconstruction spec YAML.

    QSIRecon creates derivative directories based on the qsirecon_suffix
    of each node, not the workflow name.

    Parameters
    ----------
    recon_spec_path : Path
        Path to reconstruction spec YAML file.

    Returns
    -------
    List[str]
        List of qsirecon_suffix values from nodes in the spec.
    """
    if not recon_spec_path or not recon_spec_path.exists():
        return ["default"]

    try:
        with open(recon_spec_path) as f:
            spec = yaml.safe_load(f)

        suffixes = []

        # Single workflow spec
        if isinstance(spec, dict) and "nodes" in spec:
            for node in spec["nodes"]:
                if "qsirecon_suffix" in node:
                    suffixes.append(node["qsirecon_suffix"])

        # Multiple workflows
        elif isinstance(spec, list):
            for workflow in spec:
                if "nodes" in workflow:
                    for node in workflow["nodes"]:
                        if "qsirecon_suffix" in node:
                            suffixes.append(node["qsirecon_suffix"])

        return suffixes if suffixes else ["default"]
    except Exception:
        # If we can't parse the spec, use default
        return ["default"]
