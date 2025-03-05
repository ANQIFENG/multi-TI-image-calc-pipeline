#!/usr#!/usr/bin/env python
import numpy as np
import nibabel as nib
from skimage.filters import threshold_otsu
from scipy.optimize import curve_fit
from functools import partial
from multiprocessing import Pool
# import warnings
# warnings.filterwarnings("ignore")


def zinf(vals):
    vals[~ np.isfinite(vals)] = 0
    return vals


def fit_func(ti, pd, t1, tr, use_abs=False):
    im = pd * (1 - 2 * np.exp(-ti / t1) + np.exp(-tr / t1))
    im = np.abs(im) if use_abs else im
    return zinf(im)


def solve_func(val, func, ti, inital_guess=[1000, 1000]):
    popt, _ = curve_fit(func, ti, val, p0=inital_guess)
    return popt


def calculate_pd_t1_map(mprage_path, fgatir_path, mask_path,
                     ti_mprage, ti_fgatir, tr,
                     mprage_isflip, fgatir_isflip,
                     pd_out_path, t1_out_path,
                     num_workers):
    # load data
    mprage = nib.load(mprage_path).get_fdata().astype(np.float32)
    fgatir = nib.load(fgatir_path).get_fdata().astype(np.float32)
    mask = nib.load(mask_path).get_fdata().astype(np.float32) if mask_path else None

    # combine mprage and fgatir
    images = np.stack([mprage * mprage_isflip, fgatir * fgatir_isflip], axis=-1)

    # define TIs
    tis = [ti_mprage, ti_fgatir]

    orig_shape = images.shape[:-1]
    new_shape = [int(np.prod(images.shape[:-1])), images.shape[-1]]
    images = np.reshape(images, new_shape)

    if mask is None:
        sum_images = np.sum(np.abs(images), axis=-1)
        threshold = threshold_otsu(sum_images)
        mask = sum_images > threshold
    else:
        mask = mask > 0.5
    mask = mask.flatten()

    pd = np.zeros(len(images))
    t1 = np.zeros(len(images))

    func = partial(fit_func, tr=tr, use_abs=False)
    wrap_func = partial(solve_func, func=func, ti=tis)

    with Pool(num_workers) as p:
        popt = np.array(p.map(wrap_func, images[mask]))

    pd[mask], t1[mask] = popt[:, 0], popt[:, 1]
    pd[pd < 0] = 0
    t1[t1 < 0] = 0
    pd = np.reshape(pd, orig_shape)
    t1 = np.reshape(t1, orig_shape)

    affine = nib.load(mprage_path).affine
    header = nib.load(mprage_path).header

    nib.Nifti1Image(pd, affine, header).to_filename(pd_out_path)
    nib.Nifti1Image(t1, affine, header).to_filename(t1_out_path)
