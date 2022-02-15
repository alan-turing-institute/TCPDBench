#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Generate the table of descriptive statistics

1. Name of the dataset
2. Dimensionality
3. Length
4. Recording frequency (hourly, monthly, etc)
5. Number of change points (min/max/avg?)

Author: Gertjan van den Burg
Copyright (c) 2021 - The Alan Turing Institute
License: See the LICENSE file.

"""

import argparse
import json
import os

from typing import Any
from typing import Dict
from typing import List

from common import Dataset
from common import load_summaries
from frequencies import FREQUENCIES

PREAMBLE = [
    "\\documentclass[11pt, preview=true]{standalone}",
    "\\pdfinfoomitdate=1",
    "\\pdftrailerid{}",
    "\\pdfsuppressptexinfo=1",
    "\\pdfinfo{ /Creator () /Producer () }",
    "\\usepackage{booktabs}",
    "\\usepackage{multirow}",
    "\\usepackage{amsmath}",
    "\\begin{document}",
]
EPILOGUE = ["\\end{document}"]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-d", "--dataset-dir", help="Directory with datasets", required=True
    )
    parser.add_argument(
        "-s",
        "--summary-dir",
        help="Directory with summary files",
        required=True,
    )
    parser.add_argument(
        "-a",
        "--standalone",
        help="Create a standalone LaTeX file",
        action="store_true",
    )
    parser.add_argument("-o", "--output", help="Output LaTeX file to save to")
    return parser.parse_args()


def load_datasets(dataset_dir: str) -> Dict[Dataset, Dict[str, Any]]:
    datasets = {}
    files = os.listdir(dataset_dir)
    assert len(files) == len(Dataset)

    for f in sorted(files):
        path = os.path.join(dataset_dir, f)
        with open(path, "r") as fp:
            dataset_data = json.load(fp)
        dataset = Dataset[dataset_data["name"]]
        datasets[dataset] = dataset_data

    return datasets


def make_table(
    datasets: Dict[Dataset, Dict[str, Any]],
    summaries: Dict[Dataset, Dict[str, Any]],
) -> List[str]:

    tex = []
    tex.append("%% This table requires booktabs!")
    tex.append("\\begin{tabular}{llrrrrr}")

    header = [
        "",
        "Frequency",
        "Length ($T$)",
        "Dim. ($d$)",
        "Min CP",
        "Max CP",
        "Avg CP",
    ]
    tex.append(" & ".join(header) + "\\\\")
    tex.append("\\toprule")

    min_cp = lambda ann: min(map(len, ann.values()))
    max_cp = lambda ann: max(map(len, ann.values()))
    avg_cp = lambda ann: sum(map(len, ann.values())) / len(ann)
    verb = lambda m: "\\verb+%s+" % m

    table = []
    for i, d in enumerate(datasets):
        data = datasets[d]
        summary = summaries[d]
        row = [
            verb((" " if i < 9 else "") + f"{i+1}. " + d.name),
            FREQUENCIES[d],
            str(data["n_obs"]),
            str(data["n_dim"]),
            str(min_cp(summary["annotations"])),
            str(max_cp(summary["annotations"])),
            str(avg_cp(summary["annotations"])),
        ]
        table.append(row)

    for row in table:
        tex.append(" & ".join(row) + " \\\\")
    tex.append("\\bottomrule")
    tex.append("\\end{tabular}")
    return tex


def main():
    args = parse_args()
    datasets = load_datasets(args.dataset_dir)
    summaries = load_summaries(args.summary_dir)

    tex = make_table(datasets, summaries)
    tex = PREAMBLE + tex + EPILOGUE if args.standalone else tex

    if args.output:
        with open(args.output, "w") as fp:
            fp.write("\n".join(tex))
    else:
        print("\n".join(tex))


if __name__ == "__main__":
    main()
