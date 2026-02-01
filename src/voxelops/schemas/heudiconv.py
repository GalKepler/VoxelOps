"""HeudiConv schemas: inputs, outputs, and defaults."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class HeudiconvInputs:
    """Required inputs for HeudiConv DICOM to BIDS conversion.

    Attributes:
        dicom_dir: Directory containing DICOM files
        participant: Participant label (without 'sub-' prefix)
        output_dir: Output BIDS directory (optional, defaults to dicom_dir/../bids)
        session: Session label (optional, without 'ses-' prefix)
    """

    dicom_dir: Path
    participant: str
    output_dir: Optional[Path] = None
    session: Optional[str] = None
    heuristic: Optional[Path] = None

    def __post_init__(self):
        """Ensure paths are Path objects."""
        self.dicom_dir = Path(self.dicom_dir)
        if self.output_dir:
            self.output_dir = Path(self.output_dir)


@dataclass
class HeudiconvOutputs:
    """Expected outputs from HeudiConv.

    Attributes:
        bids_dir: Root BIDS directory
        participant_dir: Participant-specific directory (sub-XX/)
        dataset_description: dataset_description.json file
    """

    bids_dir: Path
    participant_dir: Path
    dataset_description: Path

    @classmethod
    def from_inputs(cls, inputs: HeudiconvInputs, output_dir: Path):
        """Generate expected output paths from inputs.

        Args:
            inputs: HeudiconvInputs instance
            output_dir: Resolved output directory

        Returns:
            HeudiconvOutputs with expected paths
        """
        participant_dir = output_dir / f"sub-{inputs.participant}"
        if inputs.session:
            participant_dir = participant_dir / f"ses-{inputs.session}"

        return cls(
            bids_dir=output_dir,
            participant_dir=participant_dir,
            dataset_description=output_dir / "dataset_description.json",
        )


@dataclass
class HeudiconvDefaults:
    """Default configuration for HeudiConv.

    Attributes:
        heuristic: Path to heuristic.py file (required for conversion)
        bids_validator: Run BIDS validator after conversion
        overwrite: Overwrite existing output
        converter: DICOM converter to use
        docker_image: Docker image to use
    """

    heuristic: Optional[Path] = None
    bids_validator: bool = True
    overwrite: bool = False
    converter: str = "dcm2niix"
    bids: Optional[str] = "notop"
    grouping: Optional[str] = "all"
    docker_image: str = "nipy/heudiconv:1.3.4"
    # Post-processing options
    post_process: bool = True  # Enable post-heudiconv processing
    post_process_dry_run: bool = False  # Test mode - report only, don't modify

    def __post_init__(self):
        """Ensure heuristic path is Path object if provided."""
        if self.heuristic:
            self.heuristic = Path(self.heuristic)
