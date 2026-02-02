"""Base utilities for all procedure runners."""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from voxelops.exceptions import (
    InputValidationError,
    ProcedureExecutionError,
)


def validate_input_dir(input_dir: Path, dir_type: str = "Input") -> None:
    """Validate that an input directory exists.

    Parameters
    ----------
    input_dir : Path
        Directory to validate.
    dir_type : str, optional
        Type of directory for error message, by default "Input".

    Raises
    ------
    InputValidationError
        If directory doesn't exist.
    """
    if not input_dir.exists():
        raise InputValidationError(f"{dir_type} directory not found: {input_dir}")

    if not input_dir.is_dir():
        raise InputValidationError(f"{dir_type} path is not a directory: {input_dir}")


def validate_participant(
    input_dir: Path, participant: str, prefix: str = "sub-"
) -> None:
    """Validate that a participant exists in the input directory.

    Parameters
    ----------
    input_dir : Path
        Directory containing participant data.
    participant : str
        Participant label (without prefix).
    prefix : str, optional
        Expected prefix, by default "sub-".

    Raises
    ------
    InputValidationError
        If participant not found.
    """
    participant_dir = input_dir / f"{prefix}{participant}"
    if not participant_dir.exists():
        raise InputValidationError(
            f"Participant {prefix}{participant} not found in {input_dir}"
        )


def run_docker(
    cmd: List[str],
    tool_name: str,
    participant: str,
    log_dir: Optional[Path] = None,
    capture_output: bool = True,
) -> Dict[str, Any]:
    """Execute Docker command and return execution record.

    Parameters
    ----------
    cmd : List[str]
        Docker command as list of strings.
    tool_name : str
        Name of the tool being run (for logging).
    participant : str
        Participant label.
    log_dir : Optional[Path], optional
        Directory to save execution log JSON, by default None.
    capture_output : bool, optional
        Whether to capture stdout/stderr, by default True.

    Returns
    -------
    Dict[str, Any]
        A dictionary with execution details:
            - tool: Tool name
            - participant: Participant label
            - command: Full command that was executed
            - exit_code: Process exit code
            - start_time: ISO format timestamp
            - end_time: ISO format timestamp
            - duration_seconds: Duration in seconds
            - duration_human: Human-readable duration
            - success: Boolean success status
            - log_file: Path to JSON log (if log_dir provided)
            - stdout: Process stdout (if captured)
            - stderr: Process stderr (if captured)
            - error: Error message (if failed)

    Raises
    ------
    ProcedureExecutionError
        If command fails.
    """
    # Setup logging
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"{tool_name}_{participant}_{timestamp}.json"
    else:
        log_file = None

    print(f"\n{'='*80}")
    print(f"Running {tool_name} for participant {participant}")
    print(f"{'='*80}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*80}\n")

    start_time = datetime.now()

    try:
        result = subprocess.run(
            cmd, capture_output=capture_output, text=True, check=False
        )

        end_time = datetime.now()
        duration = end_time - start_time

        # Build execution record
        record = {
            "tool": tool_name,
            "participant": participant,
            "command": cmd,
            "exit_code": result.returncode,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "duration_seconds": duration.total_seconds(),
            "duration_human": str(duration),
            "success": result.returncode == 0,
        }

        if capture_output:
            record["stdout"] = result.stdout
            record["stderr"] = result.stderr

        # Save to JSON log
        if log_file:
            record["log_file"] = str(log_file)
            with open(log_file, "w") as f:
                json.dump(record, f, indent=2)
            print(f"Execution log saved: {log_file}")

        # Check for errors
        if result.returncode != 0:
            error_msg = f"{tool_name} failed with exit code {result.returncode}"
            if capture_output and result.stderr:
                error_msg += f"\n\nStderr (last 1000 chars):\n{result.stderr[-1000:]}"

            record["error"] = error_msg

            # Update log file with error
            if log_file:
                with open(log_file, "w") as f:
                    json.dump(record, f, indent=2)

            raise ProcedureExecutionError(
                procedure_name=tool_name,
                message=error_msg,
            )

        print(f"\n{'='*80}")
        print(f"✓ {tool_name} completed successfully")
        print(f"Duration: {duration}")
        print(f"{'='*80}\n")

        return record

    except subprocess.TimeoutExpired as e:
        raise ProcedureExecutionError(
            procedure_name=tool_name,
            message=f"Process timed out after {e.timeout} seconds",
        )
    except Exception as e:
        if not isinstance(e, ProcedureExecutionError):
            raise ProcedureExecutionError(
                procedure_name=tool_name, message=str(e), original_error=e
            )
        raise
