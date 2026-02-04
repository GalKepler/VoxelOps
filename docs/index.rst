VoxelOps Documentation
======================

.. image:: images/Gemini_Generated_Image_m9bi47m9bi47m9bi.png
   :alt: VoxelOps Logo
   :align: center
   :width: 500px

.. image:: https://github.com/yalab-devops/VoxelOps/actions/workflows/ci.yml/badge.svg
   :target: https://github.com/yalab-devops/VoxelOps/actions/workflows/ci.yml
   :alt: CI
.. image:: https://codecov.io/gh/yalab-devops/VoxelOps/branch/main/graph/badge.svg?token=YOUR_CODECOV_TOKEN
   :target: https://codecov.io/gh/yalab-devops/VoxelOps
   :alt: codecov
.. image:: https://app.codacy.com/project/badge/Grade/YOUR_CODACY_PROJECT_ID
   :target: https://www.codacy.com/gh/yalab-devops/VoxelOps/dashboard?utm_source=github.com&utm_medium=referral&utm_content=yalab-devops/VoxelOps&utm_campaign=Badge_Grade
   :alt: Codacy Badge
.. image:: https://badge.fury.io/py/voxelops.svg
   :target: https://badge.fury.io/py/voxelops
   :alt: PyPI version
.. image:: https://readthedocs.org/projects/voxelops/badge/?version=latest
   :target: https://voxelops.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status
.. image:: https://img.shields.io/badge/License-MIT-blue.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License: MIT

**Clean, simple neuroimaging pipeline automation for brain banks.**

VoxelOps wraps Docker-based neuroimaging tools into clean Python functions
that return plain dicts -- ready for your database, your logs, and your
peace of mind.

.. code-block:: python

   from voxelops import run_qsiprep, QSIPrepInputs

   result = run_qsiprep(
       QSIPrepInputs(bids_dir="/data/bids", participant="01"),
       nprocs=16,
   )

   print(result["duration_human"])   # "1:30:00"
   print(result["command"])          # exact Docker command for reproducibility

Key Features
------------

- **Simple functions** -- ``run_*()`` functions that return dicts, no classes or inheritance
- **Typed schemas** -- dataclass inputs, outputs, and defaults for every procedure
- **Reproducibility** -- the exact Docker command is stored in every execution record
- **Database-ready** -- results are plain dicts, trivial to persist anywhere
- **Brain bank defaults** -- define standard parameters once, reuse everywhere

Available Procedures
--------------------

.. list-table::
   :header-rows: 1
   :widths: 20 40 20 20

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

Installation
------------

.. code-block:: bash

   pip install voxelops

Requirements: Python >= 3.8, Docker installed and accessible.

.. toctree::
   :maxdepth: 2
   :caption: Contents

   getting_started
   workflows
   source/modules
   tutorials
   contributing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


