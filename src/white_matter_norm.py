#!/usr/bin/env python

import nibabel as nib
import numpy as np


def wm_norm(mprage_path,
            fgatir_path,
            wm_membership_path,
            mprage_out_path,
            fgatir_out_path,
            wm_mask_out_path,
            VALUE=1000,
            THRESHOLD=0.40):

    # load MPRAGE and FGATIR
    mprage = nib.load(mprage_path)
    fgatir = nib.load(fgatir_path)
    mprage_np = mprage.get_fdata().astype(np.float32)
    fgatir_np = fgatir.get_fdata().astype(np.float32)

    # generate wm mask
    wm_membership = nib.load(wm_membership_path).get_fdata().astype(np.float32)
    wm_mask = wm_membership > THRESHOLD

    # calculate the mean value according to the white matter mask on MPRAGE
    mean_val = mprage_np[wm_mask].mean()

    # normalize MPRAGE and FGATIR using the same scaling factor
    mprage_np = (mprage_np / mean_val) * VALUE
    fgatir_np = (fgatir_np / mean_val) * VALUE

    # save output
    mprage_out = nib.Nifti1Image(mprage_np, mprage.affine, mprage.header)
    fgatir_out = nib.Nifti1Image(fgatir_np, fgatir.affine, fgatir.header)
    wm_mask_out = nib.Nifti1Image(wm_mask, mprage.affine, mprage.header)

    mprage_out.to_filename(mprage_out_path)
    fgatir_out.to_filename(fgatir_out_path)
    wm_mask_out.to_filename(wm_mask_out_path)

    print("Saving done. Mean value is: ", mean_val)




