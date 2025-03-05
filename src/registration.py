#!/usr/bin/env python
from argparse import ArgumentParser
import os
import shutil
from pathlib import Path
import subprocess
from typing import Optional

import nibabel as nib
import numpy as np
from SimpleITK import (
    ReadTransform,
    WriteTransform,
    Similarity3DTransform,
    Euler3DTransform,
)


def extract_rigid_transform(transform: Path, target: Path) -> (Path, Path):
    """Extract a rigid and (inverse) scale transform from a similarity (7 DOF) transform

    This function splits a similarity transform into a rigid and scale scale transform.
    The scale transform is inverted (for use in scaling a fixed image).
    The scale transform has an added center that corrects for scaling.

    Args:
        transform: path to the similarity transform to be split
        target: path to the fixed image used to create the transform

    Returns:
        Two file paths. The first pointing to the created (inverse) scale transform and
        the second pointing to the extracted rigid transform.
    """
    fixed_obj = nib.Nifti1Image.load(target)

    tfm = ReadTransform(str(transform)).Downcast()

    inv_scale_tfm = Similarity3DTransform()
    inv_scale_tfm.SetScale(tfm.GetInverse().Downcast().GetScale())
    inv_scale_tfm.SetCenter(
        (
            0,
            (fixed_obj.shape[1] - fixed_obj.shape[2]) * fixed_obj.header.get_zooms()[0],
            (fixed_obj.shape[1] - fixed_obj.shape[2]) * fixed_obj.header.get_zooms()[0],
        )
    )
    WriteTransform(
        inv_scale_tfm, str(transform.parent / (transform.stem + "_invscale" + transform.suffix))
    )
    tfm.SetScale(1.0)

    rigid = Euler3DTransform()
    rigid.SetMatrix(tfm.GetMatrix())
    rigid.SetTranslation(tfm.GetTranslation())
    rigid.SetCenter(tfm.GetCenter())

    WriteTransform(rigid, str(transform.parent / (transform.stem + "_rigid" + transform.suffix)))
    return (
        transform.parent / (transform.stem + "_invscale" + transform.suffix),
        transform.parent / (transform.stem + "_rigid" + transform.suffix),
    )


def extract_from_composite(composite: Path) -> Path:
    """Extract a single transform from a composite transform wrapper

    This function extracts a transform from a composite transform wrapper. This is
    intended to be used when a composite transform is created, but only contains a
    single transform.

    Args:
        composite: path to the composite transform file

    Returns:
        A file path pointing to the extracted transform file.
    """
    comp_tfm = ReadTransform(str(composite)).Downcast()
    comp_tfm.FlattenTransform()
    WriteTransform(
        comp_tfm.GetNthTransform(0).Downcast(),
        str(composite.parent / composite.name.replace("Composite.h5", "Rigid.mat")),
    )
    return composite.parent / composite.name.replace("Composite.h5", "Rigid.mat")


def compose_transforms(transform_list: list[Path], output_filepath: Path) -> None:
    """Compose a list of rigid transforms into a single transform

    This function composes a list of rigid transforms into a single rigid transform.
    The transforms in the list should be in reverse application order. For example, if
    [A, B, C] is given as input, the transforms will be applied C, then B, then A.

    Args:
        transform_list: a list of paths pointing to transforms to be composed
        output_filepath: path for the output composed transform
    """
    transforms = [
        ReadTransform(str(transform_file)).Downcast() for transform_file in transform_list
    ]
    mat = np.eye(3)
    c = np.zeros(3)
    t = np.zeros(3)

    for curr_tx in reversed(transforms):
        mat_curr = np.asarray(curr_tx.GetMatrix()).reshape(3, 3)
        c_curr = np.asarray(curr_tx.GetCenter())
        t_curr = np.asarray(curr_tx.GetTranslation())
        mat = np.dot(mat_curr, mat)
        t = np.dot(mat_curr, t + c - c_curr) + t_curr + c_curr - c

    output_tfm = Euler3DTransform()
    output_tfm.SetMatrix(mat.flatten())
    output_tfm.SetTranslation(t)
    output_tfm.SetCenter(c)
    WriteTransform(output_tfm, str(output_filepath))


def clip_to_input_range(img_path: Path, input_path: Path):
    """Clip an image to the range of another image

    This function clips an image to the range of another image. This is useful for
    clipping a bias corrected image to the range of the original image.

    Args:
        img_path: path to the image to be clipped
        input_path: path to the image to use for clipping
    """
    img_obj = nib.Nifti1Image.load(img_path)
    input_obj = nib.Nifti1Image.load(input_path)
    img_data = img_obj.get_fdata()
    input_data = input_obj.get_fdata()
    img_data = np.clip(img_data, input_data.min(), input_data.max())
    nib.Nifti1Image(img_data, None, img_obj.header).to_filename(img_path)


def main(args: Optional[list[str]] = None):
    parser = ArgumentParser(
        prog="Registration",
        description=(
            "Registration between two images (MOVING and FIXED). "
            "The MOVING image will be rigidly registered to the FIXED image. "
            "A registration mask (FIXED_REGMASK) and a brain mask (FIXED_BRAINMASK) "
            "are also required for the fixed image. If SCALE_FIXED is set to 1, "
            "the FIXED image will be globally scaled to match the MOVING image. "
            "This improves consistency of registration when only using rigid transforms. "
            "If the FIXED image has a transform from a previous registration "
            "(i.e., to an atlas), this can be included in the final transform by "
            "passing it as FIXED_TRANSFORM. The transformed image will be clipped "
            "to the range of the MOVING image to lessen artifacts from interpolation. "
            "\n"
            "Files should be in the IACL directory structure "
            ".../{PROJECT}/{SUBJECT}/{SESSION}/proc."
            "All inputs should be an absolute path to a file."
        ),
    )
    parser.add_argument(
        "--moving-image",
        help="path to moving image (to be registered)",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--fixed-image",
        help="path to fixed image (registration target)",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--fixed-brainmask",
        help="path to brain mask for fixed image",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--fixed-regmask",
        help="path to registration mask for fixed image (i.e., dilated head mask)",
        type=Path,
    )
    parser.add_argument(
        "--fixed-transform",
        help="path to existing transform for fixed image (requires fixed-target)",
        type=Path,
    )
    parser.add_argument(
        "--fixed-target",
        help="path to registered version of fixed image (required with fixed-transform)",
        type=Path,
    )
    parser.add_argument(
        "--scale-fixed",
        help="scale the fixed image globally to match the moving image",
        action="store_true",
        default=False,
    )
    parser.add_argument(
        "--num-threads",
        help="number of threads to use for ANTs programs",
        type=int,
        default=1,
    )
    parser.add_argument(
        "--output-dir",
        help="directory to save the output files",
        type=Path,
        required=True,
    )
    parsed_args = parser.parse_args(args)

    # Set ITK_GLOBAL_DEFAULT_NUMBER_OF_THREADS to manage multithreading in ANTs
    ants_env = os.environ.copy()
    ants_env["NSLOTS"] = str(parsed_args.num_threads)
    ants_env["ANTS_RANDOM_SEED"] = "1"

    # Get absolute paths for all file path inputs and check that they exist
    for argname in [
        "moving_image",
        "fixed_image",
        "fixed_brainmask",
        "fixed_regmask",
        "fixed_transform",
        "fixed_target",
    ]:
        if getattr(parsed_args, argname) is not None:
            setattr(parsed_args, argname, getattr(parsed_args, argname).resolve())
            if not getattr(parsed_args, argname).exists():
                raise ValueError("%s does not exist." % argname.replace("_", "-"))

    # Check that fixed-transform and fixed-target are both specfied (or both None)
    if (parsed_args.fixed_transform is None) ^ (parsed_args.fixed_target is None):
        raise ValueError("fixed-transform and fixed-target must both be specified or not at all.")

    # Path name variables
    output_dir = parsed_args.output_dir.resolve()
    output_dir.mkdir(exist_ok=True, parents=True)

    moving_stem = parsed_args.moving_image.name.split(".")[0]
    fixed_stem = parsed_args.fixed_image.name.split(".")[0]
    ext = "".join(parsed_args.moving_image.suffixes)
    temp_dir = output_dir / (moving_stem + "__" + fixed_stem)
    temp_dir.mkdir(exist_ok=True, parents=True)

    # INITIAL REGISTRATION
    # Initial registration is done using antsAI to provided multiple starting points for a quick registration.
    # Moving and fixed images are subsampled to 4x4x4mm for speed.
    # antsAI is then run with a small sweep of angles and a 40mm grid of starting points.
    # The starting point options (and subsampling) are taken from antsBrainExtraction script in ANTs.
    # Mattes is used for the metric (more stable than MI)
    # Sampling grid is reduced for speed (still robust).
    # If SCALE_FIXED is 1, we run with a Similarity (7 DOF) transform to get a global scale.
    # We also extract the inverse scale and rigid transforms from the Similarity transform
    # The inverse scale transform is used to scale the fixed image (and both masks).
    # We then assign the scaled versions to use later in registration.
    # IF SCALE_FIXED is 0, we use a Rigid (6 DOF) transform in antsAI and assign the fixed image and masks.

    # Resample Moving Image
    resample_moving_cmd = [
        "ResampleImageBySpacing",
        "3",
        parsed_args.moving_image,
        str(temp_dir / "moving.nii.gz"),
        "4",
        "4",
        "4",
        "1",
    ]
    subprocess.run(resample_moving_cmd, check=True, env=ants_env)

    # Resample Fixed Image
    resample_fixed_cmd = [
        "ResampleImageBySpacing",
        "3",
        parsed_args.fixed_image,
        str(temp_dir / "fixed.nii.gz"),
        "4",
        "4",
        "4",
        "1",
    ]
    subprocess.run(resample_fixed_cmd, check=True, env=ants_env)

    if parsed_args.scale_fixed:
        # Similarity Registration with antsAI
        scale_fixed_ai = [
            "antsAI",
            "-d",
            "3",
            "-m",
            "Mattes[%s,%s,32,Regular,0.20]"
            % (temp_dir / "fixed.nii.gz", temp_dir / "moving.nii.gz"),
            "-t",
            "Similarity[0.1]",
            "-o",
            str(temp_dir / "ai.mat"),
            "-s",
            "[20,0.12]",
            "-g",
            "[40,0x0x0]",
            "-p",
            "0",
            "-c",
            "10",
            "-v",
        ]
        subprocess.run(scale_fixed_ai, check=True, env=ants_env)

        # Extract rigid and inverse scale transforms from similarity transform
        inv_scale, rigid_transform = extract_rigid_transform(
            temp_dir / "ai.mat",
            parsed_args.fixed_image,
        )

        # Scale fixed image
        scale_image_cmd = [
            "antsApplyTransforms",
            "--dimensionality",
            "3",
            "--input",
            str(parsed_args.fixed_image),
            "--reference-image",
            str(parsed_args.fixed_image),
            "--output",
            str(temp_dir / "scaled_fixed.nii.gz"),
            "--output-data-type",
            "float",
            "--transform",
            str(inv_scale),
            "--verbose",
        ]
        subprocess.run(scale_image_cmd, check=True, env=ants_env)

        # Scale fixed image brainmask
        scale_mask_cmd = [
            "antsApplyTransforms",
            "--dimensionality",
            "3",
            "--input",
            str(parsed_args.fixed_brainmask),
            "--reference-image",
            str(parsed_args.fixed_brainmask),
            "--output",
            str(temp_dir / "scaled_fixed_brainmask.nii.gz"),
            "--interpolation",
            "NearestNeighbor",
            "--output-data-type",
            "float",
            "--transform",
            str(inv_scale),
            "--verbose",
        ]
        subprocess.run(scale_mask_cmd, check=True, env=ants_env)

        # Scale fixed image registration mask (if present)
        fixed_regmask_to_use = None
        if parsed_args.fixed_regmask is not None:
            scale_regmask_cmd = [
                "antsApplyTransforms",
                "--dimensionality",
                "3",
                "--input",
                str(parsed_args.fixed_regmask),
                "--reference-image",
                str(parsed_args.fixed_regmask),
                "--output",
                str(temp_dir / "scaled_fixed_regmask.nii.gz"),
                "--interpolation",
                "NearestNeighbor",
                "--output-data-type",
                "float",
                "--transform",
                str(inv_scale),
                "--verbose",
            ]
            subprocess.run(scale_regmask_cmd, check=True, env=ants_env)
            fixed_regmask_to_use = temp_dir / "scaled_fixed_regmask.nii.gz"

        init_transform_to_use = rigid_transform
        fixed_to_use = temp_dir / "scaled_fixed.nii.gz"
        fixed_brainmask_to_use = temp_dir / "scaled_fixed_brainmask.nii.gz"
    else:
        # Rigid Registration with antsAI
        rigid_antsai_cmd = [
            "antsAI",
            "-d",
            "3",
            "-m",
            "Mattes[%s,%s,32,Regular,0.20]"
            % (temp_dir / "fixed.nii.gz", temp_dir / "moving.nii.gz"),
            "-t",
            "Rigid[0.1]",
            "-o",
            str(temp_dir / "ai_rigid.mat"),
            "-s",
            "[20,0.12]",
            "-g",
            "[40,0x0x0]",
            "-p",
            "0",
            "-c",
            "10",
            "-v",
        ]
        subprocess.run(rigid_antsai_cmd, check=True, env=ants_env)

        init_transform_to_use = temp_dir / "ai_rigid.mat"
        fixed_to_use = parsed_args.fixed_image
        fixed_brainmask_to_use = parsed_args.fixed_brainmask
        fixed_regmask_to_use = parsed_args.fixed_regmask

    # REGISTRATION
    # antsRegistration is used for registration here.
    # There are two "stages", both using Rigid transforms and the Mattes (MI) metric.
    # This registration is initialized with the rigid transform from the initial registration step.
    # In the first stage, we use the "registration mask" to restrict the metric.
    # This mask can also be all 1's without too much difference.
    # This is a large whole head mask, so only cuts out background.
    # We use 4 levels at different resolutions and smoothing factors
    # This first stage goes does to 2x downsampled
    # In the second stage, we use the brain mask to restrict the metric.
    # We only use 3 levels here and start at 4x moving to full resolution for the last level.
    # The second stage is initialized from the first stages result.
    reg_cmd = [
        "antsRegistration",
        "--dimensionality",
        "3",
        "--random-seed",
        "0",
        "--verbose",
        "1",
        "--output",
        str(temp_dir / "output"),
        "--initialize-transforms-per-stage",
        "1",
        "--write-composite-transform",
        "1",
        "--collapse-output-transforms",
        "0",
        "--initial-moving-transform",
        str(init_transform_to_use),
        "--metric",
        "Mattes[%s,%s,1.0,32,Regular,0.25]" % (fixed_to_use, parsed_args.moving_image),
        "--transform",
        "Rigid[0.1]",
        "--convergence",
        "[2000x1000x500x250,1e-6,10]",
        "--smoothing-sigmas",
        "4x3x2x1",
        "--shrink-factors",
        "16x8x4x2",
        "--masks",
        "[%s,None]" % "None" if fixed_regmask_to_use is None else fixed_regmask_to_use,
        "--metric",
        "Mattes[%s,%s,1.0,32,Regular,0.25]" % (fixed_to_use, parsed_args.moving_image),
        "--transform",
        "Rigid[0.1]",
        "--convergence",
        "[500x250x100,1e-6,10]",
        "--smoothing-sigmas",
        "2x1x0",
        "--shrink-factors",
        "4x2x1",
        "--masks",
        "[%s,None]" % fixed_brainmask_to_use,
    ]
    subprocess.run(reg_cmd, check=True, env=ants_env)

    # Because of the way the antsRegistration command must be created, we end up with a "composite" transform.
    # This only contains the rigid transform from the registration, but it is easier if we extract it ITK format.
    rigid_mat = extract_from_composite(temp_dir / "outputComposite.h5")

    # COMBINE TRANSFORMS
    # If a transform is given for the fixed image, we can combine it with the one calculated here
    # This allows an image to be registered to another image (i.e. an atlas image) through an intermediate fixed image
    if parsed_args.fixed_transform is not None:
        compose_transforms([rigid_mat, parsed_args.fixed_transform], temp_dir / "combined.mat")
        transform_to_use = temp_dir / "combined.mat"
        target_to_use = parsed_args.fixed_target
    else:
        target_to_use = parsed_args.fixed_image
        transform_to_use = rigid_mat

    # TRANSFORM
    # We use antsApplyTransforms to transform the moving image using the registration transform
    # Cubic B-Splines are used for interpolation
    transform_cmd = [
        "antsApplyTransforms",
        "--dimensionality",
        "3",
        "--input",
        parsed_args.moving_image,
        "--reference-image",
        target_to_use,
        "--output",
        str(temp_dir / "output.nii.gz"),
        "--interpolation",
        "BSpline[3]",
        "--output-data-type",
        "float",
        "--transform",
        transform_to_use,
        "--verbose",
    ]
    subprocess.run(transform_cmd, check=True, env=ants_env)

    # Clip output to input range
    clip_to_input_range(temp_dir / "output.nii.gz", parsed_args.moving_image)

    # Copy Output
    (temp_dir / "output.nii.gz").rename(output_dir / f"{moving_stem}_reg{ext}")
    transform_to_use.rename(output_dir / f"{moving_stem}_reg{transform_to_use.suffix}")

    # Delete temporary results
    shutil.rmtree(temp_dir)


if __name__ == "__main__":
    main()