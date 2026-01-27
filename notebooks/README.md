# YALab Procedures Notebooks

This directory contains Jupyter notebooks demonstrating the use of yalab-procedures for neuroimaging data processing.

## Notebooks Overview

### Basic Procedures

1. **[01_heudiconv_basics.ipynb](01_heudiconv_basics.ipynb)** - DICOM to BIDS Conversion
   - Convert DICOM files to BIDS format
   - Use heuristic files for mapping
   - Basic usage, configuration, and batch processing
   - Error handling and validation

2. **[02_qsiprep_basics.ipynb](02_qsiprep_basics.ipynb)** - Diffusion MRI Preprocessing
   - Preprocess diffusion-weighted imaging data
   - Resource allocation and configuration
   - View HTML QC reports
   - Batch processing examples

3. **[03_qsirecon_basics.ipynb](03_qsirecon_basics.ipynb)** - Diffusion Reconstruction
   - Fit diffusion models (DTI, CSD, MAPMRI, etc.)
   - Generate tractography
   - Create structural connectivity matrices
   - Visualize connectivity matrices

4. **[04_qsiparc_basics.ipynb](04_qsiparc_basics.ipynb)** - Parcellation and Regional Analysis
   - Apply parcellation schemes
   - Extract regional diffusion metrics
   - Combine statistics across participants
   - Visualize regional metrics

### Complete Workflows

5. **[05_full_pipeline.ipynb](05_full_pipeline.ipynb)** - End-to-End Pipeline
   - Run complete pipeline: DICOM → BIDS → QSIPrep → QSIRecon → QSIParc
   - Chain procedures together
   - Batch processing multiple participants
   - Save comprehensive pipeline records

## Getting Started

### Prerequisites

1. **Install yalab-procedures**:
   ```bash
   # Using uv (recommended)
   uv pip install -e /path/to/yalab-procedures-v2

   # Or using pip
   pip install -e /path/to/yalab-procedures-v2
   ```

2. **Install Jupyter and visualization packages**:
   ```bash
   # Using uv (recommended)
   uv pip install jupyter matplotlib pandas seaborn

   # Or using pip
   pip install jupyter matplotlib pandas seaborn

   # Or install with the notebooks extras
   uv pip install -e "/path/to/yalab-procedures-v2[notebooks]"
   ```

3. **Docker**: Ensure Docker is installed and running

4. **FreeSurfer License**: Obtain from https://surfer.nmr.mgh.harvard.edu/registration.html

### Running Notebooks

1. Start Jupyter:
   ```bash
   jupyter notebook
   ```

2. Navigate to the `notebooks/` directory

3. Open a notebook and update paths to match your data structure

4. Run cells sequentially

## Directory Structure

Notebooks assume the following directory structure (adjust paths as needed):

```
/data/
├── raw/
│   └── dicom/           # Raw DICOM files
│       └── sub-01/
│       └── sub-02/
│
├── bids/                # BIDS-formatted dataset
│   ├── sub-01/
│   ├── sub-02/
│   └── dataset_description.json
│
├── derivatives/         # Processing outputs
│   ├── qsiprep/
│   │   └── qsiprep/    # QSIPrep outputs
│   ├── qsirecon/
│   │   └── qsirecon/   # QSIRecon outputs
│   └── qsiparc/
│       └── qsiparc/    # QSIParc outputs
│
├── work/               # Working directories (can be deleted after processing)
│   ├── heudiconv/
│   ├── qsiprep/
│   ├── qsirecon/
│   └── qsiparc/
│
└── records/            # Execution records (JSON)
    ├── pipeline/
    ├── qsiprep/
    └── qsirecon/

/config/
├── heuristics/         # HeudiConv heuristic files
│   └── brain_bank.py
└── recon_specs/        # QSIRecon reconstruction specifications
    ├── dsi_studio_gqi.json
    ├── mrtrix_msmt_csd.json
    └── amico_noddi.json
```

## Customization

Each notebook includes sections for:
- **Path configuration**: Update paths to match your setup
- **Resource allocation**: Adjust cores and memory based on your system
- **Docker images**: Pin specific versions for reproducibility
- **Batch processing**: Process multiple participants efficiently

## Common Workflows

### Single Participant Processing

1. Start with `01_heudiconv_basics.ipynb` to convert DICOM to BIDS
2. Continue with `02_qsiprep_basics.ipynb` for preprocessing
3. Run `03_qsirecon_basics.ipynb` for reconstruction
4. Finish with `04_qsiparc_basics.ipynb` for parcellation

### Batch Processing

Use `05_full_pipeline.ipynb` to process multiple participants through the complete pipeline.

### Configuration Management

After the configuration enhancement features are implemented:
- `06_configuration_management.ipynb` - Using config files, environment variables, and templates
- `07_logging_and_monitoring.ipynb` - Real-time streaming, log querying, and aggregation

## Tips

- **Start small**: Test with one participant before running batch processing
- **Monitor resources**: Check disk space, memory usage, and CPU utilization
- **Review QC reports**: Always check HTML reports for quality control
- **Save execution records**: Store results in a database for provenance tracking
- **Version control**: Pin Docker image versions for reproducibility
- **Error handling**: Implement try-except blocks for production workflows

## Troubleshooting

### Docker Issues

- **Permission denied**: Ensure your user is in the `docker` group
- **Out of memory**: Increase Docker memory limits in settings
- **Image not found**: Pull images manually: `docker pull pennlinc/qsiprep:1.0.2`

### Path Issues

- **BIDS validation errors**: Check that participant directories use `sub-` prefix
- **FreeSurfer license**: Ensure license file path is correct
- **Input not found**: Verify directory structure matches expected format

### Processing Failures

- **Check logs**: Execution records include stdout/stderr for debugging
- **Review HTML reports**: QC reports show processing quality and issues
- **Disk space**: Ensure sufficient space in work and output directories
- **Memory**: Some steps require significant RAM (32GB+ recommended)

## Contributing

Found a bug or have a suggestion? Please:
1. Check existing issues at https://github.com/yalab/yalab-procedures-v2/issues
2. Create a new issue with details about your environment and the problem
3. Include relevant notebook cells and error messages

## Additional Resources

- **yalab-procedures Documentation**: See main [README.md](../README.md)
- **BIDS Specification**: https://bids-specification.readthedocs.io/
- **QSIPrep Documentation**: https://qsiprep.readthedocs.io/
- **QSIRecon Documentation**: https://qsiprep.readthedocs.io/en/latest/reconstruction.html
- **FreeSurfer**: https://surfer.nmr.mgh.harvard.edu/

## License

These notebooks are provided as examples and educational resources. Modify as needed for your specific use case.
