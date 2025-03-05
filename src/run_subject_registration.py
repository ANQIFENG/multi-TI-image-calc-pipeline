#!/usr/bin/env python

import os
import subprocess


def register_mprage_to_mni(mprage_path, atlas_dir, output_dir, num_threads=1):
    fixed_image = os.path.join(atlas_dir, "mni_icbm152_t1_tal_nlin_sym_09c_pow2.nii.gz")
    fixed_brainmask = os.path.join(atlas_dir, "mni_icbm152_t1_tal_nlin_sym_09c_mask_pow2.nii.gz")
    fixed_regmask = os.path.join(atlas_dir, "mni_icbm152_t1_tal_nlin_sym_09c_regmask_pow2.nii.gz")

    reg_cmd = [
        "python", "/opt/run/registration.py",
        "--moving-image", mprage_path,
        "--fixed-image", fixed_image,
        "--fixed-brainmask", fixed_brainmask,
        "--fixed-regmask", fixed_regmask,
        "--scale-fixed",
        "--num-threads", str(num_threads),
        "--output-dir", output_dir

    ]
    subprocess.run(reg_cmd, check=True)