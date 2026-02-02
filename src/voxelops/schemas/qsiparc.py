"""QSIParc schemas: inputs, outputs, and defaults."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from parcellate.interfaces.models import AtlasDefinition

@dataclass
class QSIParcInputs:
    """Required inputs for QSIParc parcellation.

    Attributes:
        qsirecon_dir: QSIRecon output directory
        participant: Participant label (without 'sub-' prefix)
        output_dir: Output directory (optional, defaults to qsirecon_dir parent)
        session: Session label (optional, without 'ses-' prefix)
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

    Attributes:
        output_dir: Parcellation output directory
    """

    output_dir: Path

    @classmethod
    def from_inputs(cls, inputs: QSIParcInputs, output_dir: Path):
        """Generate expected output paths from inputs.

        Args:
            inputs: QSIParcInputs instance
            output_dir: Resolved output directory

        Returns:
            QSIParcOutputs with expected paths
        """
        return cls(output_dir=output_dir)


@dataclass
class QSIParcDefaults:
    """Default configuration for QSIParc (brain bank standards).

    Attributes:
        mask: Mask to apply during parcellation ("gm", "wm", "brain", or path)
        force: Whether to overwrite existing outputs
        background_label: Label value for background voxels
        resampling_target: Resampling strategy ("data", "labels", "atlas", or None)
        log_level: Logging verbosity (e.g., "INFO", "DEBUG")
    """

    mask: Optional[str] = "gm"
    force: bool = False
    background_label: int = 0
    resampling_target: Optional[str] = "data"
    log_level: str = "INFO"
    n_jobs: Optional[int] = 1
    n_procs: Optional[int] = 1