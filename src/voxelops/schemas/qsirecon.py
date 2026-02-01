"""QSIRecon schemas: inputs, outputs, and defaults."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List


@dataclass
class QSIReconInputs:
    """Required inputs for QSIRecon diffusion reconstruction.

    Attributes:
        qsiprep_dir: QSIPrep output directory
        participant: Participant label (without 'sub-' prefix)
        output_dir: Output directory (optional, defaults to qsiprep_dir/../qsirecon)
        work_dir: Working directory (optional, defaults to output_dir/../work/qsirecon)
    """

    qsiprep_dir: Path
    participant: str
    output_dir: Optional[Path] = None
    work_dir: Optional[Path] = None
    recon_spec: Optional[Path] = None

    def __post_init__(self):
        """Ensure paths are Path objects."""
        self.qsiprep_dir = Path(self.qsiprep_dir)
        if self.output_dir:
            self.output_dir = Path(self.output_dir)
        if self.work_dir:
            self.work_dir = Path(self.work_dir)
        if self.recon_spec:
            self.recon_spec = Path(self.recon_spec)


@dataclass
class QSIReconOutputs:
    """Expected outputs from QSIRecon.

    Attributes:
        qsirecon_dir: QSIRecon output directory
        participant_dir: Participant-specific directory
        html_report: HTML report file
        work_dir: Working directory
    """

    qsirecon_dir: Path
    participant_dir: Path
    html_report: Path
    work_dir: Path

    @classmethod
    def from_inputs(cls, inputs: QSIReconInputs, output_dir: Path, work_dir: Path):
        """Generate expected output paths from inputs.

        Args:
            inputs: QSIReconInputs instance
            output_dir: Resolved output directory
            work_dir: Resolved work directory

        Returns:
            QSIReconOutputs with expected paths
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

    Attributes:
        nprocs: Number of parallel processes
        mem_gb: Memory limit in GB
        atlases: List of atlases for connectivity
        recon_spec: Path to reconstruction spec YAML
        fs_subjects_dir: FreeSurfer subjects directory
        fs_license: Path to FreeSurfer license file
        docker_image: Docker image to use
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
