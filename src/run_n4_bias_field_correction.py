#!/usr/bin/env python

import logging
import os
from pathlib import Path
import subprocess


def bias_correction(image: str, out_dir: str):
    ants_env = os.environ.copy()
    ants_env["NSLOTS"] = "1"
    ants_env["ANTS_RANDOM_SEED"] = "1"

    image = Path(image).resolve()
    out_dir = Path(out_dir).resolve()
    out_dir.mkdir(exist_ok=True, parents=True)

    stem = image.name.split(".")[0]
    image_out_fp = out_dir / f"{stem}_n4.nii.gz"
    bias_field_out_fp = out_dir / f"{stem}_bias.nii.gz"

    n4_cmd = [
        "N4BiasFieldCorrection",
        "--image-dimensionality", "3",
        "--input-image", str(image),
        "--rescale-intensities", "1",
        "--shrink-factor", "4",
        '--convergence', '[200x200x200x200,0.0005]',
        "--output", f'[{image_out_fp},{bias_field_out_fp}]',
        "--verbose",
    ]

    logging.info("Running N4BiasFieldCorrection")
    subprocess.run(
        n4_cmd,
        check=True,
        env=ants_env,
    )


