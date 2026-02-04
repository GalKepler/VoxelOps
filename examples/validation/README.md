# Validation Framework Examples

This directory contains comprehensive examples for using the VoxelOps validation framework.

## 📚 Full Documentation

For detailed documentation on the validation framework, see:
- **[Validation Framework Guide](../../docs/validation.rst)** - Complete guide with API reference
- **[Contributing Guide](../../docs/contributing.rst)** - Adding validation to new procedures

## Getting Started

Start with these notebooks in order:

1. **`01_validation_framework_intro.ipynb`** - Essential concepts
   - Basic usage of `run_procedure()`
   - Understanding `ProcedureResult` objects
   - Reading validation reports
   - Using audit logs
   - Error handling patterns

2. **`02_qsiprep_validation.ipynb`** - QSIPrep specifics
   - What QSIPrepValidator checks
   - Common validation failures and solutions
   - Batch processing with validation
   - Database integration examples
   - Troubleshooting guide

3. **`03_custom_validation_rules.ipynb`** - Advanced customization
   - Creating custom validation rules
   - Building custom validators
   - Conditional rules
   - Post-validation checks
   - Best practices

## Quick Reference

### Basic Usage

```python
from voxelops import run_procedure, QSIPrepInputs

inputs = QSIPrepInputs(
    bids_dir="/data/bids",
    participant="001",
)

result = run_procedure("qsiprep", inputs)

if result.success:
    print(f"✓ Success! Duration: {result.duration_seconds:.1f}s")
else:
    print(f"✗ Failed: {result.get_failure_reason()}")
```

### What Gets Validated

#### HeudiConv (DICOM → BIDS)
**Pre-validation:**
- DICOM directory exists
- Heuristic file exists
- DICOM files present (*.dcm)

**Post-validation:**
- BIDS directory created
- Participant directory created

#### QSIPrep (DWI Preprocessing)
**Pre-validation:**
- BIDS directory exists
- Participant exists
- DWI files exist (*.nii.gz)
- Bval/bvec files exist
- T1w anatomical exists

**Post-validation:**
- QSIPrep output directory created
- Participant output directory created

#### QSIRecon (DWI Reconstruction)
**Pre-validation:**
- QSIPrep directory exists
- Participant exists
- Preprocessed DWI exists
- Confounds file exists

**Post-validation:**
- QSIRecon directory created
- Participant directory created
- Output directory created

#### QSIParc (Parcellation)
**Pre-validation:**
- QSIRecon directory exists
- Participant exists
- Reconstruction files exist

**Post-validation:**
- Output directory created
- Workflow directories created
- Parcellated TSV files exist

## Available Validation Rules

VoxelOps provides reusable validation rules in `voxelops.validation.rules.common`:

| Rule | Phase | Purpose | Example Usage |
|------|-------|---------|---------------|
| `DirectoryExistsRule` | Pre | Check directory exists | BIDS directory, QSIPrep output |
| `FileExistsRule` | Pre | Check file exists | Heuristic file, FreeSurfer license |
| `ParticipantExistsRule` | Pre | Check participant in input | sub-01 exists in BIDS |
| `GlobFilesExistRule` | Both | Check files match pattern | DWI files, output NIfTIs |
| `OutputDirectoryExistsRule` | Post | Check output created | QSIPrep output directory |
| `ExpectedOutputsExistRule` | Post | Check expected outputs | HTML reports, workflow outputs |

### ExpectedOutputsExistRule

The `ExpectedOutputsExistRule` is a powerful generic rule that handles various output structures:

```python
from voxelops.validation.rules.common import ExpectedOutputsExistRule

# Single file (e.g., HTML report)
ExpectedOutputsExistRule(
    outputs_attr="html_report",
    item_type="HTML report",
)

# Flat dictionary {session: path}
ExpectedOutputsExistRule(
    outputs_attr="session_outputs",
    item_type="session outputs",
)

# Nested dictionary {workflow: {session: path}}
ExpectedOutputsExistRule(
    outputs_attr="workflow_reports",
    item_type="workflow HTML reports",
    flatten_nested=True,
)
```

### GlobFilesExistRule participant_level

The `participant_level` parameter controls search behavior:

```python
# Pre-validation: Search in participant subdirectory
GlobFilesExistRule(
    base_dir_attr="bids_dir",
    pattern="**/dwi/*.nii.gz",
    participant_level=True,  # Searches in bids_dir/sub-{participant}/
)

# Post-validation: Search in already participant-specific directory
GlobFilesExistRule(
    base_dir_attr="output_dir",
    pattern="**/*.nii.gz",
    phase="post",
    participant_level=False,  # output_dir is already sub-{participant}/
)
```

## Common Patterns

### Check Validation Before Running

```python
from voxelops import QSIPrepValidator, ValidationContext

validator = QSIPrepValidator()
context = ValidationContext(
    procedure_name="qsiprep",
    participant="001",
    inputs=inputs,
)

# Run just pre-validation
pre_report = validator.validate_pre(context)

if pre_report.passed:
    print("✓ Inputs valid, ready to run")
else:
    print("✗ Validation failed:")
    for error in pre_report.errors:
        print(f"  • {error.message}")
```

### Batch Processing with Validation

```python
participants = ["001", "002", "003"]
results = []

for participant in participants:
    inputs = QSIPrepInputs(bids_dir=bids_dir, participant=participant)
    result = run_procedure("qsiprep", inputs)
    results.append(result)

    if result.success:
        print(f"sub-{participant}: ✓")
    elif result.status == "pre_validation_failed":
        print(f"sub-{participant}: Skipped (invalid inputs)")
    else:
        print(f"sub-{participant}: ✗ {result.get_failure_reason()}")

# Summary
successful = sum(1 for r in results if r.success)
print(f"\nCompleted: {successful}/{len(results)}")
```

### Save Results to Database

```python
# Convert to dict for database storage
result_dict = result.to_dict()

# MongoDB example
db.procedure_runs.insert_one(result_dict)

# PostgreSQL example (using jsonb)
cursor.execute(
    "INSERT INTO runs (data) VALUES (%s)",
    (json.dumps(result_dict),)
)
```

### Query Failed Runs

```python
# Find all pre-validation failures
failed_pre = [
    r for r in results
    if r.status == "pre_validation_failed"
]

# Categorize by failure reason
from collections import Counter
reasons = Counter(r.get_failure_reason() for r in failed_pre)

for reason, count in reasons.most_common():
    print(f"{count}x: {reason}")
```

## Validation Status Reference

| Status | Meaning | What Happened |
|--------|---------|---------------|
| `success` | ✓ Everything passed | Procedure ran and outputs validated |
| `pre_validation_failed` | ✗ Invalid inputs | Didn't run (caught early) |
| `execution_failed` | ✗ Procedure crashed | Ran but failed during execution |
| `post_validation_failed` | ✗ Invalid outputs | Ran but outputs don't meet requirements |

## Validation Report Structure

```python
ValidationReport(
    phase="pre",              # "pre" or "post"
    procedure="qsiprep",      # Procedure name
    participant="001",        # Participant ID
    session="01",             # Session ID (optional)
    timestamp=datetime.now(), # When validation ran
    results=[                 # List of ValidationResult objects
        ValidationResult(
            rule_name="bids_dir_exists",
            rule_description="Verify BIDS directory exists",
            passed=True,
            severity="error",
            message="BIDS directory exists: /data/bids",
            details={"path": "/data/bids", "exists": True},
            timestamp=datetime.now(),
        ),
        # ... more results
    ],
)
```

## Audit Log Format

Audit logs are JSONL files (one JSON object per line):

```jsonl
{"event_type":"procedure_start","procedure":"qsiprep","participant":"001","session":null,"timestamp":"2024-01-15T10:00:00","data":{"inputs":{...},"config":{...}},"run_id":"abc-123"}
{"event_type":"pre_validation","procedure":"qsiprep","participant":"001","session":null,"timestamp":"2024-01-15T10:00:01","data":{"phase":"pre","passed":true,...},"run_id":"abc-123"}
{"event_type":"execution_start","procedure":"qsiprep","participant":"001","session":null,"timestamp":"2024-01-15T10:00:02","data":{},"run_id":"abc-123"}
{"event_type":"execution_success","procedure":"qsiprep","participant":"001","session":null,"timestamp":"2024-01-15T10:15:30","data":{"duration_seconds":928.5,"exit_code":0},"run_id":"abc-123"}
{"event_type":"post_validation","procedure":"qsiprep","participant":"001","session":null,"timestamp":"2024-01-15T10:15:31","data":{"phase":"post","passed":true,...},"run_id":"abc-123"}
{"event_type":"procedure_complete","procedure":"qsiprep","participant":"001","session":null,"timestamp":"2024-01-15T10:15:31","data":{},"run_id":"abc-123"}
```

## Troubleshooting

### "Pre-validation failed: BIDS directory not found"
- Check the `bids_dir` path is correct
- Verify the directory exists: `ls /data/bids`
- Ensure proper permissions

### "No DWI files found"
- Check participant directory: `ls /data/bids/sub-001/dwi/`
- Verify BIDS naming: files should match `*_dwi.nii.gz`
- Check for typos in participant ID

### "Participant not found"
- Verify participant directory exists: `/data/bids/sub-001/`
- Check participant ID is correct (no "sub-" prefix in inputs)
- Verify BIDS structure

### "Post-validation failed: Output directory not created"
- Check procedure execution logs
- Procedure may have crashed silently
- Review audit log for execution errors

## Additional Resources

- [VoxelOps Documentation](../../docs/)
- [BIDS Specification](https://bids-specification.readthedocs.io/)
- [QSIPrep Documentation](https://qsiprep.readthedocs.io/)
- [Validation Framework Source](../../src/voxelops/validation/)

## Contributing

Found a useful pattern? Create an issue or PR with your example notebook!
