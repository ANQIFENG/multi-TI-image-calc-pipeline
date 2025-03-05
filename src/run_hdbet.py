#!/usr/bin/env python

from HD_BET.run import run_hd_bet


def run_hdbet(data_path: str, out_path: str):

    run_hd_bet(
        data_path,
        out_path,
        postprocess=True,
        keep_mask=True,
        bet=True,
        )