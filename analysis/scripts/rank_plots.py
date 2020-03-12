#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Create rank plots from best table json files.

Author: Gertjan van den Burg
Copyright (c) 2020 - The Alan Turing Institute
License: See the LICENSE file.

"""

import argparse

from labella.timeline import TimelineTex
from labella.scale import LinearScale

from rank_common import load_data, compute_ranks, preprocess_data
from significance import reference_difference


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-i",
        "--input",
        help="Input JSON file with results for each method",
        required=True,
    )
    parser.add_argument(
        "-o", "--output", help="Output tex file to write to", required=True
    )
    parser.add_argument(
        "-b",
        "--better",
        help="Whether higher or lower is better",
        choices=["min", "max"],
        default="max",
    )
    parser.add_argument(
        "--type",
        help="Type of table to make",
        choices=["best", "default"],
        required=True,
    )
    return parser.parse_args()


def method_name(m):
    m = m.split("_")[-1]
    return "\\textsc{%s}" % m


def make_rank_plot(
    results,
    output_file,
    keep_methods=None,
    higher_better=True,
    return_ranks=False,
):
    methods = keep_methods[:]
    avg_ranks, all_ranks = compute_ranks(
        results, keep_methods=keep_methods, higher_better=higher_better
    )
    plot_data = [
        {"time": rank, "text": method_name(method)}
        for method, rank in avg_ranks.items()
    ]

    color = "#000"

    options = {
        "scale": LinearScale(),
        "direction": "up",
        "domain": [1, len(methods)],
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

    ref_method, CD, _ = reference_difference(avg_ranks, n_datasets)

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

    higher_better = args.better == "max"

    data = load_data(args.input)
    clean, methods = preprocess_data(data, args.type)

    make_rank_plot(
        clean, args.output, keep_methods=methods, higher_better=higher_better
    )


if __name__ == "__main__":
    main()
