"""Base classes for the validation framework."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Literal, Optional

if TYPE_CHECKING:
    from voxelops.validation.context import ValidationContext


@dataclass
class ValidationResult:
    """Result of a single validation rule check.

    This is the atomic unit of validation - one rule, one outcome.
    Designed to be easily serializable for database storage.
    """

    rule_name: str
    rule_description: str
    passed: bool
    severity: Literal["error", "warning", "info"]
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "rule_name": self.rule_name,
            "rule_description": self.rule_description,
            "passed": self.passed,
            "severity": self.severity,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


class ValidationRule(ABC):
    """Abstract base class for validation rules.

    Subclass this to create specific validation checks.
    Each rule should check ONE thing and return a clear result.
    """

    # These must be set by subclasses
    name: str = "unnamed_rule"
    description: str = "No description provided"
    severity: Literal["error", "warning", "info"] = "error"
    phase: Literal["pre", "post"] = "pre"

    @abstractmethod
    def check(self, context: "ValidationContext") -> ValidationResult:
        """Execute the validation check.

        Parameters
        ----------
        context : ValidationContext
            Contains all information needed for validation.

        Returns
        -------
        ValidationResult
            The outcome of this check.
        """
        pass

    def skip_condition(self, context: "ValidationContext") -> bool:
        """Return True to skip this rule for this context.

        Override this method for rules that only apply conditionally.
        For example, a FreeSurfer check might skip if FS isn't required.
        """
        return False

    def _pass(self, message: str, details: Dict[str, Any] = None) -> ValidationResult:
        """Helper to create a passing result."""
        return ValidationResult(
            rule_name=self.name,
            rule_description=self.description,
            passed=True,
            severity=self.severity,
            message=message,
            details=details or {},
        )

    def _fail(self, message: str, details: Dict[str, Any] = None) -> ValidationResult:
        """Helper to create a failing result."""
        return ValidationResult(
            rule_name=self.name,
            rule_description=self.description,
            passed=False,
            severity=self.severity,
            message=message,
            details=details or {},
        )


@dataclass
class ValidationReport:
    """Complete validation report for a phase (pre or post).

    Aggregates multiple ValidationResults and provides summary methods.
    """

    phase: Literal["pre", "post"]
    procedure: str
    participant: str
    session: Optional[str]
    timestamp: datetime = field(default_factory=datetime.now)
    results: List[ValidationResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """True if no errors occurred (warnings are OK)."""
        return all(r.passed or r.severity != "error" for r in self.results)

    @property
    def errors(self) -> List[ValidationResult]:
        """Get all failed error-severity results."""
        return [r for r in self.results if not r.passed and r.severity == "error"]

    @property
    def warnings(self) -> List[ValidationResult]:
        """Get all failed warning-severity results."""
        return [r for r in self.results if not r.passed and r.severity == "warning"]

    @property
    def passed_checks(self) -> List[ValidationResult]:
        """Get all passed results."""
        return [r for r in self.results if r.passed]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "phase": self.phase,
            "procedure": self.procedure,
            "participant": self.participant,
            "session": self.session,
            "timestamp": self.timestamp.isoformat(),
            "passed": self.passed,
            "total_checks": len(self.results),
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "passed_count": len(self.passed_checks),
            "results": [r.to_dict() for r in self.results],
        }

    def summary(self) -> str:
        """Get a human-readable summary."""
        status = "PASSED" if self.passed else "FAILED"
        return (
            f"{self.phase.upper()} validation {status}: "
            f"{len(self.passed_checks)} passed, "
            f"{len(self.errors)} errors, "
            f"{len(self.warnings)} warnings"
        )
