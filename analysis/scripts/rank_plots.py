#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Create rank plots from table json files.

Author: Gertjan van den Burg
Copyright (c) 2020 - The Alan Turing Institute
License: See the LICENSE file.

"""

import argparse

from typing import Dict

from labella.timeline import TimelineTex
from labella.scale import LinearScale

from common import Dataset
from common import Dimensionality
from common import Experiment
from common import Method
from common import MissingStrategy
from common import filter_scores
from common import load_score_file
from rank_common import compute_ranks
from significance import reference_difference


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        help="Score file with scores for each method and dataset",
        required=True,
    )
    parser.add_argument(
        "-o", "--output", help="Output tex file to write to", required=True
    )
    parser.add_argument(
        "-d",
        "--dim",
        help="Dimensionality to consider",
        choices=["univariate", "multivariate"],
        required=True,
    )
    parser.add_argument(
        "-e",
        "--experiment",
        help="Experiment to consider for rank plots",
        choices=["default", "oracle"],
        required=True,
    )
    parser.add_argument(
        "-m",
        "--missing",
        help=(
            "How to handle failures (do 'complete' case analysis or "
            "give score of 'zero')"
        ),
        choices=[ms.name for ms in MissingStrategy],
        required=True,
    )
    return parser.parse_args()


def method_name(m: Method):
    return "\\textsc{%s}" % m.name


def make_rank_plot(
    filtered_scores: Dict[Dataset, Dict[Method, float]],
    output_file,
    higher_better=True,
    return_ranks=False,
):
    avg_ranks, all_ranks = compute_ranks(
        filtered_scores, higher_better=higher_better
    )

    plot_data = [
        {"time": rank, "text": method_name(method)}
        for method, rank in avg_ranks.items()
    ]

    color = "#000"

    options = {
        "scale": LinearScale(),
        "direction": "up",
        "domain": [1, len(avg_ranks)],
        "layerGap": 20,
        "borderColor": "#000",
        "showBorder": False,
        "labelBgColor": "#fff",
        "linkColor": color,
        "labelTextColor": color,
        "dotColor": color,
        "initialWidth": 600,
        "initialHeight": 75,
        "latex": {"linkThickness": "thin", "reproducible": True},
        "dotRadius": 2,
        "margin": {"left": 0, "bottom": 0, "right": 0, "top": 0},
    }

    tl = TimelineTex(plot_data, options=options)
    texlines = tl.export()

    n_datasets = len(all_ranks)
    ref_method, _, CD = reference_difference(avg_ranks, n_datasets)

    # we're going to insert the critical difference line after the dots
    # scope,·so we first have to figure out where that is.
    lines = texlines.split("\n")
    idx = None
    find_scope = False
    for i, line in enumerate(lines):
        if line.strip() == "% dots":
            find_scope = True
        if find_scope and "\\end{scope}" in line:
            idx = i + 1
            break

    before = lines[:idx]
    after = lines[idx:]

    nodes, _ = tl.compute()
    bestnode = next(
        (n for n in nodes if n.data.text == method_name(ref_method)), None
    )
    # idealPos is the position on the axis
    posBest = bestnode.getRoot().idealPos
    posCD = tl.options["scale"](bestnode.data.time + CD)

    CDlines = [
        "% Critical difference",
        "\\def\\posBest{%.16f}" % posBest,
        "\\def\\posCD{%.16f}" % posCD,
        "\\begin{scope}",
        "\\draw (\\posBest, 30) -- (\\posBest, 20);",
        "\\draw (\\posBest, 25) --node[below] {CD} (\\posCD, 25);",
        "\\draw (\\posCD, 30) -- (\\posCD, 20);",
        "\\end{scope}",
    ]

    all_lines = before + [""] + CDlines + after

    with open(output_file, "w") as fp:
        fp.write("\n".join(all_lines))


def main():
    args = parse_args()

    scores = load_score_file(args.input)
    experiment = Experiment[args.experiment]
    dimensionality = Dimensionality[args.dim]
    missing_strategy = MissingStrategy[args.missing]
    filtered_scores = filter_scores(
        scores, experiment, dimensionality, missing_strategy=missing_strategy
    )

    make_rank_plot(filtered_scores, args.output, higher_better=True)


if __name__ == "__main__":
    main()
