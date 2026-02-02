VoxelOps
========

.. image:: https://readthedocs.org/projects/voxelops/badge/?version=latest
   :target: https://voxelops.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://github.com/yalab-devops/VoxelOps/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/yalab-devops/VoxelOps/actions/workflows/ci.yml
   :alt: CI Status


Clean, simple neuroimaging pipeline automation for brain banks.
--------------------------------------------------------------

VoxelOps is a Python package designed to streamline and automate neuroimaging data processing within brain bank environments. It provides straightforward interfaces for popular neuroimaging tools, encapsulating complex Docker commands into simple Python function calls. This ensures consistency, reproducibility, and ease of use for researchers and data managers alike.

Features
--------

-   **Containerized Workflows**: Run neuroimaging procedures (e.g., Heudiconv, QSIPrep, QSIRecon, QSIParc) in isolated Docker containers, ensuring reproducible environments.
-   **Simplified Interface**: Abstract away complex command-line arguments and Docker specifics with intuitive Python functions and dataclass-based inputs/outputs.
-   **Automated Data Handling**: Standardized input validation, output generation, and robust error handling for common neuroimaging tasks.
-   **BIDS Compliance Tools**: Post-processing utilities to ensure BIDS (Brain Imaging Data Structure) compliance, such as adding ``IntendedFor`` fields to fieldmap JSONs and cleaning up auxiliary files.
-   **Extensible Design**: Easily integrate new neuroimaging pipelines or customize existing ones to fit specific research needs.

Installation
------------

You can install VoxelOps using ``pip``:

.. code-block:: bash

    pip install voxelops

For development, clone the repository and install in editable mode with development dependencies:

.. code-block:: bash

    git clone https://github.com/yalab-devops/VoxelOps.git
    cd VoxelOps
    pip install -e ".[dev,docs]"

Usage
-----

VoxelOps provides runner functions for each neuroimaging tool. Here's a quick example for ``QSIPrep``:

.. code-block:: python

    from pathlib import Path
    from voxelops import run_qsiprep, QSIPrepInputs, QSIPrepDefaults

    # Define your inputs
    inputs = QSIPrepInputs(
        bids_dir=Path("/path/to/your/bids_dataset"),
        participant="sub-01",
    )

    # (Optional) Customize configuration
    config = QSIPrepDefaults(
        nprocs=8,
        mem_mb=30000,
        anatomical_template=["MNI152NLin2009cAsym", "T1w"],
    )

    # Run QSIPrep
    result = run_qsiprep(inputs, config=config)

    if result['success']:
        print(f"QSIPrep completed for {result['participant']} in {result['duration_human']}")
        print(f"Outputs are in: {result['expected_outputs'].qsiprep_dir}")
    else:
        print(f"QSIPrep failed: {result.get('error', 'Unknown error')}")


For more detailed usage examples, refer to the ``examples/`` directory and the full documentation.

Documentation
-------------

The full documentation for VoxelOps is available on ReadTheDocs (once deployed):

- `VoxelOps Documentation <https://voxelops.readthedocs.io>`_

Contributing
------------

We welcome contributions! Please see our `CONTRIBUTING.md` (if available) for guidelines on how to get started.

License
-------

This project is licensed under the MIT License - see the `LICENSE` file for details.
