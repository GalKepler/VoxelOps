# VoxelOps Notebooks

Jupyter notebooks demonstrating VoxelOps for neuroimaging data processing.

## Notebooks

### Basic Procedures

1. **[01_heudiconv_basics.ipynb](01_heudiconv_basics.ipynb)** -- DICOM to BIDS Conversion
   - Convert DICOM files to BIDS format using heuristic files
   - Configuration, batch processing, and error handling

2. **[02_qsiprep_basics.ipynb](02_qsiprep_basics.ipynb)** -- Diffusion MRI Preprocessing
   - Preprocess diffusion-weighted imaging data
   - Resource allocation, HTML QC reports, batch processing

3. **[03_qsirecon_basics.ipynb](03_qsirecon_basics.ipynb)** -- Diffusion Reconstruction
   - Fit diffusion models (DTI, CSD, MAPMRI, etc.)
   - Generate tractography and structural connectivity matrices

4. **[04_qsiparc_basics.ipynb](04_qsiparc_basics.ipynb)** -- Parcellation
   - Apply parcellation schemes to reconstruction outputs
   - Extract regional diffusion metrics

### Complete Workflow

5. **[05_full_pipeline.ipynb](05_full_pipeline.ipynb)** -- End-to-End Pipeline
   - Full pipeline: DICOM -> BIDS -> QSIPrep -> QSIRecon -> QSIParc
   - Chaining procedures, batch processing, saving execution records

## Getting Started

### Prerequisites

1. **Install VoxelOps**:
   ```bash
   pip install voxelops

   # Or for development:
   pip install -e "/path/to/VoxelOps"
   ```

2. **Install Jupyter**:
   ```bash
   pip install jupyter matplotlib pandas seaborn

   # Or install with the notebooks extras:
   pip install -e "/path/to/VoxelOps[notebooks]"
   ```

3. **Docker**: Ensure Docker is installed and running

4. **FreeSurfer License**: Required for QSIPrep/QSIRecon. Obtain from https://surfer.nmr.mgh.harvard.edu/registration.html

### Running Notebooks

1. Start Jupyter: `jupyter notebook`
2. Navigate to the `notebooks/` directory
3. Update paths in each notebook to match your data layout
4. Run cells sequentially

## Expected Directory Structure

Notebooks assume a layout like:

```
/data/
    raw/dicom/          # Raw DICOM files (sub-01/, sub-02/, ...)
    bids/               # BIDS-formatted dataset
    derivatives/
        qsiprep/        # QSIPrep outputs
        qsirecon/       # QSIRecon outputs
        qsiparc/        # QSIParc outputs
    work/               # Working directories (can be deleted after processing)
```

## Tips

- **Start small**: Test with one participant before batch processing
- **Monitor resources**: Check disk space, memory, and CPU usage
- **Review QC reports**: Always check HTML reports after QSIPrep/QSIRecon
- **Save records**: Store execution result dicts for provenance tracking
- **Pin Docker images**: Use specific versions (e.g., `pennlinc/qsiprep:1.0.2`) for reproducibility

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Docker permission denied | Add your user to the `docker` group |
| Out of memory | Reduce `mem_mb` or increase Docker memory limits |
| BIDS validation errors | Check participant directories use `sub-` prefix |
| FreeSurfer license error | Verify `fs_license` path points to a valid license file |

## Additional Resources

- **VoxelOps Documentation**: [voxelops.readthedocs.io](https://voxelops.readthedocs.io)
- **BIDS Specification**: [bids-specification.readthedocs.io](https://bids-specification.readthedocs.io/)
- **QSIPrep Documentation**: [qsiprep.readthedocs.io](https://qsiprep.readthedocs.io/)
- **FreeSurfer**: [surfer.nmr.mgh.harvard.edu](https://surfer.nmr.mgh.harvard.edu/)
