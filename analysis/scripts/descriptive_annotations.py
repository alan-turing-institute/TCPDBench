# -*- coding: utf-8 -*-

"""Extract descriptive statistics for the time series

This script is used to extract descriptive statistics about the number of 
annotations from the summary files.

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
        choices=["min", "max", "mean", "std"],
        required=True,
    )
    return parser.parse_args()


def load_unique_annotations(summary_dir):
    files = os.listdir(summary_dir)
    assert len(files) == N_DATASETS

    n_uniq_anno = []
    for f in sorted(files):
        path = os.path.join(summary_dir, f)
        with open(path, "r") as fp:
            data = json.load(fp)

        all_anno = set()
        for annotations in data["annotations"].values():
            for cp in annotations:
                all_anno.add(cp)
        n_uniq_anno.append(len(all_anno))
    return n_uniq_anno


def main():
    args = parse_args()
    if args.type == "max":
        func = max
    elif args.type == "mean":
        func = statistics.mean
    elif args.type == "std":
        func = statistics.stdev
    elif args.type == "min":
        func = min
    else:
        raise ValueError("Unknown type")

    n_uniq_anno = load_unique_annotations(args.summary_dir)
    if args.type in ["min", "max"]:
        print("%i%%" % func(n_uniq_anno))
    else:
        print("%.1f%%" % func(n_uniq_anno))


if __name__ == "__main__":
    main()
