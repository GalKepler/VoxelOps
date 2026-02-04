Contributing to VoxelOps
=========================

First off, thank you for considering contributing to VoxelOps! We welcome
contributions of all kinds, from bug fixes to new features. This guide focuses
on how to add a new "runner" to the project.

What is a Runner?
-----------------

In VoxelOps, a "runner" is a Python function that wraps a command-line tool,
typically a Docker-based neuroimaging tool. The goal is to provide a simple,
consistent Python interface for these tools.

A runner is composed of three main parts:

1.  **The Runner Function**: This is the main function that users will call.
    It takes an ``inputs`` object and an optional ``config`` object, builds
    and executes a command, and returns a dictionary of results.
    (e.g., ``src/voxelops/runners/qsiprep.py``)

2.  **The Schemas**: These are dataclasses that define the inputs, default
    parameters, and expected outputs for the runner. They provide type
    hinting and validation.
    (e.g., ``src/voxelops/schemas/qsiprep.py``)

3.  **Tests**: Each runner should have corresponding tests to ensure it works
    correctly. (e.g., ``tests/test_runners_qsiprep.py``)

Step-by-Step Guide to Adding a New Runner
-----------------------------------------

Let's say we want to add a new runner for a tool called ``mytool``.

### 1. Create the Schema File

First, create a new file in ``src/voxelops/schemas/`` named ``mytool.py``. In
this file, you'll define three dataclasses:

-   ``MyToolInputs``: Required inputs for your tool, like ``bids_dir`` or
    ``participant``.
-   ``MyToolDefaults``: Default parameters for the tool, like the Docker image
    name or the number of processors.
-   ``MyToolOutputs``: The expected outputs of the tool, like file paths.

Here's an example for ``src/voxelops/schemas/mytool.py``:

.. code-block:: python

   from dataclasses import dataclass
   from pathlib import Path

   @dataclass
   class MyToolInputs:
       bids_dir: Path
       participant: str
       output_dir: Path | None = None
       work_dir: Path | None = None

   @dataclass
   class MyToolDefaults:
       docker_image: str = "myorg/mytool:latest"
       nprocs: int = 2

   @dataclass
   class MyToolOutputs:
       output_file: Path

       @classmethod
       def from_inputs(cls, inputs: MyToolInputs, output_dir: Path) -> "MyToolOutputs":
           return cls(
               output_file=output_dir / f"sub-{inputs.participant}" / "output.txt"
           )

### 2. Create the Runner Function File

Next, create the main runner file in ``src/voxelops/runners/``, also named
``mytool.py``. This file will contain the ``run_mytool`` function.

This function should:

-   Accept ``inputs`` (``MyToolInputs``) and optional ``config``
    (``MyToolDefaults``).
-   Use helpers from ``voxelops.runners._base`` to validate inputs.
-   Construct the full ``docker run`` command as a list of strings.
-   Call ``run_docker`` from the base module to execute the command.
-   Return the resulting execution dictionary, augmented with inputs, config,
    and expected outputs.

Here is an example for ``src/voxelops/runners/mytool.py``:

.. code-block:: python

   import os
   from pathlib import Path
   from typing import Dict, Optional, Any

   from voxelops.runners._base import (
       run_docker,
       validate_input_dir,
       validate_participant,
   )
   from voxelops.schemas.mytool import (
       MyToolInputs,
       MyToolOutputs,
       MyToolDefaults,
   )

   def run_mytool(
       inputs: MyToolInputs, config: Optional[MyToolDefaults] = None, **overrides
   ) -> Dict[str, Any]:

       config = config or MyToolDefaults()
       for key, value in overrides.items():
           if hasattr(config, key):
               setattr(config, key, value)

       validate_input_dir(inputs.bids_dir, "BIDS")
       validate_participant(inputs.bids_dir, inputs.participant)

       output_dir = inputs.output_dir or (inputs.bids_dir.parent / "derivatives")
       work_dir = inputs.work_dir or (output_dir.parent / "work" / "mytool")
       output_dir.mkdir(parents=True, exist_ok=True)
       work_dir.mkdir(parents=True, exist_ok=True)

       expected_outputs = MyToolOutputs.from_inputs(inputs, output_dir)

       uid = os.getuid()
       gid = os.getgid()

       cmd = [
           "docker", "run", "-ti", "--rm",
           "--user", f"{uid}:{gid}",
           "-v", f"{inputs.bids_dir}:/data:ro",
           "-v", f"{output_dir}:/out",
           "-v", f"{work_dir}:/work",
           config.docker_image,
           "/data", "/out", "participant",
           "--participant-label", inputs.participant,
           "--nprocs", str(config.nprocs),
       ]

       log_dir = output_dir.parent / "logs"
       result = run_docker(
           cmd=cmd,
           tool_name="mytool",
           participant=inputs.participant,
           log_dir=log_dir,
       )

       result["inputs"] = inputs
       result["config"] = config
       result["expected_outputs"] = expected_outputs

       return result


### 3. Add the Runner to the ``__init__.py``

Make your new runner easily importable by adding it to
``src/voxelops/runners/__init__.py``:

.. code-block:: python

   # src/voxelops/runners/__init__.py
   ...
   from .mytool import run_mytool
   ...

And also to the main ``__init__.py`` in ``src/voxelops/__init__.py``:

.. code-block:: python

    # src/voxelops/__init__.py
    ...
    from .runners import (
        ...
        run_mytool,
    )
    ...
    __all__ = [
        ...
        "run_mytool",
    ]


### 4. Write Tests

Finally, add tests for your new runner. Create a new file
``tests/test_runners_mytool.py``. You should at least test:

-   That the runner function runs without errors (you can mock the
    ``subprocess.run`` call).
-   That the Docker command is built correctly.
-   That input validation works as expected.

Refer to existing tests like ``tests/test_runners_qsiprep.py`` for examples.

### 5. Add Validation

VoxelOps includes a validation framework to ensure data quality. You should
create a validator for your new procedure.

Create ``src/voxelops/validation/validators/mytool.py``:

.. code-block:: python

   """MyTool validator with pre and post validation rules."""

   from voxelops.validation.rules.common import (
       DirectoryExistsRule,
       GlobFilesExistRule,
       OutputDirectoryExistsRule,
       ParticipantExistsRule,
   )
   from voxelops.validation.validators.base import Validator


   class MyToolValidator(Validator):
       """Validator for MyTool procedure."""

       procedure_name = "mytool"

       pre_rules = [
           # Validate inputs before execution
           DirectoryExistsRule("bids_dir", "BIDS directory"),
           ParticipantExistsRule(),
           GlobFilesExistRule(
               base_dir_attr="bids_dir",
               pattern="**/anat/*_T1w.nii.gz",
               min_count=1,
               file_type="T1w images",
               participant_level=True,  # Search in sub-{participant} subdirectory
           ),
       ]

       post_rules = [
           # Validate outputs after execution
           OutputDirectoryExistsRule("output_dir", "Output directory"),
           GlobFilesExistRule(
               base_dir_attr="output_dir",
               pattern="**/*.nii.gz",
               min_count=1,
               file_type="Output images",
               phase="post",
               participant_level=False,  # output_dir is already participant-specific
           ),
       ]

Then:

1. Export it in ``src/voxelops/validation/validators/__init__.py``:

   .. code-block:: python

      from .mytool import MyToolValidator

      __all__ = [
          ...,
          "MyToolValidator",
      ]

2. Register it in ``src/voxelops/procedures/orchestrator.py``:

   .. code-block:: python

      from voxelops.validation.validators import MyToolValidator

      VALIDATORS = {
          ...,
          "mytool": MyToolValidator(),
      }

3. Add tests in ``tests/validation/test_validators_mytool.py``

See the **Validation Framework** documentation for detailed guidance.

### 6. Update Documentation

If you've added a new runner, add it to the list of available procedures in
``docs/index.rst`` and create a new ``.rst`` file for your runner in the
``docs/source/`` folder.

Final Words
-----------

Once you've followed these steps, open a pull request on GitHub. We'll review
your contribution and work with you to get it merged.

For more information on validation, see :doc:`validation`.

Thank you for helping us make VoxelOps better!
