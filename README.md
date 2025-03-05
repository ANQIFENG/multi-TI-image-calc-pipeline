# multi-TI-image-calc-pipeline
This is a streamlined pipeline for generating multi-TI images from paired T1-weighted MRI acquisitions 
(e.g., MPRAGE & FGATIR) with identical parameters but different inversion times.

**Pipeline Steps:**  
- **Brain Extraction**: HD-BET  
- **Registration**: Co-register to MNI space  
- **Bias Field Correction**:  
  - Compute N4 bias field for both T1-weighted images  
  - Derive harmonic bias field  
  - Apply correction using the harmonic bias field  
- **Mask Computation**:  
  - Background mask  
  - White matter mask  
- **Intensity Normalization**: Fuzzy C-means white matter mean normalization  
- **Map Computation**:  
  - Generate T1 and PD maps  
  - Synthesize multi-TI images from these maps  



## How to run :runner:
### Prerequisites
- **Operating System:** Linux or OSX.
- **Hardware:** GPU is required.


### Installation
You can install the Singularity Image with the following command:
```bash
singularity pull --docker-login docker://registry.gitlab.com/anqifeng/smri_pipeline:v1.0.0
```
Alternatively, you can download the Singularity Image directly from [[link](https://mega.nz/file/QzcXmIjK#oJvzHiriYlNroSfR6cp5pWFShmFEoeaPU1l8apmZGp4)].


### Usage
Run the processing pipeline with the following command, 
replacing placeholders with actual paths to your input files and output directory. 
Input files must be in NIfTI format (`.nii` or `.nii.gz`).

Command:
```bash
singularity run -e --nv smri_pipeline.sif \
            --mprage ${path_to_your_mprage_image} \
            --fgatir ${path_to_your_fgatir_image} \
            --out_dir ${path_to_the_directory_where_you_want_the_output_to_be_stored} \
            --tr ${repetition_time_for_your_mprage_and_fgatir_images} \
            --ti_mprage ${inversion_time_for_your_mprage_image} \
            --ti_fgatir ${inversion_time_for_your_fgatir_image} \
            --ti_min ${minimum_inversion_time_for_synthesizing_multi_ti_images} \
            --ti_max ${maximum_inversion_time_for_synthesizing_multi_ti_images} \
            --ti_step ${step_size_for_inversion_times_between_ti_min_and_ti_max} \
            --num_workers ${number_of_workers_for_parallel_processing} \
            --save_intermediate ${flag_to_save_intermediate_results}
 ```   

Example bash script:
```bash
#!/bin/bash

# Define paths to your data, output directory and singularity image
mprage_path="./MPRAGE.nii.gz"
fgatir_path="./FGATIR.nii.gz"
output_dir="./ratnus_outputs"
sif_path="./smri_pipeline_v1.0.0.sif"
repetition_time=4000.0 # ms
inversion_time_mprage=1400.0 # ms
inversion_time_fgatir=400.0 # ms
inversion_time_min=400.0 # ms
inversion_time_max=1400.0 # ms
inversion_time_step=20.0 # ms
num_workers=8
whether_save_intermediate=False #bool

# Run multi-TI images calculation pipeline
singularity run --nv $sif_path \
                --mprage ${mprage_path} \
                --fgatir ${fgatir_path} \
                --out_dir ${output_dir} \
                --tr ${repetition_time} \
                --ti_mprage ${inversion_time_mprage} \
                --ti_fgatir ${inversion_time_fgatir} \
                --ti_min ${inversion_time_min} \
                --ti_max ${inversion_time_max} \
                --ti_step ${inversion_time_step} \
                --num_workers ${num_workers} \
                --save_intermediate ${whether_save_intermediate}
```


## Details :brain:
### Inputs 
<div style="text-align: center;">
  <table>
    <thead>
      <tr>
        <th></th>
        <th>Preparation</th>
        <th >Required</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td style="text-align: center;">mprage</td>
        <td style="text-align: left;"> 
          <ul>
              <li> Path to the MPRAGE image file. </li>
          </ul>
        </td>
        <td style="text-align: center;">✅</td>
      </tr>
      <tr>
        <td style="text-align: center;">fgatir</td>
        <td style="text-align: left;"> 
          <ul>
              <li> Path to the FGATIR image file. </li>
          </ul>
        </td>
        <td style="text-align: center;">✅</td>
      </tr>
      <tr>
        <td style="text-align: center;">out_dir</td>
        <td style="text-align: left;"> 
          <ul>
              <li> Directory where output files will be stored. </li>
          </ul>
        </td>
        <td style="text-align: center;">✅</td>
      </tr>
      <tr>
        <td style="text-align: center;">tr</td>
        <td style="text-align: left;">
          <ul>
            <li> Repetition time (TR) for both the MPRAGE and FGATIR images.</li>
            <li> Used for T1/PD calculation and Multi-TI synthesis. </li>
          </ul>
        </td>
        <td style="text-align: center;">✅</td>
      </tr>
      <tr>
        <td style="text-align: center;">ti_mprage</td>
        <td style="text-align: left;">
          <ul>
            <li> Inversion time (TI) for the MPRAGE image.</li>
            <li> Used for T1/PD calculation. </li>
          </ul>
        </td>
        <td style="text-align: center;">✅</td>
      </tr>
      <tr>
        <td style="text-align: center;">ti_fgatir</td>
        <td style="text-align: left;">
          <ul>
            <li> Inversion time (TI) for the FGATIR image.</li>
            <li> Used for T1/PD calculation. </li>
          </ul>
        </td>
        <td style="text-align: center;">✅</td>
      </tr>
      <tr>
        <td style="text-align: center;">ti_min</td>
        <td style="text-align: left;"> 
          <ul>
              <li> Minimum inversion time (TI) for Multi-TI image synthesis. </li> 
          </ul>
        </td>
        <td style="text-align: center;">✅</td>
      </tr>
      <tr>
        <td style="text-align: center;">ti_max</td>
        <td style="text-align: left;"> 
          <ul>
              <li> Maximum inversion time (TI) for Multi-TI image synthesis. </li> 
          </ul>
        </td> 
        <td style="">✅</td>
      </tr>
      <tr>
        <td style="text-align: center;">ti_step</td>
        <td style="text-align: left;"> 
          <ul>
              <li> Increment between Minimum TI and Maximum TI for Multi-TI image synthesis. </li> 
          </ul>
        </td> 
        <td style="">✅</td>
      </tr>
      <tr>
        <td style="text-align: center;">num_workers</td>
        <td style="text-align: left;">
          <ul>
          <li> Number of CPU cores for parallel processing. </li>
          </ul>
        </td>
        <td style="text-align: center;">✅</td>
      </tr>
      <tr>
        <td style="text-align: center;">save_intermediate</td>
        <td style="text-align: left;">
          <ul>
          <li> Boolean flag to save intermediate results (True or False). Default: False. </li>
        </ul>
        </td>
        <td style="text-align: center;">🟡</td>
      </tr>
    </tbody>
  </table>
</div>
✅ Required parameters. 🟡 Optional parameters (defaults applied if not provided).

### Outputs
#### Output Structure
The output directory (`/path/to/output`) is organized into four subdirectories:

``` 
/path/to/output
    └── proc
        └── [output NIfTI files]
    └── logs
        └── [images-processing-pipeline]
            └── [processing logs]
    └── qa
        └── [images-processing-pipeline]
            └── [QA images]
    └── tmp 
        └── [temporary results]
```

- `proc`: Stores the output NIfTI files.
- `log`: Stores the logs from the processing steps.
- `qa`: Stores the images for Quality Assurance (QA). It allows for a quick review of the results.
- `tmp`: Stores temporary results (only created if `save_intermediate=True`).

#### Output Files
RATNUS generates multiple output NIfTI files in `proc` directory. 
The output file names have specific suffixes that represent their content. 
Below is a list of the output files and their descriptions:

- `*_reg_thre.nii.gz`: MPRAGE and FGATIR images registered to MNI space.
- `*_transform.mat`: Transformation matrix for MPRAGE and FGATIR registration.
- `*_n4sqrt.nii.gz`: MPRAGE and FGATIR images after N4 bias field correction.
- `*_bias.nii.gz`: Bias field for MPRAGE and FGATIR images.
- `*_harmonic_bias.nii.gz`: Harmonic bias field.
- `*_wmn.nii.gz`: MPRAGE and FGATIR images after white matter mean normalization. Finish processing stage, ready for further calculations such as PD and T1 maps.
- `*_wm_mask.nii.gz`: White matter mask in MNI space.
- `*_bg_mask.nii.gz`: Background mask in MNI space.
- `*_brain_mask.nii.gz`: Brain mask in MNI space.
- `*_t1_map.nii.gz`: T1 map.
- `*_pd_map.nii.gz`: PD map.
- `multi-ti/synT1_xxx.nii.gz`: Multi-TI images, where `xxx` represents the TI value.

### Citation
If you find this repository useful, please cite our paper: <br>
RATNUS: Rapid, Automatic Thalamic Nuclei Segmentation using Multimodal MRI inputs.

```bibtex
@article{feng2024ratnus,
  title={RATNUS: Rapid, Automatic Thalamic Nuclei Segmentation using Multimodal MRI inputs},
  author={Feng, Anqi and Bian, Zhangxing and Dewey, Blake E and Colinco, Alexa Gail and Zhuo, Jiachen and Prince, Jerry L},
  journal={arXiv preprint arXiv:2409.06897},
  year={2024}
}


