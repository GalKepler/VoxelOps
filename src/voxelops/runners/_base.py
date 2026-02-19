"""Base utilities for all procedure runners."""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from voxelops.exceptions import (
    DependencyError,
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


def _get_image(cmd: list[str]) -> str:
    """Parse the image (docker image) from a command list.

    Skips all ``docker run`` flags and their arguments to find the first
    positional argument, which is the image name.

    Parameters
    ----------
    cmd : list[str]
        Command list, e.g. ["docker", "run", "--rm", "-v", "/a:/b",
        "myimage:latest", "--arg1", "val"]

    Returns
    -------
    str
        The Docker image name (e.g. ``"nipy/heudiconv:1.3.4"``).

    Raises
    ------
    InputValidationError
        If the image name cannot be found in the command.
    """
    try:
        run_idx = cmd.index("run")
    except ValueError as e:
        raise InputValidationError(
            f"Not a valid docker run command: {' '.join(cmd)}"
        ) from e

    # Docker run flags that consume a following argument.
    flags_with_args = {
        "-e",
        "--env",
        "-m",
        "--memory",
        "-p",
        "--publish",
        "-u",
        "--user",
        "-v",
        "--volume",
        "-w",
        "--workdir",
        "--cpus",
        "--entrypoint",
        "--gpus",
        "--log-driver",
        "--log-opt",
        "--mount",
        "--name",
        "--network",
        "--pid",
        "--platform",
        "--shm-size",
        "--tmpfs",
    }

    i = run_idx + 1
    while i < len(cmd):
        arg = cmd[i]
        if arg.startswith("--") and "=" in arg:
            # --flag=value form – skip
            i += 1
        elif arg in flags_with_args:
            # Skip the flag and its value
            i += 2
        elif arg.startswith("-"):
            # Standalone flag (e.g. --rm, -it, -d)
            i += 1
        else:
            return arg

    raise InputValidationError(
        f"Could not find Docker image in command: {' '.join(cmd)}"
    )


def ensure_docker_image(cmd: list[str]) -> str:
    """Ensure the Docker image required by *cmd* is available locally.

    Inspects the local Docker daemon for the image. If the image is not
    found, it is pulled automatically.

    Parameters
    ----------
    cmd : list[str]
        A ``docker run …`` command list from which the image name is
        extracted.

    Returns
    -------
    str
        The Docker image name that was validated / pulled.

    Raises
    ------
    DependencyError
        If the image cannot be found locally **and** the pull fails
        (e.g. network error, image does not exist on the registry).
    """
    image = _get_image(cmd)

    # Check whether the image already exists locally.
    result = subprocess.run(
        ["docker", "image", "inspect", image],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode == 0:
        print(f"Docker image found locally: {image}")
        return image

    # Image not present – attempt to pull it.
    print(f"Docker image not found locally: {image}")
    print(f"Pulling {image} …")

    pull_result = subprocess.run(
        ["docker", "pull", image],
        capture_output=True,
        text=True,
        check=False,
    )

    if pull_result.returncode != 0:
        stderr = pull_result.stderr.strip()
        raise DependencyError(
            dependency=image,
            message=(
                f"Failed to pull Docker image '{image}'. "
                f"Make sure the image name is correct and you have "
                f"network access.\n{stderr}"
            ),
        )

    print(f"Successfully pulled: {image}")
    return image


def validate_existing_image(cmd: list[str]) -> None:
    """Validate that a command produces an existing image file.

    Parameters
    ----------
    cmd : List[str]
        Command to execute that should produce an image file.

    Raises
    ------
    InputValidationError
        If the command does not produce an existing image file.
    """
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output_path = Path(result.stdout.strip())
        if not output_path.exists():
            raise InputValidationError(
                f"Expected output image not found: {output_path}"
            )
    except subprocess.CalledProcessError as e:
        raise InputValidationError(
            f"Command failed: {' '.join(cmd)}\n{e.stderr}"
        ) from e


def run_docker(
    cmd: list[str],
    tool_name: str,
    participant: str,
    log_dir: Path | None = None,
    capture_output: bool = True,
) -> dict[str, Any]:
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

    # Validate / pull the Docker image before running.
    ensure_docker_image(cmd)

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
        ) from e
    except Exception as e:
        if not isinstance(e, ProcedureExecutionError):
            raise ProcedureExecutionError(
                procedure_name=tool_name, message=str(e), original_error=e
            ) from e
        raise
