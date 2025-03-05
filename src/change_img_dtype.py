#!/usr/bin/env python

import nibabel as nib
import numpy as np


def change_image_dtype(data_path, out_path):
    data = nib.load(data_path)
    data.header.set_data_dtype(np.float32)
    nib.save(data, out_path)
