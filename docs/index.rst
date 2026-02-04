VoxelOps Documentation
======================

.. image:: https://github.com/GalKepler/VoxelOps/blob/main/docs/images/Gemini_Generated_Image_m9bi47m9bi47m9bi.png?raw=true
   :alt: VoxelOps Logo
   :align: center

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
