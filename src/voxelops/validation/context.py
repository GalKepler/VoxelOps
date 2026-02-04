"""Validation context - holds all information needed for validation checks."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class ValidationContext:
    """All information needed for validation checks.

    This is passed to every validation rule, providing access to:
    - Procedure identification (name, participant, session)
    - Input schemas (procedure-specific)
    - Configuration (procedure-specific defaults)
    - Expected outputs (for post-validation)
    - Execution results (for post-validation)
    """

    # Procedure identification
    procedure_name: str
    participant: str
    session: str | None = None

    # Inputs and config (type depends on procedure)
    inputs: Any = None
    config: Any = None
    expected_outputs: Any = None

    # For post-validation
    execution_result: dict[str, Any] | None = None

    # Optional brain bank config
    brain_bank_config: dict[str, Any] | None = None

    @property
    def input_dir(self) -> Path | None:
        """Get the primary input directory based on procedure type."""
        if self.inputs is None:
            return None

        # Try common input directory attributes
        for attr in ["bids_dir", "dicom_dir", "qsiprep_dir", "qsirecon_dir"]:
            if hasattr(self.inputs, attr):
                value = getattr(self.inputs, attr)
                if value is not None:
                    return Path(value)
        return None

    @property
    def output_dir(self) -> Path | None:
        """Get the output directory."""
        if self.inputs is None:
            return None

        if hasattr(self.inputs, "output_dir") and self.inputs.output_dir:
            return Path(self.inputs.output_dir)
        return None

    @property
    def participant_label(self) -> str:
        """Participant label with 'sub-' prefix."""
        return f"sub-{self.participant}"

    @property
    def session_label(self) -> str | None:
        """Session label with 'ses-' prefix, if session exists."""
        return f"ses-{self.session}" if self.session else None

    @property
    def participant_dir(self) -> Path | None:
        """Get participant directory in input."""
        if self.input_dir is None:
            return None

        participant_dir = self.input_dir / self.participant_label
        if self.session:
            participant_dir = participant_dir / self.session_label
        return participant_dir

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get a value from brain bank config or procedure config."""
        # First check brain bank config
        if self.brain_bank_config:
            # Check procedure-specific config
            proc_config = self.brain_bank_config.get(self.procedure_name, {})
            if key in proc_config:
                return proc_config[key]
            # Check global config
            if key in self.brain_bank_config:
                return self.brain_bank_config[key]

        # Then check procedure config
        if self.config and hasattr(self.config, key):
            return getattr(self.config, key)

        return default
