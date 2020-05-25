#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A method that always returns no change points

Author: G.J.J. van den Burg
Date: 2020-05-07
License: MIT
Copyright: 2020, The Alan Turing Institute

"""

import argparse
import time

from cpdbench_utils import load_dataset, exit_success


def parse_args():
    parser = argparse.ArgumentParser(description="Wrapper for None-detector")
    parser.add_argument(
        "-i", "--input", help="path to the input data file", required=True
    )
    parser.add_argument("-o", "--output", help="path to the output file")
    return parser.parse_args()


def main():
    args = parse_args()

    data, mat = load_dataset(args.input)

    start_time = time.time()

    locations = []

    stop_time = time.time()
    runtime = stop_time - start_time

    exit_success(data, args, {}, locations, runtime, __file__)


if __name__ == "__main__":
    main()
