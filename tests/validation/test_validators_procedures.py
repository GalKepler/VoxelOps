"""Tests for procedure-specific validators."""

from dataclasses import dataclass
from pathlib import Path

import pytest

from voxelops.validation.context import ValidationContext
from voxelops.validation.validators import (
    HeudiConvValidator,
    QSIParcValidator,
    QSIPrepValidator,
    QSIReconValidator,
)


@dataclass
class MockInputs:
    """Mock inputs for testing."""

    dicom_dir: Path | None = None
    bids_dir: Path | None = None
    qsiprep_dir: Path | None = None
    qsirecon_dir: Path | None = None
    heuristic: Path | None = None


@dataclass
class MockExpectedOutputs:
    """Mock expected outputs for testing."""

    bids_dir: Path | None = None
    participant_dir: Path | None = None
    qsiprep_dir: Path | None = None
    qsirecon_dir: Path | None = None
    output_dir: Path | None = None
    html_report: Path | None = None
    workflow_reports: dict | None = None
    workflow_dirs: dict | None = None


class TestHeudiConvValidator:
    """Tests for HeudiConvValidator."""

    def test_validator_attributes(self):
        """Test HeudiConvValidator attributes."""
        validator = HeudiConvValidator()
        assert validator.procedure_name == "heudiconv"
        assert len(validator.pre_rules) == 3
        assert len(validator.post_rules) == 2

    def test_pre_validation_success(self, tmp_path):
        """Test successful pre-validation."""
        # Setup test environment
        dicom_dir = tmp_path / "dicoms"
        dicom_dir.mkdir()
        (dicom_dir / "scan1.dcm").touch()
        heuristic = tmp_path / "heuristic.py"
        heuristic.touch()

        validator = HeudiConvValidator()
        context = ValidationContext(
            procedure_name="heudiconv",
            participant="01",
            inputs=MockInputs(dicom_dir=dicom_dir, heuristic=heuristic),
        )

        report = validator.validate_pre(context)

        assert report.procedure == "heudiconv"
        assert report.phase == "pre"
        assert report.passed is True
        assert len(report.results) == 3

    def test_pre_validation_missing_dicom_dir(self, tmp_path):
        """Test pre-validation with missing DICOM directory."""
        dicom_dir = tmp_path / "nonexistent"
        heuristic = tmp_path / "heuristic.py"
        heuristic.touch()

        validator = HeudiConvValidator()
        context = ValidationContext(
            procedure_name="heudiconv",
            participant="01",
            inputs=MockInputs(dicom_dir=dicom_dir, heuristic=heuristic),
        )

        report = validator.validate_pre(context)

        assert report.passed is False
        assert len(report.errors) >= 1

    def test_post_validation_success(self, tmp_path):
        """Test successful post-validation."""
        # Setup test environment
        bids_dir = tmp_path / "bids"
        bids_dir.mkdir()
        (bids_dir / "dataset_description.json").touch()
        participant_dir = bids_dir / "sub-01"
        participant_dir.mkdir()

        validator = HeudiConvValidator()
        context = ValidationContext(
            procedure_name="heudiconv",
            participant="01",
            expected_outputs=MockExpectedOutputs(
                bids_dir=bids_dir, participant_dir=participant_dir
            ),
        )

        report = validator.validate_post(context)

        assert report.procedure == "heudiconv"
        assert report.phase == "post"
        assert report.passed is True


class TestQSIPrepValidator:
    """Tests for QSIPrepValidator."""

    def test_validator_attributes(self):
        """Test QSIPrepValidator attributes."""
        validator = QSIPrepValidator()
        assert validator.procedure_name == "qsiprep"
        assert len(validator.pre_rules) == 6
        assert (
            len(validator.post_rules) == 3
        )  # Added ExpectedOutputsExistRule for HTML report

    def test_pre_validation_success_with_sessions(self, tmp_path):
        """Test successful pre-validation with session-based BIDS dataset."""
        # Setup test environment with sessions
        bids_dir = tmp_path / "bids"
        sub_dir = bids_dir / "sub-01"
        ses_dir = sub_dir / "ses-01"
        dwi_dir = ses_dir / "dwi"
        anat_dir = ses_dir / "anat"
        dwi_dir.mkdir(parents=True)
        anat_dir.mkdir(parents=True)

        # Create required files
        (dwi_dir / "sub-01_ses-01_dwi.nii.gz").touch()
        (dwi_dir / "sub-01_ses-01_dwi.bval").touch()
        (dwi_dir / "sub-01_ses-01_dwi.bvec").touch()
        (anat_dir / "sub-01_ses-01_T1w.nii.gz").touch()

        validator = QSIPrepValidator()
        context = ValidationContext(
            procedure_name="qsiprep",
            participant="01",
            session="01",
            inputs=MockInputs(bids_dir=bids_dir),
        )

        report = validator.validate_pre(context)

        assert report.procedure == "qsiprep"
        assert report.passed is True
        assert len(report.results) == 6

    def test_pre_validation_success_without_sessions(self, tmp_path):
        """Test successful pre-validation with non-session BIDS dataset."""
        # Setup test environment without sessions
        bids_dir = tmp_path / "bids"
        sub_dir = bids_dir / "sub-01"
        dwi_dir = sub_dir / "dwi"
        anat_dir = sub_dir / "anat"
        dwi_dir.mkdir(parents=True)
        anat_dir.mkdir(parents=True)

        # Create required files
        (dwi_dir / "sub-01_dwi.nii.gz").touch()
        (dwi_dir / "sub-01_dwi.bval").touch()
        (dwi_dir / "sub-01_dwi.bvec").touch()
        (anat_dir / "sub-01_T1w.nii.gz").touch()

        validator = QSIPrepValidator()
        context = ValidationContext(
            procedure_name="qsiprep",
            participant="01",
            inputs=MockInputs(bids_dir=bids_dir),
        )

        report = validator.validate_pre(context)

        assert report.procedure == "qsiprep"
        assert report.passed is True
        assert len(report.results) == 6

    def test_pre_validation_missing_dwi(self, tmp_path):
        """Test pre-validation with missing DWI files."""
        bids_dir = tmp_path / "bids"
        sub_dir = bids_dir / "sub-01"
        sub_dir.mkdir(parents=True)

        validator = QSIPrepValidator()
        context = ValidationContext(
            procedure_name="qsiprep",
            participant="01",
            inputs=MockInputs(bids_dir=bids_dir),
        )

        report = validator.validate_pre(context)

        assert report.passed is False
        assert len(report.errors) >= 1

    def test_post_validation_success(self, tmp_path):
        """Test successful post-validation."""
        # Setup test environment
        qsiprep_dir = tmp_path / "qsiprep"
        qsiprep_dir.mkdir()
        html_report = qsiprep_dir / "sub-01.html"
        html_report.touch()

        participant_dir = qsiprep_dir / "sub-01"
        dwi_dir = participant_dir / "dwi"
        dwi_dir.mkdir(parents=True)
        (dwi_dir / "sub-01_desc-preproc_dwi.nii.gz").touch()

        validator = QSIPrepValidator()
        context = ValidationContext(
            procedure_name="qsiprep",
            participant="01",
            expected_outputs=MockExpectedOutputs(
                qsiprep_dir=qsiprep_dir,
                participant_dir=participant_dir,
                html_report=html_report,
            ),
        )

        report = validator.validate_post(context)

        assert report.passed is True
        assert len(report.results) == 3  # qsiprep_dir, participant_dir, html_report


class TestQSIReconValidator:
    """Tests for QSIReconValidator."""

    def test_validator_attributes(self):
        """Test QSIReconValidator attributes."""
        validator = QSIReconValidator()
        assert validator.procedure_name == "qsirecon"
        assert len(validator.pre_rules) == 4
        assert (
            len(validator.post_rules) == 4
        )  # Added back participant_dir and workflow_reports checks

    def test_pre_validation_success(self, tmp_path):
        """Test successful pre-validation."""
        # Setup test environment
        qsiprep_dir = tmp_path / "qsiprep"
        sub_dir = qsiprep_dir / "sub-01"
        dwi_dir = sub_dir / "dwi"
        dwi_dir.mkdir(parents=True)

        # Create required files
        (dwi_dir / "sub-01_desc-preproc_dwi.nii.gz").touch()
        (dwi_dir / "sub-01-image_qc.tsv").touch()

        validator = QSIReconValidator()
        context = ValidationContext(
            procedure_name="qsirecon",
            participant="01",
            inputs=MockInputs(qsiprep_dir=qsiprep_dir),
        )

        report = validator.validate_pre(context)

        assert report.procedure == "qsirecon"
        assert report.passed is True

    def test_post_validation_success(self, tmp_path):
        """Test successful post-validation."""
        # Setup test environment
        qsirecon_dir = tmp_path / "qsirecon"
        participant_dir = qsirecon_dir / "sub-01"
        output_dir = participant_dir / "output"
        output_dir.mkdir(parents=True)
        (output_dir / "sub-01_recon.nii.gz").touch()

        # Create workflow reports for the new ExpectedOutputsExistRule
        workflow_reports = {"workflow1": {"session1": tmp_path / "report1.html"}}
        (tmp_path / "report1.html").touch()

        validator = QSIReconValidator()
        context = ValidationContext(
            procedure_name="qsirecon",
            participant="01",
            expected_outputs=MockExpectedOutputs(
                qsirecon_dir=qsirecon_dir,
                participant_dir=participant_dir,
                workflow_reports=workflow_reports,
            ),
        )

        report = validator.validate_post(context)

        assert report.passed is True


class TestQSIParcValidator:
    """Tests for QSIParcValidator."""

    def test_validator_attributes(self):
        """Test QSIParcValidator attributes."""
        validator = QSIParcValidator()
        assert validator.procedure_name == "qsiparc"
        assert len(validator.pre_rules) == 3
        assert len(validator.post_rules) == 3  # output_dir, workflow_dirs, TSV files

    def test_pre_validation_success(self, tmp_path):
        """Test successful pre-validation."""
        # Setup test environment with proper QSIRecon derivative structure
        qsirecon_dir = tmp_path / "qsirecon"
        sub_dir = qsirecon_dir / "sub-01"
        sub_dir.mkdir(parents=True)

        # Create QSIRecon derivative outputs as expected by the validator
        workflow_dir = (
            qsirecon_dir / "derivatives" / "qsirecon-test_workflow" / "sub-01" / "dwi"
        )
        workflow_dir.mkdir(parents=True)
        (workflow_dir / "sub-01_recon.nii.gz").touch()

        validator = QSIParcValidator()
        context = ValidationContext(
            procedure_name="qsiparc",
            participant="01",
            inputs=MockInputs(qsirecon_dir=qsirecon_dir),
        )

        report = validator.validate_pre(context)

        assert report.procedure == "qsiparc"
        assert report.passed is True

    def test_post_validation_success(self, tmp_path):
        """Test successful post-validation."""
        # Setup test environment
        output_dir = tmp_path / "parcellation"
        output_dir.mkdir()

        # Create workflow directory structure and TSV files
        workflow_dwi_dir = output_dir / "qsirecon-test_workflow" / "sub-01" / "dwi"
        workflow_dwi_dir.mkdir(parents=True)
        (workflow_dwi_dir / "sub-01_parcellated.tsv").touch()

        # Create workflow_dirs for ExpectedOutputsExistRule
        workflow_dirs = {"test_workflow": {None: workflow_dwi_dir}}

        validator = QSIParcValidator()
        context = ValidationContext(
            procedure_name="qsiparc",
            participant="01",
            expected_outputs=MockExpectedOutputs(
                output_dir=output_dir,
                workflow_dirs=workflow_dirs,
            ),
        )

        report = validator.validate_post(context)

        assert report.passed is True


class TestAllValidators:
    """Tests that apply to all validators."""

    @pytest.mark.parametrize(
        "validator_class,procedure_name",
        [
            (HeudiConvValidator, "heudiconv"),
            (QSIPrepValidator, "qsiprep"),
            (QSIReconValidator, "qsirecon"),
            (QSIParcValidator, "qsiparc"),
        ],
    )
    def test_validator_has_rules(self, validator_class, procedure_name):
        """Test that all validators have rules defined."""
        validator = validator_class()
        assert validator.procedure_name == procedure_name
        assert len(validator.pre_rules) > 0
        # Post rules are optional but should be defined
        assert hasattr(validator, "post_rules")

    @pytest.mark.parametrize(
        "validator_class",
        [
            HeudiConvValidator,
            QSIPrepValidator,
            QSIReconValidator,
            QSIParcValidator,
        ],
    )
    def test_validate_all_returns_both_reports(self, validator_class):
        """Test that validate_all returns both pre and post reports."""
        validator = validator_class()
        # Note: validation will fail due to missing inputs, but we're just
        # testing that both reports are returned
        context = ValidationContext(
            procedure_name=validator.procedure_name,
            participant="01",
        )

        pre_report, post_report = validator.validate_all(context)

        assert pre_report.phase == "pre"
        assert post_report.phase == "post"
        assert pre_report.procedure == validator.procedure_name
        assert post_report.procedure == validator.procedure_name
        # Reports should have results (even if they're failures)
        assert isinstance(pre_report.results, list)
        assert isinstance(post_report.results, list)
