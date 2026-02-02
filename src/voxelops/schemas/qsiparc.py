"""QSIParc schemas: inputs, outputs, and defaults."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
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
    output_dir: Optional[Path] = None
    session: Optional[str] = None
    atlases: Optional[list[AtlasDefinition]] = None
    n_jobs: Optional[int] = None
    n_procs: Optional[int] = None

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
    """

    output_dir: Path

    @classmethod
    def from_inputs(cls, inputs: QSIParcInputs, output_dir: Path):
        """Generate expected output paths from inputs.

        Parameters
        ----------
        inputs : QSIParcInputs
            QSIParcInputs instance.
        output_dir : Path
            Resolved output directory.

        Returns
        -------
        QSIParcOutputs
            QSIParcOutputs with expected paths.
        """
        return cls(output_dir=output_dir)


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

    mask: Optional[str] = "gm"
    force: bool = False
    background_label: int = 0
    resampling_target: Optional[str] = "data"
    log_level: str = "INFO"
    n_jobs: Optional[int] = 1
    n_procs: Optional[int] = 1