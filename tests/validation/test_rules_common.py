from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from voxelops.validation.context import ValidationContext
from voxelops.validation.rules.common import (
    DirectoryExistsRule,
    FileExistsRule,
    GlobFilesExistRule,
    OutputDirectoryExistsRule,
    ParticipantExistsRule,
)


@dataclass
class MockInputs:
    bids_dir: Optional[Path] = None
    dicom_dir: Optional[Path] = None
    fs_license: Optional[Path] = None
    output_dir: Optional[Path] = None
    qsiprep_dir: Optional[Path] = None


@dataclass
class MockConfig:
    fs_license: Optional[Path] = None


class TestDirectoryExistsRule:
    def test_passes_when_directory_exists(self, tmp_path):
        bids_dir = tmp_path / "bids"
        bids_dir.mkdir()

        rule = DirectoryExistsRule("bids_dir", "BIDS")
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            inputs=MockInputs(bids_dir=bids_dir),
        )

        result = rule.check(context)

        assert result.passed
        assert result.details["exists"] is True
        assert "exists" in result.message

    def test_fails_when_directory_missing(self, tmp_path):
        bids_dir = tmp_path / "nonexistent"

        rule = DirectoryExistsRule("bids_dir", "BIDS")
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            inputs=MockInputs(bids_dir=bids_dir),
        )

        result = rule.check(context)

        assert not result.passed
        assert result.severity == "error"
        assert "not found" in result.message

    def test_fails_when_path_is_file(self, tmp_path):
        bids_file = tmp_path / "bids.txt"
        bids_file.touch()

        rule = DirectoryExistsRule("bids_dir", "BIDS")
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            inputs=MockInputs(bids_dir=bids_file),
        )

        result = rule.check(context)

        assert not result.passed
        assert "not a directory" in result.message

    def test_passes_when_path_attr_is_none_and_optional(self):
        rule = DirectoryExistsRule("bids_dir", "BIDS")
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            inputs=MockInputs(bids_dir=None),
        )
        result = rule.check(context)
        assert result.passed
        assert "not specified (optional)" in result.message

    def test_fails_when_inputs_none(self):
        rule = DirectoryExistsRule("bids_dir", "BIDS")
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            inputs=None,
        )
        result = rule.check(context)
        assert not result.passed
        assert "No inputs provided" in result.message

    def test_fails_when_inputs_missing_attr(self):
        rule = DirectoryExistsRule("missing_attr", "Missing")
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            inputs=MockInputs(),  # No 'missing_attr'
        )
        result = rule.check(context)
        assert not result.passed
        assert "missing 'missing_attr' attribute" in result.message


class TestFileExistsRule:
    def test_passes_when_file_exists(self, tmp_path):
        fs_license = tmp_path / "license.txt"
        fs_license.touch()

        rule = FileExistsRule("fs_license", "FreeSurfer License", on_config=True)
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            config=MockConfig(fs_license=fs_license),
        )
        result = rule.check(context)
        assert result.passed
        assert result.details["exists"] is True

    def test_fails_when_file_missing(self, tmp_path):
        fs_license = tmp_path / "nonexistent_license.txt"

        rule = FileExistsRule("fs_license", "FreeSurfer License", on_config=True)
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            config=MockConfig(fs_license=fs_license),
        )
        result = rule.check(context)
        assert not result.passed
        assert "not found" in result.message

    def test_passes_when_file_attr_is_none(self):
        rule = FileExistsRule("fs_license", "FreeSurfer License", on_config=True)
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            config=MockConfig(fs_license=None),
        )
        result = rule.check(context)
        assert result.passed
        assert "not specified (optional)" in result.message

    def test_fails_when_path_is_directory(self, tmp_path):
        license_dir = tmp_path / "license_dir"
        license_dir.mkdir()

        rule = FileExistsRule("fs_license", "FreeSurfer License", on_config=True)
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            config=MockConfig(fs_license=license_dir),
        )
        result = rule.check(context)
        assert not result.passed
        assert "not a file" in result.message

    def test_fails_when_source_none(self):
        rule = FileExistsRule("fs_license", "FreeSurfer License", on_config=True)
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            config=None,
        )
        result = rule.check(context)
        assert not result.passed
        assert "No config provided" in result.message

    def test_fails_when_source_missing_attr(self):
        rule = FileExistsRule("missing_attr", "Missing", on_config=True)
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            config=MockConfig(),  # No 'missing_attr'
        )
        result = rule.check(context)
        assert not result.passed
        assert "Config missing 'missing_attr' attribute" in result.message


class TestParticipantExistsRule:
    def test_passes_when_participant_dir_exists(self, tmp_path):
        bids_dir = tmp_path / "bids"
        (bids_dir / "sub-01").mkdir(parents=True)

        rule = ParticipantExistsRule()
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            inputs=MockInputs(bids_dir=bids_dir),
        )
        result = rule.check(context)
        assert result.passed
        assert "Participant found" in result.message

    def test_fails_when_participant_dir_missing(self, tmp_path):
        bids_dir = tmp_path / "bids"
        bids_dir.mkdir()

        rule = ParticipantExistsRule()
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            inputs=MockInputs(bids_dir=bids_dir),
        )
        result = rule.check(context)
        assert not result.passed
        assert "Participant not found" in result.message

    def test_fails_when_input_dir_not_determinable(self):
        rule = ParticipantExistsRule()
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            inputs=MockInputs(),  # No bids_dir, dicom_dir, etc.
        )
        result = rule.check(context)
        assert not result.passed
        assert "Cannot determine input directory" in result.message

    def test_with_custom_prefix(self, tmp_path):
        bids_dir = tmp_path / "data"
        (bids_dir / "anon-01").mkdir(parents=True)

        rule = ParticipantExistsRule(prefix="anon-")
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            inputs=MockInputs(bids_dir=bids_dir),
        )
        result = rule.check(context)
        assert result.passed
        assert "anon-01" in result.details["path"]


class TestOutputDirectoryExistsRule:
    @dataclass
    class MockExpectedOutputs:
        qsiprep_dir: Optional[Path] = None

    def test_passes_when_output_dir_exists(self, tmp_path):
        output_dir = tmp_path / "derivatives" / "qsiprep"
        output_dir.mkdir(parents=True)

        rule = OutputDirectoryExistsRule("qsiprep_dir", "QSIPrep Output")
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            expected_outputs=self.MockExpectedOutputs(qsiprep_dir=output_dir),
        )
        result = rule.check(context)
        assert result.passed
        assert "created" in result.message

    def test_fails_when_output_dir_missing(self, tmp_path):
        output_dir = tmp_path / "nonexistent_output"

        rule = OutputDirectoryExistsRule("qsiprep_dir", "QSIPrep Output")
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            expected_outputs=self.MockExpectedOutputs(qsiprep_dir=output_dir),
        )
        result = rule.check(context)
        assert not result.passed
        assert "not created" in result.message

    def test_fails_when_expected_outputs_none(self):
        rule = OutputDirectoryExistsRule("qsiprep_dir", "QSIPrep Output")
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            expected_outputs=None,
        )
        result = rule.check(context)
        assert not result.passed
        assert "No expected outputs defined" in result.message

    def test_fails_when_expected_outputs_missing_attr(self):
        rule = OutputDirectoryExistsRule("missing_attr", "Missing Output")
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            expected_outputs=self.MockExpectedOutputs(),  # No 'missing_attr'
        )
        result = rule.check(context)
        assert not result.passed
        assert "missing 'missing_attr'" in result.message

    def test_fails_when_path_not_defined(self):
        rule = OutputDirectoryExistsRule("qsiprep_dir", "QSIPrep Output")
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            expected_outputs=self.MockExpectedOutputs(qsiprep_dir=None),
        )
        result = rule.check(context)
        assert not result.passed
        assert "path not defined" in result.message


class TestGlobFilesExistRule:
    @dataclass
    class MockExpectedOutputs:
        dwi_dir: Path

    def test_passes_when_files_exist(self, tmp_path):
        bids_dir = tmp_path / "bids"
        (bids_dir / "sub-01" / "dwi").mkdir(parents=True)
        (bids_dir / "sub-01" / "dwi" / "sub-01_dwi.nii.gz").touch()

        rule = GlobFilesExistRule(
            base_dir_attr="bids_dir", pattern="dwi/*_dwi.nii.gz", file_type="DWI files"
        )
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            inputs=MockInputs(bids_dir=bids_dir),
        )
        result = rule.check(context)
        assert result.passed
        assert "Found 1 DWI files" in result.message

    def test_fails_when_files_missing(self, tmp_path):
        bids_dir = tmp_path / "bids"
        # Create participant directory but no dwi files
        (bids_dir / "sub-01").mkdir(parents=True)

        rule = GlobFilesExistRule(
            base_dir_attr="bids_dir", pattern="dwi/*_dwi.nii.gz", file_type="DWI files"
        )
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            inputs=MockInputs(bids_dir=bids_dir),
        )
        result = rule.check(context)
        assert not result.passed
        assert "Found 0 DWI files" in result.message

    def test_fails_when_participant_dir_missing(self, tmp_path):
        """Test that it fails when participant directory doesn't exist."""
        bids_dir = tmp_path / "bids"
        bids_dir.mkdir()
        # No participant directory created

        rule = GlobFilesExistRule(
            base_dir_attr="bids_dir", pattern="dwi/*_dwi.nii.gz", file_type="DWI files"
        )
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            inputs=MockInputs(bids_dir=bids_dir),
        )
        result = rule.check(context)
        assert not result.passed
        assert "Participant directory does not exist" in result.message
        assert "sub-01" in result.details["expected_path"]

    def test_fails_when_base_dir_missing(self, tmp_path):
        rule = GlobFilesExistRule(
            base_dir_attr="nonexistent_dir", pattern="*", file_type="Files"
        )
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            inputs=MockInputs(),  # No 'nonexistent_dir'
        )
        result = rule.check(context)
        assert not result.passed
        assert "Cannot determine base directory" in result.message

    def test_fails_when_base_dir_does_not_exist(self, tmp_path):
        bids_dir = tmp_path / "nonexistent"
        rule = GlobFilesExistRule(
            base_dir_attr="bids_dir", pattern="*", file_type="Files"
        )
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            inputs=MockInputs(bids_dir=bids_dir),
        )
        result = rule.check(context)
        assert not result.passed
        assert "Base directory does not exist" in result.message

    def test_search_dir_with_session(self, tmp_path):
        bids_dir = tmp_path / "bids"
        (bids_dir / "sub-01" / "ses-01" / "dwi").mkdir(parents=True)
        (bids_dir / "sub-01" / "ses-01" / "dwi" / "sub-01_ses-01_dwi.nii.gz").touch()

        rule = GlobFilesExistRule(
            base_dir_attr="bids_dir", pattern="dwi/*_dwi.nii.gz", file_type="DWI files"
        )
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            session="01",
            inputs=MockInputs(bids_dir=bids_dir),
        )
        result = rule.check(context)
        assert result.passed
        assert "Found 1 DWI files" in result.message

    def test_base_dir_attr_from_expected_outputs(self, tmp_path):
        output_dir = tmp_path / "derivatives"
        (output_dir / "sub-01" / "dwi").mkdir(parents=True)
        (output_dir / "sub-01" / "dwi" / "sub-01_dwi.nii.gz").touch()

        @dataclass
        class MockExpectedOutputsWithDwiDir:
            dwi_dir: Path

        rule = GlobFilesExistRule(
            base_dir_attr="dwi_dir",
            pattern="sub-01_dwi.nii.gz",
            file_type="DWI files",
            phase="post",
            participant_level=False,  # base_dir is already participant-specific
        )
        context = ValidationContext(
            procedure_name="test",
            participant="01",
            expected_outputs=MockExpectedOutputsWithDwiDir(
                dwi_dir=output_dir / "sub-01" / "dwi"
            ),
            inputs=MockInputs(),  # no bids_dir to avoid precedence issues
        )
        result = rule.check(context)
        assert result.passed
        assert "Found 1 DWI files" in result.message
