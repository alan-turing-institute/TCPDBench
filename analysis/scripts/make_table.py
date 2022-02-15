#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to generate large tables from summary files

Metrics, experiments, methods, and datasets are hard-coded as a means of 
validation.

Author: G.J.J. van den Burg
Copyright (c) 2020 - The Alan Turing Institute
License: See the LICENSE file.

"""

import argparse
import json

from typing import List

from common import Dataset
from common import Experiment
from common import UNIDATASETS
from common import QC_DATASETS
from common import MULTIDATASETS
from common import Method
from common import Metric
from common import Result
from latex import build_latex_table
from score_file import collect_results


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--summary-dir",
        help="Directory with summary files",
        required=True,
    )
    parser.add_argument(
        "-m",
        "--metric",
        help="Metric to use for the table",
        choices=["f1", "cover"],
        required=True,
    )
    parser.add_argument(
        "-e",
        "--experiment",
        help="Experiment to make table for",
        choices=["default", "oracle"],
        required=True,
    )
    return parser.parse_args()


def load_summary(filename):
    with open(filename, "r") as fp:
        data = json.load(fp)
    return data


def write_latex(results: List[Result]):
    methods = sorted(set(r.method.name for r in results))
    datasets = sorted(set(r.dataset.name for r in results))

    qc_datasets = [d.name for d in list(QC_DATASETS)]
    multi_datasets = [d.name for d in MULTIDATASETS]
    uni_datasets = [d.name for d in UNIDATASETS if not d in QC_DATASETS]
    datasets = (
        sorted(uni_datasets) + sorted(qc_datasets) + sorted(multi_datasets)
    )
    first_qc = sorted(qc_datasets)[0]
    first_multi = sorted(multi_datasets)[0]

    textsc = lambda m: "\\textsc{%s}" % m
    verb = lambda m: "\\verb+%s+" % m

    headers = ["Dataset"] + list(map(textsc, methods))

    table = []
    for dataset in datasets:
        row = [verb(dataset)]
        d = Dataset(dataset)

        for method in methods:
            m = Method(method)
            r = next((r for r in results if r.method == m and r.dataset == d))
            row.append(r.placeholder if r.score is None else r.score)

        table.append(row)
    spec = "l" + "c" * len(methods)
    tex = build_latex_table(
        table, headers, floatfmt=".3f", table_spec=spec, booktabs=True
    )

    # add a horizontal line between different dataset types
    lines = tex.split("\n")
    newlines = []
    for line in lines:
        if line.startswith(verb(first_qc)):
            newlines.append("\\midrule")
        elif line.startswith(verb(first_multi)):
            newlines.append("\\midrule")
        newlines.append(line)
    tex = "\n".join(newlines)
    print(tex)


def main():
    args = parse_args()
    metric = Metric[args.metric]
    experiment = Experiment[args.experiment]

    # We work with the raw summary files here because we need the placeholder
    # in the LaTeX tables.
    results = collect_results(
        summary_dir=args.summary_dir,
        metric=metric,
        experiment=experiment,
    )
    write_latex(results)


if __name__ == "__main__":
    main()
