"""QSIPrep schemas: inputs, outputs, and defaults."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List


@dataclass
class QSIPrepInputs:
    """Required inputs for QSIPrep diffusion preprocessing.

    Parameters
    ----------
    bids_dir : Path
        BIDS dataset directory.
    participant : str
        Participant label (without 'sub-' prefix).
    output_dir : Optional[Path], optional
        Output directory, by default None.
        If None, defaults to bids_dir/../derivatives/qsiprep.
    work_dir : Optional[Path], optional
        Working directory, by default None.
        If None, defaults to output_dir/../work/qsiprep.
    bids_filters : Optional[Path], optional
        Path to BIDS filters JSON file, by default None.
    """

    bids_dir: Path
    participant: str
    output_dir: Optional[Path] = None
    work_dir: Optional[Path] = None
    bids_filters: Optional[Path] = None  # Path to BIDS filters JSON file

    def __post_init__(self):
        """Ensure paths are Path objects."""
        self.bids_dir = Path(self.bids_dir)
        if self.output_dir:
            self.output_dir = Path(self.output_dir)
        if self.work_dir:
            self.work_dir = Path(self.work_dir)
        if self.bids_filters:
            self.bids_filters = Path(self.bids_filters)


@dataclass
class QSIPrepOutputs:
    """Expected outputs from QSIPrep.

    Parameters
    ----------
    qsiprep_dir : Path
        QSIPrep output directory.
    participant_dir : Path
        Participant-specific directory.
    html_report : Path
        HTML report file.
    work_dir : Path
        Working directory.
    figures_dir : Path
        QC figures directory.
    """

    qsiprep_dir: Path
    participant_dir: Path
    html_report: Path
    work_dir: Path
    figures_dir: Path

    @classmethod
    def from_inputs(cls, inputs: QSIPrepInputs, output_dir: Path, work_dir: Path):
        """Generate expected output paths from inputs.

        Parameters
        ----------
        inputs : QSIPrepInputs
            QSIPrepInputs instance.
        output_dir : Path
            Resolved output directory.
        work_dir : Path
            Resolved work directory.

        Returns
        -------
        QSIPrepOutputs
            QSIPrepOutputs with expected paths.
        """
        qsiprep_dir = output_dir / "qsiprep"
        participant_dir = qsiprep_dir / f"sub-{inputs.participant}"

        return cls(
            qsiprep_dir=qsiprep_dir,
            participant_dir=participant_dir,
            html_report=qsiprep_dir / f"sub-{inputs.participant}.html",
            work_dir=work_dir,
            figures_dir=participant_dir / "figures",
        )


@dataclass
class QSIPrepDefaults:
    """Default configuration for QSIPrep (brain bank standards).

    Parameters
    ----------
    nprocs : int, optional
        Number of parallel processes, by default 8.
    mem_gb : int, optional
        Memory limit in GB, by default 16000.
    output_resolution : float, optional
        Output resolution in mm, by default 1.6.
    anatomical_template : List[str], optional
        List of output spaces, by default ["MNI152NLin2009cAsym"].
    longitudinal : bool, optional
        Enable longitudinal processing, by default False.
    subject_anatomical_reference : str, optional
        Anatomical reference for longitudinal processing, by default "unbiased".
    skip_bids_validation : bool, optional
        Skip BIDS validation, by default False.
    fs_license : Optional[Path], optional
        Path to FreeSurfer license file, by default None.
    docker_image : str, optional
        Docker image to use, by default "pennlinc/qsiprep:latest".
    """

    nprocs: int = 8
    mem_mb: int = 16000
    output_resolution: float = 1.6
    anatomical_template: List[str] = field(
        default_factory=lambda: ["MNI152NLin2009cAsym"]
    )
    longitudinal: bool = False
    subject_anatomical_reference: str = "unbiased"
    skip_bids_validation: bool = False
    fs_license: Optional[Path] = None
    docker_image: str = "pennlinc/qsiprep:latest"

    def __post_init__(self):
        """Ensure fs_license is Path object if provided."""
        if self.fs_license:
            self.fs_license = Path(self.fs_license)
