#!/usr/bin/env python
import logging
import nibabel as nib
import numpy as np
from radifox.utils.resize.scipy import resize
from scipy.ndimage import (
    binary_closing,
    binary_opening,
    binary_fill_holes,
    generate_binary_structure,
    iterate_structure,
    binary_dilation,
    median_filter,
)
from skimage.measure import label
from sklearn.cluster import KMeans


def fill_2p5d(img):
    for slice_num in range(img.shape[0]):
        img[slice_num, :, :] = binary_fill_holes(img[slice_num, :, :])
    for slice_num in range(img.shape[1]):
        img[:, slice_num, :] = binary_fill_holes(img[:, slice_num, :])
    for slice_num in range(img.shape[2]):
        img[:, :, slice_num] = binary_fill_holes(img[:, :, slice_num])
    return img


def create_bg_mask(data_path, out_path):
    logging.info(f"Loading image: {data_path}")
    obj = nib.load(data_path)

    logging.info("Resizing image...")
    img_data = resize(
        obj.get_fdata().astype(np.float32),
        [1 / item for item in obj.header.get_zooms()],
        order=1,
    )

    logging.info("Filtering image...")
    img_data = median_filter(img_data, 5)

    logging.info("Fitting KMeans...")
    km = KMeans(4, n_init=10, random_state=0)
    rand_mask = np.random.rand(*img_data.shape) < 0.25
    km.fit(np.expand_dims(img_data[rand_mask], 1))

    logging.info("Generating Mask...")
    classes = km.predict(np.expand_dims(img_data.flatten(), 1)).reshape(img_data.shape)
    means = [np.mean(img_data[classes == i]) for i in range(4)]
    mask = (classes == np.argmin(means)) == 0.0
    # noinspection PyTypeChecker
    mask = fill_2p5d(mask)
    dist2_5by5_kernel = iterate_structure(generate_binary_structure(3, 3), 2)
    mask = np.pad(mask, 25, mode="constant", constant_values=0.0)
    mask = binary_closing(mask, dist2_5by5_kernel, 5)
    mask = fill_2p5d(mask).astype(np.float32)
    mask = binary_opening(mask, dist2_5by5_kernel, 3)
    mask = mask[25:-25, 25:-25, 25:-25]
    labels = label(mask)
    label_counts = np.bincount(labels.ravel())
    mask = labels == (np.argmax(label_counts[1:]) + 1)
    mask = binary_dilation(mask, dist2_5by5_kernel, 2)
    mask = fill_2p5d(mask).astype(np.float32)

    logging.info("Resizing mask...")
    mask = resize(mask, obj.header.get_zooms(), order=0, target_shape=obj.shape)

    logging.info("Cleaning mask...")
    mask = np.pad(mask, 5, mode="constant", constant_values=0.0)
    mask = median_filter(mask, 5)
    mask = mask[5:-5, 5:-5, 5:-5]
    mask = binary_dilation(mask, generate_binary_structure(3, 3), 1)

    logging.info("Saving background mask...")
    nib.Nifti1Image(mask, None, obj.header).to_filename(out_path)
