Getting Started
===============

Welcome to VoxelOps! This guide will help you get VoxelOps up and running, and walk you through your first neuroimaging pipeline.

Installation
------------

First, ensure you have Python 3.8+ and Docker installed on your system.

You can install VoxelOps using ``pip``:

.. code-block:: bash

    pip install voxelops

For development or to contribute, clone the repository and install in editable mode with development and documentation dependencies:

.. code-block:: bash

    git clone https://github.com/yalab-devops/VoxelOps.git
    cd VoxelOps
    pip install -e ".[dev,docs]"

Running Your First Pipeline (QSIPrep Example)
---------------------------------------------

Let's run a basic QSIPrep pipeline to preprocess some diffusion MRI data.

Prerequisites:
-   A BIDS-compliant dataset with at least one subject and DWI data.
-   QSIPrep Docker image available locally (VoxelOps will attempt to pull it if not found).

.. code-block:: python

    from pathlib import Path
    from voxelops import run_qsiprep, QSIPrepInputs

    # 1. Define your input data and participant
    #    Replace with the actual paths to your BIDS dataset and FreeSurfer license
    bids_root = Path("/path/to/your/bids_dataset")
    participant_id = "sub-01" # Or whatever your participant label is
    fs_license_file = Path("/path/to/your/freesurfer/license.txt")

    inputs = QSIPrepInputs(
        bids_dir=bids_root,
        participant=participant_id,
        # Optional: Specify an output directory, otherwise it defaults
        # to a 'derivatives' folder next to your BIDS root.
        # output_dir=Path("/path/to/my/derivatives"),
        # Optional: Specify a working directory
        # work_dir=Path("/path/to/my/workdir"),
        # Optional: Specify a BIDS filter file
        # bids_filters=Path("/path/to/my/bids_filters.json"),
    )

    # 2. Run the QSIPrep pipeline
    #    You can pass configuration parameters directly as keyword arguments.
    #    For a full list of configuration options, see the API Reference.
    print(f"Starting QSIPrep for participant {participant_id}...")
    result = run_qsiprep(
        inputs,
        fs_license=fs_license_file, # Path to your FreeSurfer license
        nprocs=8,            # Number of CPU cores to use
        mem_mb=30000,        # Memory limit in MB
        anatomical_template=["MNI152NLin2009cAsym", "T1w"], # Output spaces
    )

    # 4. Check the results
    if result['success']:
        print(f"QSIPrep completed successfully for {result['participant']} in {result['duration_human']}")
        print(f"Outputs are located in: {result['expected_outputs'].qsiprep_dir}")
        print(f"View the HTML report at: {result['expected_outputs'].html_report}")
    else:
        print(f"QSIPrep failed for {result['participant']}.")
        print(f"Error details: {result.get('error', 'No specific error message.')}")

Next Steps
----------

-   **Tutorials**: Explore the `Tutorials` section for more in-depth guides on specific workflows (e.g., DICOM conversion, reconstruction, parcellation).
-   **API Reference**: Dive into the `API Reference` to understand the full capabilities of VoxelOps and its various modules.
-   **Examples**: Check the ``examples/`` directory in the repository for runnable scripts demonstrating different pipelines.
