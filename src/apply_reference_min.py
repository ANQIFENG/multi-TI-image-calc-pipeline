#!/usr/bin/env python

import nibabel as nib
import numpy as np


def apply_reference_min(data_path, ref_path, out_path):

    data = nib.load(data_path)
    data_np = data.get_fdata()

    ref = nib.load(ref_path)
    ref_np = ref.get_fdata()

    ref_min = ref_np.min()
    data_np[data_np < ref_min] = ref_min

    out = nib.Nifti1Image(data_np, data.affine, data.header)
    out.to_filename(out_path)
