"""QSIParc schemas: inputs, outputs, and defaults."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, List


@dataclass
class QSIParcInputs:
    """Required inputs for QSIParc parcellation.

    Attributes:
        qsirecon_dir: QSIRecon output directory
        participant: Participant label (without 'sub-' prefix)
        output_dir: Output directory (optional, defaults to qsirecon_dir/../qsiparc)
    """

    qsirecon_dir: Path
    participant: str
    output_dir: Optional[Path] = None

    def __post_init__(self):
        """Ensure paths are Path objects."""
        self.qsirecon_dir = Path(self.qsirecon_dir)
        if self.output_dir:
            self.output_dir = Path(self.output_dir)


@dataclass
class QSIParcOutputs:
    """Expected outputs from QSIParc.

    Attributes:
        qsiparc_dir: QSIParc output directory
        participant_dir: Participant-specific directory
        connectivity_dir: Connectivity matrices directory
    """

    qsiparc_dir: Path
    participant_dir: Path
    connectivity_dir: Path

    @classmethod
    def from_inputs(cls, inputs: QSIParcInputs, output_dir: Path):
        """Generate expected output paths from inputs.

        Args:
            inputs: QSIParcInputs instance
            output_dir: Resolved output directory

        Returns:
            QSIParcOutputs with expected paths
        """
        qsiparc_dir = output_dir / "qsiparc"
        participant_dir = qsiparc_dir / f"sub-{inputs.participant}"

        return cls(
            qsiparc_dir=qsiparc_dir,
            participant_dir=participant_dir,
            connectivity_dir=participant_dir / "connectivity",
        )


@dataclass
class QSIParcDefaults:
    """Default configuration for QSIParc (brain bank standards).

    Attributes:
        atlases: List of atlases for parcellation
        docker_image: Docker image to use
    """

    atlases: List[str] = field(default_factory=lambda: ["schaefer100", "schaefer200"])
    docker_image: str = "pennlinc/qsiparc:latest"
