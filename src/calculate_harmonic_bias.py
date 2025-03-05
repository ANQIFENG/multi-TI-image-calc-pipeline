#!/usr/bin/env python

import numpy as np
import nibabel as nib


def calculate_harmonic_bias(mprage_path,
                            fgatir_path,
                            mprage_bias_path,
                            fgatir_bias_path,
                            harmonic_bias_out_path,
                            mprage_out_path,
                            fgatir_out_path):

    # load MPRAGE bias field
    mprage_bias_nib = nib.load(mprage_bias_path)
    mprage_bias_affine = mprage_bias_nib.affine
    mprage_bias_header = mprage_bias_nib.header
    mprage_bias = mprage_bias_nib.get_fdata().astype(np.float32)

    # load FGATIR bias field
    fgatir_bias_nib = nib.load(fgatir_bias_path)
    fgatir_bias = fgatir_bias_nib.get_fdata().astype(np.float32)

    # calculate harmonic/geometric mean bias
    bias = np.sqrt(mprage_bias * fgatir_bias)
    assert bias.min() > 0

    # save harmonic bias
    bias_out = nib.Nifti1Image(bias, mprage_bias_affine, mprage_bias_header)
    bias_out.to_filename(harmonic_bias_out_path)

    # divide MPRAGE by harmonic bias
    mprage_nib = nib.load(mprage_path)
    mprage = mprage_nib.get_fdata().astype(np.float32)
    mprage = mprage / bias

    # save MPRAGE
    mprage_out = nib.Nifti1Image(mprage, mprage_nib.affine, mprage_nib.header)
    mprage_out.to_filename(mprage_out_path)

    # divide FGATIR by harmonic bias
    fgatir_nib = nib.load(fgatir_path)
    fgatir = fgatir_nib.get_fdata().astype(np.float32)
    fgatir = fgatir / bias

    # save FGATIR
    fgatir_out = nib.Nifti1Image(fgatir, fgatir_nib.affine, fgatir_nib.header)
    fgatir_out.to_filename(fgatir_out_path)

