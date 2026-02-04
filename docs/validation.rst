Validation Framework
====================

VoxelOps includes a comprehensive validation framework that ensures data quality and pipeline integrity through automated pre- and post-execution checks. This framework validates inputs before running procedures and verifies outputs after completion.

.. contents:: Table of Contents
   :local:
   :depth: 2

Overview
--------

The validation framework provides:

- **Pre-validation**: Check inputs exist and meet requirements before execution
- **Post-validation**: Verify expected outputs were created successfully
- **Audit logging**: Track all validation results with timestamps
- **Orchestration**: Integrated execution with automatic validation
- **Extensibility**: Easy to add validation for new procedures

Architecture
------------

The validation framework consists of several key components:

.. code-block:: text

   validation/
   ├── base.py              # Core ValidationRule and ValidationResult classes
   ├── context.py           # ValidationContext for passing data to rules
   ├── validators/          # Procedure-specific validators
   │   ├── base.py          # Base Validator class
   │   ├── heudiconv.py     # HeudiConv validator
   │   ├── qsiprep.py       # QSIPrep validator
   │   ├── qsirecon.py      # QSIRecon validator
   │   └── qsiparc.py       # QSIParc validator
   └── rules/               # Reusable validation rules
       └── common.py        # Common rules (DirectoryExistsRule, etc.)

Core Concepts
-------------

ValidationRule
~~~~~~~~~~~~~~

A ``ValidationRule`` is the base class for all validation checks. Each rule:

- Has a ``name`` and ``description``
- Implements a ``check()`` method that returns a ``ValidationResult``
- Can be configured with ``severity`` ("error" or "warning")
- Belongs to a ``phase`` ("pre" or "post")

Example:

.. code-block:: python

   from voxelops.validation.base import ValidationRule, ValidationResult
   from voxelops.validation.context import ValidationContext

   class DirectoryExistsRule(ValidationRule):
       """Check that a directory exists."""

       name = "directory_exists"
       description = "Verify directory exists"
       severity = "error"
       phase = "pre"

       def __init__(self, path_attr: str, dir_type: str = "Input"):
           self.path_attr = path_attr
           self.dir_type = dir_type

       def check(self, context: ValidationContext) -> ValidationResult:
           path = getattr(context.inputs, self.path_attr)
           if not path.exists():
               return self._fail(
                   f"{self.dir_type} directory not found: {path}",
                   {"path": str(path), "exists": False}
               )
           return self._pass(
               f"{self.dir_type} directory exists: {path}",
               {"path": str(path), "exists": True}
           )

ValidationContext
~~~~~~~~~~~~~~~~~

The ``ValidationContext`` carries all data needed for validation:

.. code-block:: python

   from voxelops.validation.context import ValidationContext

   context = ValidationContext(
       procedure_name="qsiprep",
       participant="01",
       session="baseline",           # Optional
       inputs=qsiprep_inputs,        # Procedure inputs
       config=qsiprep_config,        # Procedure config
       expected_outputs=outputs,     # Post-validation only
       execution_result=result,      # Post-validation only
   )

ValidationResult
~~~~~~~~~~~~~~~~

Each validation check returns a ``ValidationResult`` with:

- ``passed``: Boolean success/failure
- ``message``: Human-readable description
- ``details``: Dictionary with additional information
- ``severity``: "error" or "warning"
- ``timestamp``: When the check ran

Validator
~~~~~~~~~

A ``Validator`` groups multiple rules for a specific procedure:

.. code-block:: python

   from voxelops.validation.validators.base import Validator
   from voxelops.validation.rules.common import DirectoryExistsRule

   class MyToolValidator(Validator):
       """Validator for MyTool procedure."""

       procedure_name = "mytool"

       pre_rules = [
           DirectoryExistsRule("bids_dir", "BIDS directory"),
           ParticipantExistsRule(),
           # More pre-validation rules...
       ]

       post_rules = [
           OutputDirectoryExistsRule("output_dir", "Output directory"),
           # More post-validation rules...
       ]

Using the Validation Framework
-------------------------------

Standalone Validation
~~~~~~~~~~~~~~~~~~~~~

You can run validation directly:

.. code-block:: python

   from pathlib import Path
   from voxelops.schemas.qsiprep import QSIPrepInputs
   from voxelops.validation.validators import QSIPrepValidator
   from voxelops.validation.context import ValidationContext

   # Setup inputs
   inputs = QSIPrepInputs(
       bids_dir=Path("/data/bids"),
       participant="01",
   )

   # Create validator and context
   validator = QSIPrepValidator()
   context = ValidationContext(
       procedure_name="qsiprep",
       participant="01",
       inputs=inputs,
   )

   # Run pre-validation
   pre_report = validator.validate_pre(context)

   if not pre_report.passed:
       print("Pre-validation failed!")
       for error in pre_report.errors:
           print(f"  - {error}")
   else:
       print("Pre-validation passed!")
       # Proceed with execution...

Integrated with Orchestrator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The recommended approach is to use the ``run_procedure()`` orchestrator, which automatically handles validation:

.. code-block:: python

   from pathlib import Path
   from voxelops import run_procedure
   from voxelops.schemas.qsiprep import QSIPrepInputs

   inputs = QSIPrepInputs(
       bids_dir=Path("/data/bids"),
       participant="01",
   )

   # Run with automatic validation
   result = run_procedure(
       procedure="qsiprep",
       inputs=inputs,
       log_dir=Path("/data/logs"),
   )

   # Check result
   if result.success:
       print(f"✓ Success! {result.status}")
   else:
       print(f"✗ Failed: {result.get_failure_reason()}")

       # Access validation reports
       if result.pre_validation and not result.pre_validation.passed:
           print("\nPre-validation errors:")
           for error in result.pre_validation.errors:
               print(f"  - {error}")

       if result.post_validation and not result.post_validation.passed:
           print("\nPost-validation errors:")
           for error in result.post_validation.errors:
               print(f"  - {error}")

Available Common Rules
----------------------

The framework provides several reusable validation rules in ``voxelops.validation.rules.common``:

DirectoryExistsRule
~~~~~~~~~~~~~~~~~~~

Check that a directory exists in inputs.

.. code-block:: python

   DirectoryExistsRule(
       path_attr="bids_dir",        # Attribute name on inputs
       dir_type="BIDS directory",   # Human-readable type
       severity="error",            # "error" or "warning"
   )

FileExistsRule
~~~~~~~~~~~~~~

Check that a file exists in inputs or config.

.. code-block:: python

   FileExistsRule(
       path_attr="heuristic",       # Attribute name
       file_type="Heuristic file",  # Human-readable type
       severity="error",
       on_config=False,             # Look on config instead of inputs?
   )

ParticipantExistsRule
~~~~~~~~~~~~~~~~~~~~~

Check that participant directory exists in input directory.

.. code-block:: python

   ParticipantExistsRule(prefix="sub-")  # Participant directory prefix

GlobFilesExistRule
~~~~~~~~~~~~~~~~~~

Check that files matching a glob pattern exist.

.. code-block:: python

   GlobFilesExistRule(
       base_dir_attr="bids_dir",           # Base directory attribute
       pattern="**/dwi/*.nii.gz",          # Glob pattern
       min_count=1,                        # Minimum number of files required
       file_type="DWI files",              # Human-readable type
       severity="error",
       phase="pre",                        # "pre" or "post"
       participant_level=True,             # Search in participant subdir?
   )

**participant_level behavior:**

- ``True``: Searches in ``base_dir/sub-{participant}/ses-{session}`` (if session exists)
- ``False``: Searches in ``base_dir`` directly (for outputs or non-BIDS structures)

OutputDirectoryExistsRule
~~~~~~~~~~~~~~~~~~~~~~~~~~

Post-validation: Check that output directory was created.

.. code-block:: python

   OutputDirectoryExistsRule(
       output_attr="qsiprep_dir",      # Attribute on expected_outputs
       output_type="QSIPrep output",   # Human-readable type
   )

ExpectedOutputsExistRule
~~~~~~~~~~~~~~~~~~~~~~~~~

Generic post-validation rule for checking various output structures:

.. code-block:: python

   # Single file
   ExpectedOutputsExistRule(
       outputs_attr="html_report",     # Attribute on expected_outputs
       item_type="HTML report",        # Human-readable type
   )

   # Flat dictionary {key: path}
   ExpectedOutputsExistRule(
       outputs_attr="workflow_outputs",
       item_type="workflow outputs",
       flatten_nested=False,
   )

   # Nested dictionary {workflow: {session: path}}
   ExpectedOutputsExistRule(
       outputs_attr="workflow_reports",
       item_type="workflow HTML reports",
       flatten_nested=True,            # Handle nested structure
   )

This rule automatically handles:

- Single ``Path`` objects
- Flat dictionaries ``{key: path}``
- Nested dictionaries ``{key1: {key2: path}}``

Adding Validation to a New Procedure
-------------------------------------

When adding a new procedure to VoxelOps, follow these steps to include validation:

Step 1: Create Validator Class
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create a new file ``src/voxelops/validation/validators/mytool.py``:

.. code-block:: python

   """MyTool validator with pre and post validation rules."""

   from voxelops.validation.rules.common import (
       DirectoryExistsRule,
       ExpectedOutputsExistRule,
       GlobFilesExistRule,
       OutputDirectoryExistsRule,
       ParticipantExistsRule,
   )
   from voxelops.validation.validators.base import Validator


   class MyToolValidator(Validator):
       """Validator for MyTool procedure."""

       procedure_name = "mytool"

       pre_rules = [
           # Check input directory exists
           DirectoryExistsRule("bids_dir", "BIDS directory"),

           # Check participant exists in input directory
           ParticipantExistsRule(),

           # Check required files exist
           GlobFilesExistRule(
               base_dir_attr="bids_dir",
               pattern="**/anat/*_T1w.nii.gz",
               min_count=1,
               file_type="T1w images",
               participant_level=True,
           ),
       ]

       post_rules = [
           # Check output directory was created
           OutputDirectoryExistsRule("output_dir", "Output directory"),

           # Check expected files were created
           GlobFilesExistRule(
               base_dir_attr="output_dir",
               pattern="**/*.nii.gz",
               min_count=1,
               file_type="Output images",
               phase="post",
               participant_level=False,  # output_dir is already participant-specific
           ),
       ]

Step 2: Export Validator
~~~~~~~~~~~~~~~~~~~~~~~~~

Add to ``src/voxelops/validation/validators/__init__.py``:

.. code-block:: python

   from .mytool import MyToolValidator

   __all__ = [
       ...,
       "MyToolValidator",
   ]

Step 3: Register in Orchestrator
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Add to ``src/voxelops/procedures/orchestrator.py``:

.. code-block:: python

   from voxelops.validation.validators import (
       ...,
       MyToolValidator,
   )

   # Registry of validators by procedure name
   VALIDATORS = {
       ...,
       "mytool": MyToolValidator(),
   }

Step 4: Update Expected Outputs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Ensure your outputs schema in ``src/voxelops/schemas/mytool.py`` includes all paths needed for validation:

.. code-block:: python

   @dataclass
   class MyToolOutputs:
       """Expected outputs from MyTool."""

       output_dir: Path           # For OutputDirectoryExistsRule
       participant_dir: Path      # If needed
       html_report: Path          # For ExpectedOutputsExistRule

       @classmethod
       def from_inputs(cls, inputs: MyToolInputs, output_dir: Path):
           """Generate expected output paths from inputs."""
           return cls(
               output_dir=output_dir,
               participant_dir=output_dir / f"sub-{inputs.participant}",
               html_report=output_dir / f"sub-{inputs.participant}.html",
           )

Step 5: Write Tests
~~~~~~~~~~~~~~~~~~~

Create ``tests/validation/test_validators_mytool.py``:

.. code-block:: python

   """Tests for MyTool validator."""

   from pathlib import Path
   import pytest
   from voxelops.validation.context import ValidationContext
   from voxelops.validation.validators import MyToolValidator


   class TestMyToolValidator:
       """Tests for MyToolValidator."""

       def test_validator_attributes(self):
           """Test validator has correct attributes."""
           validator = MyToolValidator()
           assert validator.procedure_name == "mytool"
           assert len(validator.pre_rules) == 3
           assert len(validator.post_rules) == 2

       def test_pre_validation_success(self, tmp_path):
           """Test successful pre-validation."""
           # Setup test environment
           bids_dir = tmp_path / "bids"
           sub_dir = bids_dir / "sub-01"
           anat_dir = sub_dir / "anat"
           anat_dir.mkdir(parents=True)
           (anat_dir / "sub-01_T1w.nii.gz").touch()

           # Create mock inputs
           from dataclasses import dataclass

           @dataclass
           class MockInputs:
               bids_dir: Path

           inputs = MockInputs(bids_dir=bids_dir)

           # Run validation
           validator = MyToolValidator()
           context = ValidationContext(
               procedure_name="mytool",
               participant="01",
               inputs=inputs,
           )

           report = validator.validate_pre(context)

           assert report.passed is True
           assert len(report.results) == 3

Custom Validation Rules
-----------------------

If the common rules don't meet your needs, create custom rules:

.. code-block:: python

   from pathlib import Path
   from voxelops.validation.base import ValidationRule, ValidationResult
   from voxelops.validation.context import ValidationContext


   class BIDSValidatorRule(ValidationRule):
       """Run BIDS validator on input directory."""

       name = "bids_validator"
       description = "Run BIDS validator"
       severity = "warning"  # Non-critical
       phase = "pre"

       def check(self, context: ValidationContext) -> ValidationResult:
           """Run bids-validator command."""
           import subprocess

           bids_dir = context.inputs.bids_dir

           try:
               result = subprocess.run(
                   ["bids-validator", str(bids_dir)],
                   capture_output=True,
                   text=True,
                   timeout=60,
               )

               if result.returncode == 0:
                   return self._pass(
                       "BIDS validation passed",
                       {"bids_dir": str(bids_dir)}
                   )
               else:
                   return self._fail(
                       f"BIDS validation failed:\n{result.stderr}",
                       {
                           "bids_dir": str(bids_dir),
                           "errors": result.stderr,
                       }
                   )

           except FileNotFoundError:
               return self._fail(
                   "bids-validator not found in PATH",
                   {"bids_dir": str(bids_dir)}
               )

           except subprocess.TimeoutExpired:
               return self._fail(
                   "BIDS validation timed out",
                   {"bids_dir": str(bids_dir)}
               )

Then use it in your validator:

.. code-block:: python

   from .custom_rules import BIDSValidatorRule

   class MyToolValidator(Validator):
       procedure_name = "mytool"

       pre_rules = [
           BIDSValidatorRule(),
           # ... other rules
       ]

Best Practices
--------------

1. **Keep Rules Focused**

   Each rule should check one specific thing. This makes debugging easier and rules more reusable.

2. **Use Appropriate Severity**

   - ``"error"``: Must pass for execution to proceed
   - ``"warning"``: Logged but doesn't block execution

3. **Provide Useful Messages**

   Include enough detail in messages and details dict for users to diagnose issues:

   .. code-block:: python

      return self._fail(
          f"Missing required files in {search_dir}",
          {
              "pattern": self.pattern,
              "search_dir": str(search_dir),
              "found_count": len(found_files),
              "required_count": self.min_count,
              "found_files": [str(f.name) for f in found_files],
          }
      )

4. **Test Edge Cases**

   Test your validators with:

   - Missing directories
   - Empty directories
   - Malformed file names
   - Missing sessions (for multi-session support)

5. **Document Expected Outputs**

   Clearly document what your ``ExpectedOutputs`` schema should contain in docstrings.

6. **Use participant_level Correctly**

   - Pre-validation of BIDS inputs: ``participant_level=True``
   - Post-validation of procedure outputs: ``participant_level=False`` (output_dir is already participant-specific)

Validation Reports
------------------

Validation results are stored in ``ValidationReport`` objects:

.. code-block:: python

   @dataclass
   class ValidationReport:
       phase: str                      # "pre" or "post"
       procedure: str                  # "qsiprep", etc.
       participant: str                # "01"
       session: Optional[str]          # "baseline" or None
       timestamp: datetime             # When validation ran
       results: List[ValidationResult] # All check results

       @property
       def passed(self) -> bool:
           """True if all error-level checks passed."""
           return all(
               r.passed for r in self.results
               if r.severity == "error"
           )

       @property
       def errors(self) -> List[str]:
           """List of error messages."""
           return [
               r.message for r in self.results
               if not r.passed and r.severity == "error"
           ]

       @property
       def warnings(self) -> List[str]:
           """List of warning messages."""
           return [
               r.message for r in self.results
               if not r.passed and r.severity == "warning"
           ]

Access reports from ``ProcedureResult``:

.. code-block:: python

   result = run_procedure("qsiprep", inputs=inputs)

   # Check pre-validation
   if result.pre_validation:
       print(f"Pre-validation: {result.pre_validation.passed}")
       for error in result.pre_validation.errors:
           print(f"  ERROR: {error}")
       for warning in result.pre_validation.warnings:
           print(f"  WARNING: {warning}")

   # Check post-validation
   if result.post_validation:
       print(f"Post-validation: {result.post_validation.passed}")
       for result_item in result.post_validation.results:
           status = "✓" if result_item.passed else "✗"
           print(f"  {status} {result_item.rule_description}")

Integration with Audit Logging
-------------------------------

All validation results are automatically logged to JSON files when using ``run_procedure()``:

.. code-block:: json

   {
     "timestamp": "2024-01-15T10:30:00",
     "event_type": "validation_pre",
     "data": {
       "phase": "pre",
       "procedure": "qsiprep",
       "participant": "01",
       "passed": true,
       "results": [
         {
           "rule_name": "bids_dir_exists",
           "passed": true,
           "message": "BIDS directory exists: /data/bids",
           "severity": "error"
         }
       ]
     }
   }

Find these logs in the audit log directory (default: ``output_dir/logs``).

Troubleshooting
---------------

Validation Failed but Files Exist
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Post-validation fails even though you can see the files.

**Solutions**:

1. Check the exact paths in ``expected_outputs``
2. Ensure ``participant_level`` is set correctly
3. Check for typos in glob patterns
4. Verify file permissions

Example debugging:

.. code-block:: python

   # Print expected paths
   print("Expected outputs:")
   print(f"  qsiprep_dir: {result.execution['expected_outputs'].qsiprep_dir}")
   print(f"  Exists: {result.execution['expected_outputs'].qsiprep_dir.exists()}")

   # Check post-validation details
   for check in result.post_validation.results:
       if not check.passed:
           print(f"\nFailed check: {check.rule_name}")
           print(f"  Message: {check.message}")
           print(f"  Details: {check.details}")

Session Detection Not Working
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Validator expects sessions but doesn't find them.

**Solutions**:

1. Check session discovery functions (``_discover_sessions`` in schemas)
2. Verify directory structure matches expected pattern
3. Ensure session parameter is passed to ``ValidationContext``

Glob Pattern Not Matching
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: ``GlobFilesExistRule`` finds 0 files.

**Solutions**:

1. Test the pattern manually:

   .. code-block:: python

      from pathlib import Path
      files = list(Path("/data/bids/sub-01").glob("**/dwi/*.nii.gz"))
      print(f"Found {len(files)} files: {files}")

2. Check ``participant_level`` setting
3. Verify the ``base_dir_attr`` points to the correct directory

Summary
-------

The VoxelOps validation framework provides:

- **Automated Quality Checks**: Pre- and post-validation ensure data integrity
- **Reusable Rules**: Common validation patterns available out-of-the-box
- **Easy Extension**: Simple to add validation for new procedures
- **Comprehensive Logging**: All validation results tracked in audit logs
- **User-Friendly Reports**: Clear error messages guide troubleshooting

For more examples, see:

- ``examples/validation/01_validation_framework_intro.ipynb``
- Existing validators in ``src/voxelops/validation/validators/``
- Tests in ``tests/validation/``
