"""HeudiConv schemas: inputs, outputs, and defaults."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class HeudiconvInputs:
    """Required inputs for HeudiConv DICOM to BIDS conversion.

    Parameters
    ----------
    dicom_dir : Path
        Directory containing DICOM files.
    participant : str
        Participant label (without 'sub-' prefix).
    output_dir : Optional[Path], optional
        Output BIDS directory, by default None.
        If None, defaults to dicom_dir/../bids.
    session : Optional[str], optional
        Session label (without 'ses-' prefix), by default None.
    heuristic : Optional[Path], optional
        Path to heuristic.py file, by default None.
    """

    dicom_dir: Path
    participant: str
    output_dir: Path | None = None
    session: str | None = None
    heuristic: Path | None = None
    bids: str | None = "notop"
    grouping: str | None = "all"

    def __post_init__(self):
        """Ensure paths are Path objects."""
        self.dicom_dir = Path(self.dicom_dir)
        if self.output_dir:
            self.output_dir = Path(self.output_dir)
        if self.heuristic:
            self.heuristic = Path(self.heuristic)
        if self.bids:
            _bids = str(self.bids)
            self.bids = _bids if _bids.lower() != "none" else None
        if self.grouping:
            _grouping = str(self.grouping)
            self.grouping = _grouping if _grouping.lower() != "none" else None


@dataclass
class HeudiconvOutputs:
    """Expected outputs from HeudiConv.

    Parameters
    ----------
    bids_dir : Path
        Root BIDS directory.
    participant_dir : Path
        Participant-specific directory (sub-XX/).
    dataset_description : Path
        dataset_description.json file.
    """

    bids_dir: Path
    participant_dir: Path
    dataset_description: Path

    @classmethod
    def from_inputs(cls, inputs: HeudiconvInputs, output_dir: Path):
        """Generate expected output paths from inputs.

        Parameters
        ----------
        inputs : HeudiconvInputs
            HeudiconvInputs instance.
        output_dir : Path
            Resolved output directory.

        Returns
        -------
        HeudiconvOutputs
            HeudiconvOutputs with expected paths.
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

    Parameters
    ----------
    heuristic : Optional[Path], optional
        Path to heuristic.py file (required for conversion), by default None.
    bids_validator : bool, optional
        Run BIDS validator after conversion, by default True.
    overwrite : bool, optional
        Overwrite existing output, by default False.
    converter : str, optional
        DICOM converter to use, by default "dcm2niix".
    docker_image : str, optional
        Docker image to use, by default "nipy/heudiconv:1.3.4".
    post_process : bool, optional
        Enable post-heudiconv processing, by default True.
    post_process_dry_run : bool, optional
        Test mode - report only, don't modify, by default False.
    """

    heuristic: Path | None = None
    bids_validator: bool = True
    overwrite: bool = False
    converter: str = "dcm2niix"
    docker_image: str = "nipy/heudiconv:1.3.4"
    # Post-processing options
    post_process: bool = True  # Enable post-heudiconv processing
    post_process_dry_run: bool = False  # Test mode - report only, don't modify

    def __post_init__(self):
        """Ensure heuristic path is Path object if provided."""
        if self.heuristic:
            self.heuristic = Path(self.heuristic)
