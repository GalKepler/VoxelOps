"""Common validation rules used across multiple procedures."""

from pathlib import Path
from typing import Optional

from voxelops.validation.base import ValidationResult, ValidationRule
from voxelops.validation.context import ValidationContext


class DirectoryExistsRule(ValidationRule):
    """Check that a directory exists."""

    def __init__(
        self,
        path_attr: str,
        dir_type: str = "Input",
        severity: str = "error",
    ):
        """
        Parameters
        ----------
        path_attr : str
            Attribute name on inputs to check (e.g., 'bids_dir', 'dicom_dir')
        dir_type : str
            Human-readable type for error messages
        severity : str
            "error" or "warning"
        """
        self.path_attr = path_attr
        self.dir_type = dir_type
        self.name = f"{path_attr}_exists"
        self.description = f"Verify {dir_type} directory exists"
        self.severity = severity
        self.phase = "pre"

    def check(self, context: ValidationContext) -> ValidationResult:
        if context.inputs is None:
            return self._fail("No inputs provided", {"path_attr": self.path_attr})

        if not hasattr(context.inputs, self.path_attr):
            return self._fail(
                f"Inputs missing '{self.path_attr}' attribute",
                {"path_attr": self.path_attr},
            )

        path = getattr(context.inputs, self.path_attr)
        if path is None:
            return self._pass(  # Changed to _pass as None is acceptable for optional paths.
                f"{self.dir_type} directory not specified (optional)",
                {"path_attr": self.path_attr, "value": None},
            )

        path = Path(path)
        if not path.exists():
            return self._fail(
                f"{self.dir_type} directory not found: {path}",
                {"path": str(path), "exists": False},
            )

        if not path.is_dir():
            return self._fail(
                f"{self.dir_type} path is not a directory: {path}",
                {"path": str(path), "is_dir": False},
            )

        return self._pass(
            f"{self.dir_type} directory exists: {path}",
            {"path": str(path), "exists": True},
        )


class FileExistsRule(ValidationRule):
    """Check that a file exists."""

    def __init__(
        self,
        path_attr: str,
        file_type: str = "File",
        severity: str = "error",
        on_config: bool = False,
    ):
        """
        Parameters
        ----------
        path_attr : str
            Attribute name to check
        file_type : str
            Human-readable type for error messages
        severity : str
            "error" or "warning"
        on_config : bool
            If True, look for attr on config instead of inputs
        """
        self.path_attr = path_attr
        self.file_type = file_type
        self.on_config = on_config
        self.name = f"{path_attr}_exists"
        self.description = f"Verify {file_type} file exists"
        self.severity = severity
        self.phase = "pre"

    def check(self, context: ValidationContext) -> ValidationResult:
        source = context.config if self.on_config else context.inputs
        source_name = "config" if self.on_config else "inputs"

        if source is None:
            return self._fail(
                f"No {source_name} provided", {"path_attr": self.path_attr}
            )

        if not hasattr(source, self.path_attr):
            return self._fail(
                f"{source_name.capitalize()} missing '{self.path_attr}' attribute",
                {"path_attr": self.path_attr},
            )

        path = getattr(source, self.path_attr)
        if path is None:
            # For optional files, None is OK
            return self._pass(
                f"{self.file_type} not specified (optional)",
                {"path_attr": self.path_attr, "value": None},
            )

        path = Path(path)
        if not path.exists():
            return self._fail(
                f"{self.file_type} not found: {path}",
                {"path": str(path), "exists": False},
            )

        if not path.is_file():
            return self._fail(
                f"{self.file_type} path is not a file: {path}",
                {"path": str(path), "is_file": False},
            )

        return self._pass(
            f"{self.file_type} exists: {path}", {"path": str(path), "exists": True}
        )


class ParticipantExistsRule(ValidationRule):
    """Check that participant directory exists in input."""

    name = "participant_exists"
    description = "Verify participant exists in input directory"
    severity = "error"
    phase = "pre"

    def __init__(self, prefix: str = "sub-"):
        self.prefix = prefix

    def check(self, context: ValidationContext) -> ValidationResult:
        input_dir = context.input_dir
        if input_dir is None:
            return self._fail(
                "Cannot determine input directory", {"participant": context.participant}
            )

        participant_dir = input_dir / f"{self.prefix}{context.participant}"

        if not participant_dir.exists():
            return self._fail(
                f"Participant not found: {participant_dir}",
                {
                    "participant": context.participant,
                    "expected_path": str(participant_dir),
                    "exists": False,
                },
            )

        return self._pass(
            f"Participant found: {participant_dir}",
            {
                "participant": context.participant,
                "path": str(participant_dir),
                "exists": True,
            },
        )


class OutputDirectoryExistsRule(ValidationRule):
    """Post-validation: Check that output directory was created."""

    def __init__(self, output_attr: str, output_type: str = "Output"):
        self.output_attr = output_attr
        self.output_type = output_type
        self.name = f"{output_attr}_created"
        self.description = f"Verify {output_type} directory was created"
        self.severity = "error"
        self.phase = "post"

    def check(self, context: ValidationContext) -> ValidationResult:
        if context.expected_outputs is None:
            return self._fail(
                "No expected outputs defined", {"output_attr": self.output_attr}
            )

        if not hasattr(context.expected_outputs, self.output_attr):
            return self._fail(
                f"Expected outputs missing '{self.output_attr}'",
                {"output_attr": self.output_attr},
            )

        path = getattr(context.expected_outputs, self.output_attr)
        if path is None:
            return self._fail(
                f"{self.output_type} path not defined",
                {"output_attr": self.output_attr},
            )

        path = Path(path)
        if not path.exists():
            return self._fail(
                f"{self.output_type} not created: {path}",
                {"path": str(path), "exists": False},
            )

        return self._pass(
            f"{self.output_type} created: {path}", {"path": str(path), "exists": True}
        )


class GlobFilesExistRule(ValidationRule):
    """Check that files matching a glob pattern exist."""

    def __init__(
        self,
        base_dir_attr: str,
        pattern: str,
        min_count: int = 1,
        file_type: str = "Files",
        severity: str = "error",
        phase: str = "pre",
    ):
        self.base_dir_attr = base_dir_attr
        self.pattern = pattern
        self.min_count = min_count
        self.file_type = file_type
        self.name = f"{file_type.lower().replace(' ', '_')}_exist"
        self.description = f"Verify {file_type} exist (pattern: {pattern})"
        self.severity = severity
        self.phase = phase

    def _get_base_dir(self, context: ValidationContext) -> Optional[Path]:
        """Get the base directory to search in."""
        # Try inputs first
        if context.inputs and hasattr(context.inputs, self.base_dir_attr):
            return Path(getattr(context.inputs, self.base_dir_attr))

        # Try expected_outputs for post-validation
        if context.expected_outputs and hasattr(
            context.expected_outputs, self.base_dir_attr
        ):
            return Path(getattr(context.expected_outputs, self.base_dir_attr))

        # Fallback to input_dir
        return context.input_dir

    def check(self, context: ValidationContext) -> ValidationResult:
        base_dir = self._get_base_dir(context)

        if base_dir is None:
            return self._fail(
                f"Cannot determine base directory for {self.file_type}",
                {"base_dir_attr": self.base_dir_attr},
            )

        if not base_dir.exists():
            return self._fail(
                f"Base directory does not exist: {base_dir}",
                {"base_dir": str(base_dir), "pattern": self.pattern},
            )

        # Build search path with participant/session
        search_dir = base_dir / context.participant_label
        if context.session:
            search_dir = search_dir / context.session_label

        # If search_dir doesn't exist, try base_dir directly
        if not search_dir.exists():
            search_dir = base_dir

        found_files = list(search_dir.glob(self.pattern))

        if len(found_files) < self.min_count:
            return self._fail(
                f"Found {len(found_files)} {self.file_type}, required {self.min_count}",
                {
                    "pattern": self.pattern,
                    "search_dir": str(search_dir),
                    "found_count": len(found_files),
                    "required_count": self.min_count,
                    "found_files": [str(f.name) for f in found_files],
                },
            )

        return self._pass(
            f"Found {len(found_files)} {self.file_type}",
            {
                "pattern": self.pattern,
                "found_count": len(found_files),
                "found_files": [str(f.name) for f in found_files],
            },
        )
