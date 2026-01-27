Our MRI protocol produces (after conversion to BIDS) the following structure:

(per session):

├── anat
│   ├── sub-01_ses-01_ce-corrected_T1w.json
│   ├── sub-01_ses-01_ce-corrected_T1w.nii.gz
│   ├── sub-01_ses-01_ce-uncorrected_T1w_heudiconv291.json
│   ├── sub-01_ses-01_ce-uncorrected_T1w.json
│   ├── sub-01_ses-01_ce-uncorrected_T1w.nii.gz
│   ├── sub-01_ses-01_ce-uncorrected_T2w.json
│   ├── sub-01_ses-01_ce-uncorrected_T2w.nii.gz
│   ├── sub-01_ses-01_FLAIR.json
│   └── sub-01_ses-01_FLAIR.nii.gz
├── dwi
│   ├── sub-01_ses-01_dir-AP_dwi.bval
│   ├── sub-01_ses-01_dir-AP_dwi.bvec
│   ├── sub-01_ses-01_dir-AP_dwi.json
│   ├── sub-01_ses-01_dir-AP_dwi.nii.gz
│   ├── sub-01_ses-01_dir-PA_dwi.bval
│   ├── sub-01_ses-01_dir-PA_dwi.bvec
│   ├── sub-01_ses-01_dir-PA_dwi.json
│   └── sub-01_ses-01_dir-PA_dwi.nii.gz
├── fmap
│   ├── sub-01_ses-01_acq-dwi_dir-PA_epi.json
│   ├── sub-01_ses-01_acq-dwi_dir-PA_epi.nii.gz
│   ├── sub-01_ses-01_acq-func_dir-AP_epi.json
│   ├── sub-01_ses-01_acq-func_dir-AP_epi.nii.gz
│   ├── sub-01_ses-01_acq-func_dir-PA_epi.json
│   └── sub-01_ses-01_acq-func_dir-PA_epi.nii.gz
├── func
│   ├── sub-01_ses-01_task-emotionalnback_bold.json
│   ├── sub-01_ses-01_task-emotionalnback_bold.nii.gz
│   ├── sub-01_ses-01_task-emotionalnback_events.tsv
│   ├── sub-01_ses-01_task-rest_bold.json
│   ├── sub-01_ses-01_task-rest_bold.nii.gz
│   └── sub-01_ses-01_task-rest_events.tsv
└── sub-01_ses-01_scans.tsv

The thing is, that the *dir-PA_dwi files aren't actual DWI files (they're comrised of obly B0s)