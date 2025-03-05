#!/usr/bin/env python

import subprocess


def run_fcm_normalize(data_path, brain_mask_path, out_path):
    command = [
        'fcm-normalize', data_path,
        '-m', brain_mask_path,
        '-o', out_path,
        '-v', '-mo', 't1', '-tt', 'wm'
    ]
    subprocess.run(command, check=True)