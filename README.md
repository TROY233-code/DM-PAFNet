# DM-PAFNet: Data Preprocessing Pipeline

This repository contains the data preprocessing pipeline for the paper "DM-PAFNet: A Dual-Stage Deep Learning Framework for Parkinson's Disease Staging Prediction via Multi-modal MRI and Clinical Prior Fusion".

The scripts in this directory are designed to process raw T1-weighted MRI and Diffusion Tensor Imaging (DTI) data from the PPMI dataset. The pipeline performs a series of standard neuroimaging preprocessing steps, including reorientation, skull stripping, registration to a standard space, bias field correction, and intensity normalization. The final output is a set of clean and standardized image files ready for input into our deep learning model.

## Prerequisites

Before running the scripts, please ensure you have the following software and libraries installed.

### 1. Software

* **Python (3.8 or higher)**
* **FSL**: [https://fsl.fmrib.ox.ac.uk/fsl/fslwiki](https://fsl.fmrib.ox.ac.uk/fsl/fslwiki)
* **ANTs (for N4 Bias Correction)**: [https://github.com/ANTsX/ANTs](https://github.com/ANTsX/ANTs)

*Please make sure that FSL and ANTs tools are correctly installed and their paths are added to your system's environment variables.*

### 2. Python Libraries

We recommend creating a dedicated conda or virtual environment. The required libraries can be installed via pip:

```bash
pip install -r requirements.txt
```

## Dataset Structure

Please organize your raw data according to the following directory structure before running the scripts:

```
/your/main/data/directory/
├── raw/
│   ├── subject_001/
│   │   ├── T1w.nii.gz
│   │   └── DTI.nii.gz
│   ├── subject_002/
│   │   ├── T1w.nii.gz
│   │   └── DTI.nii.gz
│   └── ...
└── processed/  # This directory will be created to store the final results
```

## Usage

The preprocessing pipeline consists of 5 sequential steps. Please run the scripts in the specified order.

### Step 1: Reorient Images

This script reorients the raw images to a standard orientation (e.g., LAS).

```bash
python step1_reorient.py --input_folder ./data/raw --output_folder ./data/step1_oriented
```

### Step 2: Skull Stripping

This script performs brain extraction (skull stripping) on the reoriented images using FSL's BET.

```bash
python step2_skull_stripping.py --input_folder ./data/step1_oriented --output_folder ./data/step2_brain
```

### Step 3: Registration

This script registers the brain-extracted images to the MNI152 standard space template.

```bash
python step3_registration.py --input_folder ./data/step2_brain --output_folder ./data/step3_registered --template_path /path/to/your/MNI152_template.nii.gz
```

### Step 4: Bias Field Correction

This script applies N4 bias field correction to correct for intensity inhomogeneities.

```bash
python step4_bias_correction.py --input_folder ./data/step3_registered --output_folder ./data/step4_n4
```

### Step 5: Final Normalization and Enhancement

This script performs final intensity normalization and other enhancements to produce the final data ready for model training.

```bash
python step5_final_fix_enhance.py --input_folder ./data/step4_n4 --output_folder ./data/processed
```

## Final Output

After running all five steps, the `processed` directory will contain the fully preprocessed NIfTI files (e.g., `PPMI_3612_final_enhanced.nii.gz`), which can be used as input for the main deep learning model.
````