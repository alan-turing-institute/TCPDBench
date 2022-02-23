#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Create histograms of the one-vs-rest annotator scores

Author: Gertjan van den Burg
Copyright (c) 2021 - The Alan Turing Institute
License: See LICENSE file.

"""

import argparse
import numpy as np

from typing import List

from common import Metric
from common import load_summaries
from common import compute_ovr_metric


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--summary-dir",
        help="Directory with summary files",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output-file",
        help="Output file if combined mode",
        required=True,
    )
    parser.add_argument(
        "-m",
        "--metric",
        choices=["f1", "covering"],
        help="Metric to use",
        required=True,
    )
    return parser.parse_args()


def generate_latex_doc(color: str, values: List[float]) -> List[str]:
    med = np.median(values).item()
    tex = [
        "\\documentclass[preview=true]{standalone}",
        "% The next four lines ensure reproducible builds",
        "% https://tex.stackexchange.com/q/229605",
        "\\pdfinfoomitdate=1",
        "\\pdftrailerid{}",
        "\\pdfsuppressptexinfo=1",
        "\\pdfinfo{ /Creator () /Producer () }",
        "\\usepackage{pgfplots, pgfplotstable}",
        "\\usepgfplotslibrary{statistics}",
        "\\pgfplotsset{compat=1.16}",
        "\\definecolor{Color}{HTML}{%s}" % color,
        "\\begin{document}",
        "\\begin{tikzpicture}",
        "\\tikzstyle{every node}=[font=\\scriptsize]",
        "\\begin{axis}[",
        "    ybar,",
        "    ymin=0,",
        "    legend pos={north west},",
        "    legend cell align={left},",
        "    xtick pos=left,",
        "    ytick pos=left,",
        "    width=200,",
        "    height=120",
        "]",
        "\\addplot +[",
        "    Color,",
        "    fill=Color!50!white,",
        "    opacity=0.5,",
        "    hist={",
        "        bins=20,",
        "        data min=0,",
        "        data max=1",
        "    }",
        "    ] table [y index=0] {",
    ]
    for v in values:
        tex.append(repr(v))

    tex.extend(
        [
            "};"
            "\\draw[dashed, Color] ({axis cs:%f,0}|-{rel axis cs:0,0}) -- ({axis cs:%f,0}|-{rel axis cs:0,1});"
            % (med, med),
            "\\end{axis}",
            "\\end{tikzpicture}",
            "\\end{document}",
        ]
    )
    return tex


def main():
    args = parse_args()
    summaries = load_summaries(args.summary_dir)

    if args.metric == "f1":
        metric = Metric.f1
        color = "b40204"
    else:
        metric = Metric.cover
        color = "00aaba"

    all_ovr_scores = []
    for dataset in summaries:
        summary = summaries[dataset]
        annotations = summary["annotations"]
        n_obs = summary["dataset_nobs"]

        n_ann = len(annotations)
        assert n_ann == 5  # just a sanity check for us

        ann_ovr = compute_ovr_metric(annotations, n_obs, metric=metric)
        all_ovr_scores.extend(list(ann_ovr.values()))

    tex = generate_latex_doc(color, all_ovr_scores)
    with open(args.output_file, "w") as fp:
        fp.write("\n".join(tex))


if __name__ == "__main__":
    main()
