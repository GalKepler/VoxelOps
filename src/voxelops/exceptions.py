"""Custom exceptions for yalab-procedures.

This module defines a hierarchy of exceptions for consistent error handling
across all procedures in the yalab-procedures package.
"""

from typing import Optional


class YALabProcedureError(Exception):
    """Base exception for all yalab-procedures errors.

    All custom exceptions in this package inherit from this class,
    allowing callers to catch all yalab-procedures errors with a single
    except clause if desired.
    """

    pass


class ProcedureExecutionError(YALabProcedureError):
    """Raised when a procedure fails during execution.

    Parameters
    ----------
    procedure_name : str
        Name of the procedure that failed.
    message : str
        The error message.
    original_error : Optional[Exception], optional
        The underlying exception that caused the failure, if any, by default None.
    """

    def __init__(
        self,
        procedure_name: str,
        message: str,
        original_error: Optional[Exception] = None,
    ):
        self.procedure_name = procedure_name
        self.original_error = original_error
        super().__init__(f"{procedure_name} failed: {message}")


class ProcedureConfigurationError(YALabProcedureError):
    """Raised when procedure configuration is invalid.

    This includes missing required inputs, invalid input combinations,
    or configuration that cannot be used together.
    """

    pass


class InputValidationError(YALabProcedureError):
    """Raised when input validation fails.

    This is raised during pre-flight checks when inputs don't meet
    the requirements for procedure execution.
    """

    pass


class OutputCollectionError(YALabProcedureError):
    """Raised when expected outputs are not found after procedure execution.

    This indicates the procedure may have failed silently or produced
    unexpected output structure.
    """

    pass


class DockerExecutionError(ProcedureExecutionError):
    """Raised when a Docker-based procedure fails.

    Parameters
    ----------
    procedure_name : str
        Name of the procedure that failed.
    container : str
        The Docker image/container that was running.
    exit_code : int
        The exit code returned by the Docker container.
    stderr : str
        Standard error output from the container.
    """

    def __init__(
        self,
        procedure_name: str,
        container: str,
        exit_code: int,
        stderr: str,
    ):
        self.container = container
        self.exit_code = exit_code
        self.stderr = stderr
        message = f"Docker container '{container}' exited with code {exit_code}"
        if stderr:
            # Truncate very long stderr for the message
            stderr_preview = stderr[:500] + "..." if len(stderr) > 500 else stderr
            message += f": {stderr_preview}"
        super().__init__(procedure_name, message)


class FreeSurferLicenseError(ProcedureConfigurationError):
    """Raised when FreeSurfer license file cannot be found.

    This is a specific configuration error for procedures that require
    FreeSurfer and cannot locate a valid license file.
    """

    def __init__(self, message: Optional[str] = None):
        if message is None:
            message = (
                "FreeSurfer license not found. Set FS_LICENSE or FREESURFER_HOME "
                "environment variable, or provide fs_license_file parameter."
            )
        super().__init__(message)


class BIDSValidationError(YALabProcedureError):
    """Raised when BIDS dataset validation fails.

    This indicates the input data does not conform to BIDS specification
    requirements for the procedure.
    """



    pass


class DependencyError(YALabProcedureError):
    """Raised when a required external dependency is not available.

    This includes missing Docker, missing command-line tools, or
    unavailable Python packages.
    
    Parameters
    ----------
    dependency : str
        The name of the missing dependency.
    message : Optional[str], optional
        The error message, by default None.
    """

    def __init__(self, dependency: str, message: Optional[str] = None):
        self.dependency = dependency
        if message is None:
            message = f"Required dependency '{dependency}' is not available"
        super().__init__(message)


# Alias for backwards compatibility
ProcedureError = YALabProcedureError
