#!/usr/bin/env python
import nibabel as nib
import numpy as np
import os


def zinf(vals):
    vals[~ np.isfinite(vals)] = 0
    return vals


def func(ti, pd, t1, tr):
    im = pd * (1 - 2 * np.exp(-ti / t1) + np.exp(-tr / t1))
    return zinf(np.abs(im))


def synthesize_t1_image(t1map_path, pdmap_path, ti, tr, out_path):

    t1map = nib.load(t1map_path)
    t1map_np = t1map.get_fdata()
    pdmap = nib.load(pdmap_path)
    pdmap_np = pdmap.get_fdata()

    mask = np.logical_and(t1map_np > 0, pdmap_np > 0)

    affine = t1map.affine
    header = t1map.header
    shape = t1map.shape

    pdmap_np = pdmap_np[mask]
    t1map_np = t1map_np[mask]
    image = func(ti, pdmap_np, t1map_np, tr)

    result = np.zeros(shape)
    result[mask] = image

    out = nib.Nifti1Image(result, affine, header)
    out.to_filename(out_path)


def synthesize_multi_ti_images(ti_min, ti_max, step, tr, t1map_path, pdmap_path, out_dir):
    ti_values = np.arange(ti_min, ti_max + step, step)

    for ti in ti_values:
        print('Calculating Image for TI value %f' % ti)
        synT1_out_fp = os.path.join(out_dir, "synT1_" + str(ti) + ".nii.gz")
        synthesize_t1_image(t1map_path, pdmap_path, ti, tr, synT1_out_fp)

