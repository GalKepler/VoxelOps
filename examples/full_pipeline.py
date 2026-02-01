#!/usr/bin/env python3
"""Complete brain bank diffusion pipeline.

This demonstrates the full workflow:
DICOM → BIDS → QSIPrep → QSIRecon → QSIParc

Each step:
1. Takes clear inputs (paths + participant)
2. Returns execution record (dict)
3. Provides expected outputs for next step
"""

from pathlib import Path
from voxelops import (
    # Runners
    run_heudiconv,
    run_qsiprep,
    run_qsirecon,
    run_qsiparc,
    # Input schemas
    HeudiconvInputs,
    QSIPrepInputs,
    QSIReconInputs,
    QSIParcInputs,
    # Defaults (for brain bank standards)
    HeudiconvDefaults,
    QSIPrepDefaults,
)

# Your data paths
DATA_ROOT = Path("/data")
DICOMS = DATA_ROOT / "dicoms"
DERIVATIVES = DATA_ROOT / "derivatives"
HEURISTIC = Path("/code/heuristic.py")  # Your heuristic file

# Participant to process
PARTICIPANT = "01"


def run_full_pipeline(participant: str, dry_run: bool = False):
    """Run complete diffusion pipeline for a participant.

    Args:
        participant: Participant label (without 'sub-' prefix)
        dry_run: If True, only print what would run (don't execute)

    Returns:
        Dict with results from each step
    """
    pipeline_results = {}

    print("\n" + "=" * 80)
    print(f"BRAIN BANK DIFFUSION PIPELINE - Participant: {participant}")
    print("=" * 80)

    # =========================================================================
    # STEP 1: DICOM → BIDS (HeudiConv)
    # =========================================================================
    print("\nSTEP 1: Converting DICOM to BIDS...")

    heudiconv_inputs = HeudiconvInputs(
        dicom_dir=DICOMS / participant,
        participant=participant,
        output_dir=DERIVATIVES / "bids",
    )

    heudiconv_config = HeudiconvDefaults(
        heuristic=HEURISTIC,
    )

    if dry_run:
        print(f"  Would run: heudiconv")
        print(f"    Input: {heudiconv_inputs.dicom_dir}")
        print(f"    Output: {heudiconv_inputs.output_dir or 'default'}")
    else:
        heudiconv_result = run_heudiconv(heudiconv_inputs, heudiconv_config)
        pipeline_results["heudiconv"] = heudiconv_result

        print(f"✓ HeudiConv completed in {heudiconv_result['duration_human']}")
        print(f"  BIDS dir: {heudiconv_result['expected_outputs'].bids_dir}")

        # Save to database
        # db.save_processing_record(participant, heudiconv_result)

    # =========================================================================
    # STEP 2: Diffusion Preprocessing (QSIPrep)
    # =========================================================================
    print("\nSTEP 2: QSIPrep diffusion preprocessing...")

    if not dry_run:
        bids_dir = heudiconv_result["expected_outputs"].bids_dir
    else:
        bids_dir = DERIVATIVES / "bids"

    qsiprep_inputs = QSIPrepInputs(
        bids_dir=bids_dir,
        participant=participant,
    )

    # Use brain bank standard configuration
    qsiprep_config = QSIPrepDefaults(
        nprocs=16,
        mem_gb=32,
        output_resolution=1.6,
        output_spaces=["MNI152NLin2009cAsym"],
        longitudinal=True,
    )

    if dry_run:
        print(f"  Would run: qsiprep")
        print(f"    Input: {qsiprep_inputs.bids_dir}")
        print(
            f"    Config: {qsiprep_config.nprocs} cores, {qsiprep_config.mem_gb}GB RAM"
        )
    else:
        qsiprep_result = run_qsiprep(qsiprep_inputs, qsiprep_config)
        pipeline_results["qsiprep"] = qsiprep_result

        print(f"✓ QSIPrep completed in {qsiprep_result['duration_human']}")
        print(f"  Output dir: {qsiprep_result['expected_outputs'].qsiprep_dir}")

        # db.save_processing_record(participant, qsiprep_result)

    # =========================================================================
    # STEP 3: Diffusion Reconstruction (QSIRecon)
    # =========================================================================
    print("\nSTEP 3: QSIRecon diffusion reconstruction...")

    if not dry_run:
        qsiprep_dir = qsiprep_result["expected_outputs"].qsiprep_dir
    else:
        qsiprep_dir = DERIVATIVES / "qsiprep"

    qsirecon_inputs = QSIReconInputs(
        qsiprep_dir=qsiprep_dir,
        participant=participant,
    )

    if dry_run:
        print(f"  Would run: qsirecon")
        print(f"    Input: {qsirecon_inputs.qsiprep_dir}")
    else:
        # Override default atlases
        qsirecon_result = run_qsirecon(
            qsirecon_inputs,
            atlases=["schaefer100", "schaefer200", "schaefer400"],
        )
        pipeline_results["qsirecon"] = qsirecon_result

        print(f"✓ QSIRecon completed in {qsirecon_result['duration_human']}")
        print(f"  Output dir: {qsirecon_result['expected_outputs'].qsirecon_dir}")

        # db.save_processing_record(participant, qsirecon_result)

    # =========================================================================
    # STEP 4: Parcellation (QSIParc)
    # =========================================================================
    print("\nSTEP 4: QSIParc parcellation...")

    if not dry_run:
        qsirecon_dir = qsirecon_result["expected_outputs"].qsirecon_dir
    else:
        qsirecon_dir = DERIVATIVES / "qsirecon"

    qsiparc_inputs = QSIParcInputs(
        qsirecon_dir=qsirecon_dir,
        participant=participant,
    )

    if dry_run:
        print(f"  Would run: qsiparc")
        print(f"    Input: {qsiparc_inputs.qsirecon_dir}")
    else:
        qsiparc_result = run_qsiparc(qsiparc_inputs)
        pipeline_results["qsiparc"] = qsiparc_result

        print(f"✓ QSIParc completed in {qsiparc_result['duration_human']}")
        print(f"  Connectivity: {qsiparc_result['expected_outputs'].connectivity_dir}")

        # db.save_processing_record(participant, qsiparc_result)

    # =========================================================================
    # PIPELINE COMPLETE
    # =========================================================================
    print("\n" + "=" * 80)
    print("✓ PIPELINE COMPLETE")
    print("=" * 80)

    if not dry_run:
        total_duration = sum(r["duration_seconds"] for r in pipeline_results.values())
        print(f"Total duration: {total_duration / 3600:.2f} hours")

        # Save complete pipeline record to database
        # db.save_pipeline_record({
        #     'participant': participant,
        #     'steps': pipeline_results,
        #     'total_duration': total_duration,
        # })

    return pipeline_results


def batch_process_participants(participants: list):
    """Process multiple participants through the pipeline.

    Args:
        participants: List of participant labels

    Example:
        >>> participants = ["01", "02", "03"]
        >>> results = batch_process_participants(participants)
    """
    all_results = {}

    for participant in participants:
        try:
            results = run_full_pipeline(participant)
            all_results[participant] = results
            print(f"\n✓ Participant {participant}: SUCCESS")

        except Exception as e:
            print(f"\n✗ Participant {participant}: FAILED - {e}")
            all_results[participant] = {"error": str(e)}
            # Continue with next participant

    # Summary
    print("\n" + "=" * 80)
    print("BATCH PROCESSING SUMMARY")
    print("=" * 80)

    succeeded = [p for p, r in all_results.items() if "error" not in r]
    failed = [p for p, r in all_results.items() if "error" in r]

    print(f"Total: {len(participants)}")
    print(f"✓ Succeeded: {len(succeeded)} - {succeeded}")
    print(f"✗ Failed: {len(failed)} - {failed}")

    return all_results


if __name__ == "__main__":
    import sys

    # Dry run by default (change to False to actually run)
    dry_run = True

    if len(sys.argv) > 1:
        # Process specific participant(s)
        participants = sys.argv[1:]
        if len(participants) == 1:
            run_full_pipeline(participants[0], dry_run=dry_run)
        else:
            batch_process_participants(participants)
    else:
        # Example with default participant
        run_full_pipeline(PARTICIPANT, dry_run=dry_run)

        print("\n" + "=" * 80)
        print("This was a dry run. To actually execute:")
        print(f"  1. Set dry_run=False in this script")
        print(f"  2. Run: python {__file__} 01")
        print(f"  3. For batch: python {__file__} 01 02 03 04")
        print("=" * 80)
