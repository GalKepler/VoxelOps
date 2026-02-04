"""Common validation rules used across multiple procedures.

This module provides reusable validation rules that can be used across
different neuroimaging procedures. Each rule is designed to be composable,
allowing validators to mix and match rules as needed.

Available Rules
---------------
- DirectoryExistsRule: Check that an input directory exists
- FileExistsRule: Check that an input or config file exists
- ParticipantExistsRule: Check that participant directory exists in input
- OutputDirectoryExistsRule: Post-validation check for output directory
- GlobFilesExistRule: Check that files matching a pattern exist
- ExpectedOutputsExistRule: Generic post-validation for various output structures

Examples
--------
Pre-validation example:

>>> from voxelops.validation.rules.common import DirectoryExistsRule
>>> from voxelops.validation.context import ValidationContext
>>>
>>> rule = DirectoryExistsRule("bids_dir", "BIDS directory")
>>> context = ValidationContext(
...     procedure_name="qsiprep",
...     participant="01",
...     inputs=inputs,
... )
>>> result = rule.check(context)
>>> print(result.passed)

Post-validation example:

>>> from voxelops.validation.rules.common import ExpectedOutputsExistRule
>>>
>>> rule = ExpectedOutputsExistRule(
...     outputs_attr="html_report",
...     item_type="HTML report",
... )
>>> context.expected_outputs = expected_outputs
>>> result = rule.check(context)
"""

from pathlib import Path
from typing import Optional

from voxelops.validation.base import ValidationResult, ValidationRule
from voxelops.validation.context import ValidationContext


class DirectoryExistsRule(ValidationRule):
    """Check that a directory exists on the inputs object.

    This is typically used in pre-validation to ensure input directories
    exist before execution begins.

    Parameters
    ----------
    path_attr : str
        Attribute name on inputs to check (e.g., 'bids_dir', 'dicom_dir').
        The rule will look for this attribute on context.inputs.
    dir_type : str, optional
        Human-readable directory type for error messages (default: "Input").
        Example: "BIDS directory", "QSIPrep output directory"
    severity : {"error", "warning"}, optional
        Validation severity level (default: "error").
        - "error": Execution will not proceed if check fails
        - "warning": Check failure is logged but doesn't block execution

    Attributes
    ----------
    name : str
        Rule name in format "{path_attr}_exists"
    description : str
        Human-readable description
    phase : str
        Always "pre" for this rule

    Examples
    --------
    >>> # Check BIDS directory exists
    >>> rule = DirectoryExistsRule("bids_dir", "BIDS directory")
    >>>
    >>> # Check with warning severity (won't block execution)
    >>> rule = DirectoryExistsRule(
    ...     "work_dir",
    ...     "Working directory",
    ...     severity="warning"
    ... )

    Notes
    -----
    - Returns passing result if path is None (for optional inputs)
    - Checks both that path exists AND that it's a directory (not a file)
    """

    def __init__(
        self,
        path_attr: str,
        dir_type: str = "Input",
        severity: str = "error",
    ):
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
    """Check that files matching a glob pattern exist.

    This flexible rule can be used for both pre- and post-validation to verify
    that required files exist. It supports both BIDS-structured participant-level
    searches and flat directory searches.

    Parameters
    ----------
    base_dir_attr : str
        Attribute name for the base directory to search in.
        For pre-validation: usually "bids_dir", "qsiprep_dir", etc. from inputs
        For post-validation: usually "output_dir", "participant_dir" from expected_outputs
    pattern : str
        Glob pattern to match files (e.g., "**/dwi/*.nii.gz", "**/*.html").
        Patterns are relative to the search directory.
    min_count : int, optional
        Minimum number of files required (default: 1).
        Set to 0 to allow zero matches.
    file_type : str, optional
        Human-readable file type for error messages (default: "Files").
        Example: "DWI images", "HTML reports"
    severity : {"error", "warning"}, optional
        Validation severity level (default: "error").
    phase : {"pre", "post"}, optional
        Validation phase (default: "pre").
    participant_level : bool, optional
        Whether to search in participant-specific subdirectory (default: True).

        - True: Searches in base_dir/sub-{participant}/ses-{session}/ (or without ses- if no session)
          Use for pre-validation of BIDS-structured inputs
        - False: Searches directly in base_dir
          Use for post-validation when base_dir is already participant-specific

    Attributes
    ----------
    name : str
        Rule name derived from file_type
    description : str
        Description including the glob pattern

    Examples
    --------
    Pre-validation for BIDS inputs (participant_level=True):

    >>> # Check for DWI files in BIDS structure
    >>> rule = GlobFilesExistRule(
    ...     base_dir_attr="bids_dir",
    ...     pattern="**/dwi/*_dwi.nii.gz",
    ...     min_count=1,
    ...     file_type="DWI images",
    ...     participant_level=True,  # Searches in bids_dir/sub-01/
    ... )

    Post-validation for outputs (participant_level=False):

    >>> # Check for output files (output_dir is already participant-specific)
    >>> rule = GlobFilesExistRule(
    ...     base_dir_attr="output_dir",
    ...     pattern="**/*.nii.gz",
    ...     min_count=1,
    ...     file_type="Output images",
    ...     phase="post",
    ...     participant_level=False,  # output_dir is already sub-01/
    ... )

    QSIRecon derivative structure (participant_level=False):

    >>> # Check QSIRecon derivative outputs
    >>> rule = GlobFilesExistRule(
    ...     base_dir_attr="qsirecon_dir",
    ...     pattern="derivatives/qsirecon-*/**/dwi/*.nii.gz",
    ...     min_count=1,
    ...     file_type="Reconstruction outputs",
    ...     participant_level=False,  # Pattern includes full path structure
    ... )

    Notes
    -----
    - For participant_level=True, the participant directory must exist (fails if missing)
    - For participant_level=False, searches directly in base_dir (no participant filtering)
    - Found files are reported as names only (not full paths) for cleaner output
    - Session support: automatically includes session in path when context.session is set
    """

    def __init__(
        self,
        base_dir_attr: str,
        pattern: str,
        min_count: int = 1,
        file_type: str = "Files",
        severity: str = "error",
        phase: str = "pre",
        participant_level: bool = True,
    ):
        self.base_dir_attr = base_dir_attr
        self.pattern = pattern
        self.min_count = min_count
        self.file_type = file_type
        self.participant_level = participant_level
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

        # Build search path with participant/session if needed
        if self.participant_level:
            # For BIDS-root directories, append participant/session
            search_dir = base_dir / context.participant_label
            if context.session:
                search_dir = search_dir / context.session_label

            # Participant/session directory must exist
            # This ensures we only check files for the specific participant being processed
            if not search_dir.exists():
                return self._fail(
                    f"Participant directory does not exist: {search_dir}",
                    {
                        "base_dir": str(base_dir),
                        "participant": context.participant,
                        "session": context.session,
                        "expected_path": str(search_dir),
                    },
                )
        else:
            # base_dir is already participant-specific (e.g., post-validation outputs)
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


class ExpectedOutputsExistRule(ValidationRule):
    """Generic post-validation rule to check if expected outputs exist.

    This flexible rule can validate various output structures, automatically
    adapting to the type of output (single file, flat dictionary, or nested
    dictionary). This eliminates the need for separate rules for different
    output patterns.

    Supported Output Structures
    ----------------------------
    1. **Single Path**: A single file or directory
       Example: ``html_report: Path("/out/sub-01.html")``

    2. **Flat Dictionary**: Simple mapping of keys to paths
       Example: ``session_outputs: {"baseline": Path("/out/baseline.txt")}``

    3. **Nested Dictionary**: Two-level mapping (e.g., workflow × session)
       Example: ``workflow_reports: {"mrtrix": {"01": Path("/out/01.html")}}``

    Parameters
    ----------
    outputs_attr : str
        Attribute name on expected_outputs to check.
        Examples: 'html_report', 'workflow_reports', 'workflow_dirs'
    item_type : str
        Human-readable description for error messages.
        Examples: 'HTML report', 'workflow reports', 'workflow directories'
    severity : {"error", "warning"}, optional
        Validation severity level (default: "error").
    flatten_nested : bool, optional
        Whether to expect nested dictionary structure (default: False).

        - False: Expects single Path or flat dict {key: path}
        - True: Expects nested dict {key1: {key2: path}}

    Attributes
    ----------
    name : str
        Rule name in format "{outputs_attr}_exist"
    description : str
        Description of what's being checked
    phase : str
        Always "post" for this rule

    Examples
    --------
    Single file output:

    >>> # QSIPrep HTML report
    >>> rule = ExpectedOutputsExistRule(
    ...     outputs_attr="html_report",
    ...     item_type="HTML report",
    ... )
    >>> # Expects: expected_outputs.html_report = Path("/out/sub-01.html")

    Flat dictionary (session outputs):

    >>> # Session-specific outputs
    >>> rule = ExpectedOutputsExistRule(
    ...     outputs_attr="session_outputs",
    ...     item_type="session outputs",
    ...     flatten_nested=False,
    ... )
    >>> # Expects: expected_outputs.session_outputs = {
    >>> #     "baseline": Path("/out/baseline.nii.gz"),
    >>> #     "followup": Path("/out/followup.nii.gz"),
    >>> # }

    Nested dictionary (workflow × session):

    >>> # QSIRecon workflow reports
    >>> rule = ExpectedOutputsExistRule(
    ...     outputs_attr="workflow_reports",
    ...     item_type="workflow HTML reports",
    ...     flatten_nested=True,
    ... )
    >>> # Expects: expected_outputs.workflow_reports = {
    >>> #     "mrtrix": {"01": Path("/out/mrtrix/sub-01_ses-01.html")},
    >>> #     "dipy": {"01": Path("/out/dipy/sub-01_ses-01.html")},
    >>> # }

    Notes
    -----
    - Automatically detects the output structure type
    - For nested dicts, reports missing items as "workflow/session"
    - Missing files are reported with their expected paths
    - Found files are summarized by count for brevity
    - This rule replaces many specialized output-checking rules
    """

    def __init__(
        self,
        outputs_attr: str,
        item_type: str,
        severity: str = "error",
        flatten_nested: bool = False,
    ):
        self.outputs_attr = outputs_attr
        self.item_type = item_type
        self.flatten_nested = flatten_nested
        self.name = f"{outputs_attr}_exist"
        self.description = f"Check {item_type} exist"
        self.severity = severity

    def check(self, context: ValidationContext) -> ValidationResult:
        """Check that all expected outputs exist."""
        if not context.expected_outputs:
            return self._fail("No expected outputs available")

        if not hasattr(context.expected_outputs, self.outputs_attr):
            return self._fail(
                f"Expected outputs missing attribute: {self.outputs_attr}"
            )

        outputs = getattr(context.expected_outputs, self.outputs_attr)

        # Handle single path
        if isinstance(outputs, Path):
            if outputs.exists():
                return self._pass(
                    f"{self.item_type} exists: {outputs}",
                    details={self.outputs_attr: str(outputs)},
                )
            else:
                return self._fail(
                    f"{self.item_type} not found: {outputs}",
                    details={self.outputs_attr: str(outputs)},
                )

        # Handle dictionary structures
        missing_items = []
        found_items = []

        if self.flatten_nested:
            # Nested dictionary: {workflow: {session: path}}
            for key1, sub_dict in outputs.items():
                for key2, path in sub_dict.items():
                    key2_label = f"{key2}" if key2 else "no-session"
                    item_label = f"{key1}/{key2_label}"

                    if path.exists():
                        found_items.append(item_label)
                    else:
                        missing_items.append(f"{item_label} ({path})")
        else:
            # Flat dictionary: {key: path}
            for key, path in outputs.items():
                if path.exists():
                    found_items.append(key)
                else:
                    missing_items.append(f"{key} ({path})")

        if missing_items:
            return self._fail(
                f"Missing {len(missing_items)} {self.item_type}",
                details={
                    "missing": missing_items,
                    "found": found_items,
                },
            )

        return self._pass(
            f"All {len(found_items)} {self.item_type} exist",
            details={"found": found_items},
        )
