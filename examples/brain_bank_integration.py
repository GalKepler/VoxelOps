#!/usr/bin/env python3
"""Brain bank database integration example.

This shows how to integrate VoxelOps with a brain bank database system.
The execution records are simple dicts, making database integration trivial.
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import json

from voxelops import (
    run_qsiprep,
    run_qsirecon,
    QSIPrepInputs,
    QSIReconInputs,
)

# ============================================================================
# Simulated Brain Bank Database
# ============================================================================


class BrainBankDB:
    """Simulated brain bank database.

    In reality, this would be SQLAlchemy, MongoDB, PostgreSQL, etc.
    The key point: execution records are just dicts, easy to store anywhere.
    """

    def __init__(self):
        self.processing_records = []
        self.participants = {}

    def get_unprocessed_participants(self, pipeline: str) -> List[str]:
        """Get participants that haven't been processed by a pipeline.

        Args:
            pipeline: Pipeline name (e.g., "qsiprep", "qsirecon")

        Returns:
            List of participant labels
        """
        # In reality: query database
        # For demo: return hardcoded list
        if pipeline == "qsiprep":
            return ["01", "02", "03"]
        elif pipeline == "qsirecon":
            return ["01", "02"]
        return []

    def save_processing_record(
        self,
        participant: str,
        record: Dict[str, Any],
    ) -> None:
        """Save processing record to database.

        Args:
            participant: Participant label
            record: Execution record from VoxelOps

        The record dict contains everything:
            - tool: Tool name
            - participant: Participant label
            - command: Full Docker command (for reproducibility!)
            - exit_code: Exit code
            - start_time, end_time: Timestamps
            - duration_seconds: Duration
            - success: Boolean
            - log_file: Path to detailed log
            - expected_outputs: Output paths
        """
        # Example: Store in PostgreSQL JSON column
        # session.execute(
        #     insert(processing_records).values(
        #         participant_id=participant,
        #         tool=record['tool'],
        #         command=json.dumps(record['command']),
        #         duration=record['duration_seconds'],
        #         success=record['success'],
        #         timestamp=record['start_time'],
        #         full_record=record,  # JSON column
        #     )
        # )

        # Example: Store in MongoDB
        # db.processing_records.insert_one({
        #     'participant': participant,
        #     'tool': record['tool'],
        #     'timestamp': record['start_time'],
        #     'record': record,
        # })

        # For demo: just append to list
        self.processing_records.append(
            {
                "participant": participant,
                "timestamp": datetime.now(),
                "record": record,
            }
        )

        print(f"  → Saved {record['tool']} record for {participant} to database")

    def get_pipeline_status(self, participant: str) -> Dict[str, Any]:
        """Get processing status for a participant.

        Args:
            participant: Participant label

        Returns:
            Dict with pipeline status
        """
        records = [
            r for r in self.processing_records if r["participant"] == participant
        ]

        status = {
            "participant": participant,
            "completed_steps": [],
            "failed_steps": [],
            "total_duration": 0,
        }

        for rec in records:
            tool = rec["record"]["tool"]
            if rec["record"]["success"]:
                status["completed_steps"].append(tool)
                status["total_duration"] += rec["record"]["duration_seconds"]
            else:
                status["failed_steps"].append(tool)

        return status

    def reproduce_processing(self, participant: str, tool: str) -> str:
        """Get exact command to reproduce a processing step.

        Args:
            participant: Participant label
            tool: Tool name

        Returns:
            Shell command string (ready to execute)

        This is the magic of storing the command in the execution record:
        Perfect reproducibility!
        """
        for rec in self.processing_records:
            if rec["participant"] == participant and rec["record"]["tool"] == tool:
                cmd = rec["record"]["command"]
                return " ".join(cmd)

        return None


# ============================================================================
# Brain Bank Processing Functions
# ============================================================================


def process_new_participants(db: BrainBankDB, bids_root: Path):
    """Process all participants that need QSIPrep.

    This is the typical brain bank workflow:
    1. Query database for unprocessed participants
    2. Process each one
    3. Save execution record to database

    Args:
        db: Brain bank database
        bids_root: Root BIDS directory
    """
    # Get participants needing processing
    participants = db.get_unprocessed_participants("qsiprep")

    print(f"\nFound {len(participants)} participants needing QSIPrep")

    # Define brain bank standard parameters
    # These are used for ALL participants - perfect consistency!
    BRAIN_BANK_QSIPREP = {
        "nprocs": 16,
        "mem_gb": 32,
        "output_resolution": 1.6,
        "output_spaces": ["MNI152NLin2009cAsym"],
        "longitudinal": True,
    }

    for participant in participants:
        print(f"\nProcessing participant: {participant}")

        try:
            # Define inputs
            inputs = QSIPrepInputs(
                bids_dir=bids_root,
                participant=participant,
            )

            # Run with standard parameters
            result = run_qsiprep(inputs, **BRAIN_BANK_QSIPREP)

            # Save to database - trivial!
            db.save_processing_record(participant, result)

            print(f"✓ {participant}: Completed in {result['duration_human']}")

        except Exception as e:
            # Save failure to database too
            error_record = {
                "tool": "qsiprep",
                "participant": participant,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
            db.save_processing_record(participant, error_record)

            print(f"✗ {participant}: Failed - {e}")
            continue


def generate_audit_report(db: BrainBankDB) -> str:
    """Generate audit report of all processing.

    Brain banks need clear audit trails. With VoxelOps,
    every execution is logged with the exact command.

    Args:
        db: Brain bank database

    Returns:
        Markdown-formatted report
    """
    report = []
    report.append("# Brain Bank Processing Audit Report")
    report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("\n## Summary")

    # Get all participants
    participants = set(r["participant"] for r in db.processing_records)
    report.append(f"\nTotal participants processed: {len(participants)}")

    # Per-participant status
    report.append("\n## Participant Status\n")

    for participant in sorted(participants):
        status = db.get_pipeline_status(participant)

        report.append(f"\n### Participant: {participant}")
        report.append(f"\n- Completed steps: {', '.join(status['completed_steps'])}")

        if status["failed_steps"]:
            report.append(f"- Failed steps: {', '.join(status['failed_steps'])}")

        duration_hours = status["total_duration"] / 3600
        report.append(f"- Total processing time: {duration_hours:.2f} hours")

        # Reproducibility section
        report.append("\n#### Reproduction Commands\n")
        report.append("To reproduce this participant's processing:\n")
        report.append("```bash")

        for rec in db.processing_records:
            if rec["participant"] == participant and rec["record"]["success"]:
                tool = rec["record"]["tool"]
                cmd = " ".join(rec["record"]["command"])
                report.append(f"# {tool}")
                report.append(cmd)
                report.append("")

        report.append("```")

    return "\n".join(report)


def check_pipeline_completion(db: BrainBankDB) -> Dict[str, List[str]]:
    """Check which participants have completed each pipeline step.

    Args:
        db: Brain bank database

    Returns:
        Dict mapping pipeline step -> list of completed participants
    """
    completion = {
        "qsiprep": [],
        "qsirecon": [],
        "qsiparc": [],
    }

    for rec in db.processing_records:
        if rec["record"]["success"]:
            participant = rec["participant"]
            tool = rec["record"]["tool"]
            if tool in completion and participant not in completion[tool]:
                completion[tool].append(participant)

    return completion


# ============================================================================
# Example Usage
# ============================================================================


def main():
    """Example brain bank integration workflow."""

    # Initialize database
    db = BrainBankDB()

    # Paths
    bids_root = Path("/data/bids")

    print("=" * 80)
    print("BRAIN BANK INTEGRATION EXAMPLE")
    print("=" * 80)

    # Example 1: Process new participants
    print("\n1. Processing new participants...")
    # process_new_participants(db, bids_root)  # Uncomment to actually run

    # Simulate some records for demo
    db.processing_records = [
        {
            "participant": "01",
            "timestamp": datetime.now(),
            "record": {
                "tool": "qsiprep",
                "participant": "01",
                "command": ["docker", "run", "..."],
                "duration_seconds": 3600,
                "duration_human": "1:00:00",
                "success": True,
                "start_time": "2026-01-26T10:00:00",
                "end_time": "2026-01-26T11:00:00",
            },
        },
        {
            "participant": "01",
            "timestamp": datetime.now(),
            "record": {
                "tool": "qsirecon",
                "participant": "01",
                "command": ["docker", "run", "..."],
                "duration_seconds": 1800,
                "duration_human": "0:30:00",
                "success": True,
                "start_time": "2026-01-26T11:00:00",
                "end_time": "2026-01-26T11:30:00",
            },
        },
    ]

    # Example 2: Check pipeline completion
    print("\n2. Checking pipeline completion...")
    completion = check_pipeline_completion(db)
    for tool, participants in completion.items():
        print(f"  {tool}: {len(participants)} participants completed")

    # Example 3: Generate audit report
    print("\n3. Generating audit report...")
    report = generate_audit_report(db)
    print(report)

    # Example 4: Reproduce processing
    print("\n4. Reproducing processing for participant 01...")
    cmd = db.reproduce_processing("01", "qsiprep")
    if cmd:
        print(f"  Command: {cmd}")
        print("  → Just run this command to reproduce exactly!")

    print("\n" + "=" * 80)
    print("KEY BENEFITS FOR BRAIN BANKS")
    print("=" * 80)
    print(
        """
1. REPRODUCIBILITY
   - Exact command stored in database
   - Just run it again for perfect reproduction

2. AUDIT TRAIL
   - Every execution logged automatically
   - Timestamps, duration, success/failure

3. DATABASE INTEGRATION
   - Results are dicts - trivial to store
   - Works with PostgreSQL, MongoDB, SQLAlchemy, etc.

4. CONSISTENCY
   - Define standard parameters once
   - Use everywhere - same processing for all participants

5. SIMPLICITY
   - No complex objects to serialize
   - No special database schema required
   - Just store the dict!
    """
    )


if __name__ == "__main__":
    main()
