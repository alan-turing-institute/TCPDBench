# -*- coding: utf-8 -*-

"""Extract descriptive statistics for the time series

This script is used to extract descriptive statistics regarding features of the 
time series from the summary files.

Author: Gertjan van den Burg
Copyright (c) 2020 - The Alan Turing Institute
License: See the LICENSE file.

"""


import argparse
import json
import os
import statistics

N_DATASETS = 42


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--summary-dir",
        help="Directory with summary files",
        required=True,
    )
    parser.add_argument(
        "-t",
        "--type",
        help="Type of statistic to compute",
        choices=["min", "max", "mean"],
        required=True,
    )
    return parser.parse_args()


def load_summary_nobs(summary_dir):
    files = os.listdir(summary_dir)
    assert len(files) == N_DATASETS

    all_nobs = []
    for f in sorted(files):
        path = os.path.join(summary_dir, f)
        with open(path, "r") as fp:
            data = json.load(fp)
        all_nobs.append(data["dataset_nobs"])
    return all_nobs


def main():
    args = parse_args()
    if args.type == "min":
        func = min
    elif args.type == "mean":
        func = statistics.mean
    elif args.type == "max":
        func = max
    else:
        raise ValueError("Unknown type")

    all_nobs = load_summary_nobs(args.summary_dir)
    if args.type in ["min", "max"]:
        print("%i%%" % func(all_nobs))
    else:
        print("%.1f%%" % func(all_nobs))


if __name__ == "__main__":
    main()
