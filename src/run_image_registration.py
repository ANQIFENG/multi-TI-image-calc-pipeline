#!/usr/bin/env python

import subprocess


def register_fgatir_to_mprage(mprage, fgatir, brain_mask, mprage_registered, mprage_transform, output_dir, num_threads=1):

    reg_cmd = [
        "python", "/opt/run/registration.py",
        "--moving-image", fgatir,
        "--fixed-image", mprage,
        "--fixed-brainmask", brain_mask,
        "--fixed-transform", mprage_transform,
        "--fixed-target", mprage_registered,
        "--num-threads", str(num_threads),
        "--output-dir", output_dir
    ]
    subprocess.run(reg_cmd, check=True)
