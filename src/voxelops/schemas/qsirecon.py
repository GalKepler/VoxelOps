"""QSIRecon schemas: inputs, outputs, and defaults."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List


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
    output_dir: Optional[Path] = None
    work_dir: Optional[Path] = None
    recon_spec: Optional[Path] = None
    datasets: Optional[dict[str, Path]] = None
    atlases: Optional[List[str]] = None


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
    html_report : Path
        HTML report file.
    work_dir : Path
        Working directory.
    """

    qsirecon_dir: Path
    participant_dir: Path
    html_report: Path
    work_dir: Path

    @classmethod
    def from_inputs(cls, inputs: QSIReconInputs, output_dir: Path, work_dir: Path):
        """Generate expected output paths from inputs.

        Parameters
        ----------
        inputs : QSIReconInputs
            QSIReconInputs instance.
        output_dir : Path
            Resolved output directory.
        work_dir : Path
            Resolved work directory.

        Returns
        -------
        QSIReconOutputs
            QSIReconOutputs with expected paths.
        """
        qsirecon_dir = output_dir / "qsirecon"
        participant_dir = qsirecon_dir / f"sub-{inputs.participant}"

        return cls(
            qsirecon_dir=qsirecon_dir,
            participant_dir=participant_dir,
            html_report=qsirecon_dir / f"sub-{inputs.participant}.html",
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
    """

    nprocs: int = 8
    mem_mb: int = 16000
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
    fs_subjects_dir: Optional[Path] = None
    fs_license: Optional[Path] = None
    docker_image: str = "pennlinc/qsirecon:latest"

    def __post_init__(self):
        """Ensure paths are Path objects if provided."""
        if self.fs_subjects_dir:
            self.fs_subjects_dir = Path(self.fs_subjects_dir)
        if self.fs_license:
            self.fs_license = Path(self.fs_license)
