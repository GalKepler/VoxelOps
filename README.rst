VoxelOps
========

.. image:: https://github.com/GalKepler/VoxelOps/blob/main/docs/images/Gemini_Generated_Image_m9bi47m9bi47m9bi.png?raw=true
   :alt: VoxelOps Logo

Clean, simple neuroimaging pipeline automation for brain banks.
---------------------------------------------------------------

Brain banks need to process neuroimaging data **consistently**, **reproducibly**, and **auditably**. VoxelOps makes that simple by wrapping Docker-based neuroimaging tools into clean Python functions that return plain dicts -- ready for your database, your logs, and your peace of mind.

========
Overview
========

.. list-table::
    :stub-columns: 1

    * - docs
      - |docs|
    * - tests, CI & coverage
      - |github-actions| |codecov| |codacy|
    * - version
      - |pypi| |python|
    * - styling
      - |black| |isort| |flake8| |pre-commit|
    * - license
      - |license|

.. |docs| image:: https://readthedocs.org/projects/voxelops/badge/?version=latest
   :target: https://voxelops.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. |github-actions| image:: https://github.com/GalKepler/VoxelOps/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/GalKepler/VoxelOps/actions/workflows/ci.yml
   :alt: CI

.. |codecov| image:: https://codecov.io/gh/GalKepler/VoxelOps/graph/badge.svg?token=GBOLQOB5VI
   :target: https://codecov.io/gh/GalKepler/VoxelOps
   :alt: codecov

.. |codacy| image:: https://app.codacy.com/project/badge/Grade/84bfb76385244fc3b80bc18e5c8f3bfd
   :target: https://app.codacy.com/gh/GalKepler/VoxelOps/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade
   :alt: Codacy Badge

.. |pypi| image:: https://badge.fury.io/py/voxelops.svg
   :target: https://badge.fury.io/py/voxelops
   :alt: PyPI version

.. |python| image:: https://img.shields.io/badge/python-3.10%2B-blue.svg
   :target: https://www.python.org/downloads/
   :alt: Python 3.10+

.. |license| image:: https://img.shields.io/github/license/yalab-devops/yalab-procedures.svg
        :target: https://opensource.org/license/mit
        :alt: License

.. |black| image:: https://img.shields.io/badge/formatter-black-000000.svg
      :target: https://github.com/psf/black

.. |isort| image:: https://img.shields.io/badge/imports-isort-%231674b1.svg
        :target: https://pycqa.github.io/isort/

.. |flake8| image:: https://img.shields.io/badge/style-flake8-000000.svg
        :target: https://flake8.pycqa.org/en/latest/

.. |pre-commit| image:: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
        :target: https://github.com/pre-commit/pre-commit




Features
--------

- **Simple Functions** -- No classes, no inheritance -- just ``run_*()`` functions that return dicts
- **Clear Schemas** -- Typed dataclass inputs, outputs, and defaults for every procedure
- **Reproducibility** -- The exact Docker command is stored in every execution record
- **Database-Ready** -- Results are plain dicts, trivial to save to PostgreSQL, MongoDB, or JSON
- **Brain Bank Defaults** -- Define your standard parameters once, reuse across all participants
- **Comprehensive Logging** -- Every run logged to JSON with timestamps, duration, and exit codes
- **Validation Framework** -- Pre- and post-execution validation with detailed reports
- **Audit Trail** -- Full audit logging for every procedure run

Installation
------------

.. code-block:: bash

    pip install voxelops

For development:

.. code-block:: bash

    git clone https://github.com/yalab-devops/VoxelOps.git
    cd VoxelOps
    pip install -e ".[dev]"

**Requirements**: Python >= 3.10, Docker installed and accessible.

Quick Start
-----------

**Basic (direct execution):**

.. code-block:: python

    from voxelops import run_qsiprep, QSIPrepInputs

    inputs = QSIPrepInputs(
        bids_dir="/data/bids",
        participant="01",
    )

    result = run_qsiprep(inputs, nprocs=16)

    print(f"Completed in: {result['duration_human']}")
    print(f"Outputs: {result['expected_outputs'].qsiprep_dir}")
    print(f"Command: {' '.join(result['command'])}")

**With validation and audit logging (recommended):**

.. code-block:: python

    from voxelops import run_procedure, QSIPrepInputs

    inputs = QSIPrepInputs(
        bids_dir="/data/bids",
        participant="01",
    )

    result = run_procedure("qsiprep", inputs)

    if result.success:
        print(f"Completed in {result.duration_seconds:.1f}s")
    else:
        print(f"Failed: {result.get_failure_reason()}")

    # Save complete audit trail to your database
    db.save_procedure_result(result.to_dict())

Available Procedures
--------------------

.. list-table::
   :header-rows: 1
   :widths: 15 35 25 25

   * - Procedure
     - Purpose
     - Function
     - Execution
   * - HeudiConv
     - DICOM to BIDS conversion
     - ``run_heudiconv()``
     - Docker
   * - QSIPrep
     - Diffusion MRI preprocessing
     - ``run_qsiprep()``
     - Docker
   * - QSIRecon
     - Diffusion reconstruction & connectivity
     - ``run_qsirecon()``
     - Docker
   * - QSIParc
     - Parcellation via ``parcellate``
     - ``run_qsiparc()``
     - Python (direct)

Brain Bank Standards
--------------------

Define your standard parameters once, use them everywhere:

.. code-block:: python

    from voxelops import run_qsiprep, QSIPrepInputs, QSIPrepDefaults

    BRAIN_BANK_QSIPREP = QSIPrepDefaults(
        nprocs=16,
        mem_mb=32000,
        output_resolution=1.6,
        anatomical_template=["MNI152NLin2009cAsym"],
        docker_image="pennlinc/qsiprep:latest",
    )

    for participant in participants:
        inputs = QSIPrepInputs(bids_dir=bids_root, participant=participant)
        result = run_qsiprep(inputs, config=BRAIN_BANK_QSIPREP)
        db.save_processing_record(result)

Validation & Audit
------------------

``run_procedure()`` wraps any runner with pre-validation, post-validation, and a full audit trail:

.. code-block:: python

    from voxelops import run_procedure, HeudiconvInputs, HeudiconvDefaults

    inputs = HeudiconvInputs(
        dicom_dir="/data/dicoms",
        participant="01",
        session="baseline",
    )
    config = HeudiconvDefaults(heuristic="/code/heuristic.py")

    result = run_procedure("heudiconv", inputs, config)

    # result.pre_validation  -- ValidationReport before execution
    # result.post_validation -- ValidationReport after execution
    # result.audit_log_file  -- path to the JSON audit log

Logging
-------

All runners accept an optional ``log_dir`` parameter. When provided, an execution
JSON log is written alongside any audit logs. The log directory defaults to
``<output_dir>/../logs`` derived from the inputs.

.. code-block:: python

    result = run_qsiprep(inputs, log_dir="/data/logs/qsiprep")

Documentation
-------------

Full documentation is available at `voxelops.readthedocs.io <https://voxelops.readthedocs.io>`_.

License
-------

MIT License -- see the `LICENSE <LICENSE>`_ file for details.
