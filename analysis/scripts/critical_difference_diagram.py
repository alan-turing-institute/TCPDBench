#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Critical Difference Diagrams

Adapted from: https://github.com/mirkobunse/CriticalDifferenceDiagrams.jl

Author: Gertjan van den Burg
Copyright (c) 2021 - The Alan Turing Institute
License: See the LICENSE file.

"""

import argparse
import os

from collections import defaultdict

from typing import Dict
from typing import List

import networkx as nx

from common import Dataset
from common import Dimensionality
from common import Experiment
from common import MissingStrategy
from common import Method
from common import filter_scores
from common import load_score_file

from latex import build_latex_doc

from rank_common import compute_ranks

from significance import pairwise_difference_nemenyi
from significance import pairwise_difference_wilcoxon_holm


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
        "-t",
        "--test",
        help="Test to perform (Nemenyi vs. Wilcoxon-Holm)",
        choices=["nemenyi", "wilcoxon"],
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


def method_name(m: Method) -> str:
    return "\\textsc{%s}" % m.name


def dict2tex(d: Dict) -> str:
    items = []
    for key, value in d.items():
        if isinstance(value, dict):
            value = "{\n" + dict2tex(value) + "}"
        if value is None:
            items.append(f"{key}")
        else:
            items.append(f"{key}={value}")
    return ",%\n".join(items)


def generate_tex(
    avg_ranks: Dict[Method, float], method_cliques: List[List[Method]]
):
    k = len(avg_ranks)

    tex = []
    tex.append("\\documentclass[10pt]{standalone}")
    tex.append("\\pdfinfoomitdate=1")
    tex.append("\\pdftrailerid{}")
    tex.append("\\pdfsuppressptexinfo=1")
    tex.append("\\pdfinfo{ /Creator () /Producer () }")
    tex.append("\\usepackage{pgfplots}")
    tex.append("\\pgfplotsset{compat=newest}")
    tex.append("\\begin{document}")
    tex.append("\\begin{tikzpicture}")

    plot_height = (len(avg_ranks) + 1) // 2 + 2
    axis_opts = {
        "axis x line": "center",
        "axis y line": "none",
        "xmin": 1,
        "xmax": k,
        "ymin": -plot_height + 0.5,
        "ymax": 0,
        "clip": "false",
        "scale only axis": None,
        "height": "3cm",
        "width": "6cm",
        "ticklabel style": {
            "anchor": "south",
            "yshift": "1.33*\pgfkeysvalueof{/pgfplots/major tick length}",
            "font": "\\footnotesize",
        },
        "every tick/.style": {
            "yshift": ".5*\pgfkeysvalueof{/pgfplots/major tick length}",
        },
        "xtick": f"{{1,...,{k}}}",
        "axis line style": "{-}",
        "title style": {"yshift": "\\baselineskip"},
    }

    tex.append(f"\\begin{{axis}}[{dict2tex(axis_opts)}]")
    tex.append("")

    for i, method in enumerate(sorted(avg_ranks, key=avg_ranks.get)):
        r = avg_ranks[method]
        # direction = "west" if r < k // 2 else "east"
        direction = "west" if i < k // 2 else "east"
        anchor = "east" if direction == "west" else "west"

        edge_x = 1 if direction == "west" else k
        edge_y = (-(i + 1) - 0.5) if direction == "west" else -(k - i) - 0.5

        draw = [
            "\\draw[semithick, rounded corners=1pt]",
            f"(axis cs:{r}, 0) |- (axis cs: {edge_x}, {edge_y})",
            f"node[font=\\footnotesize, fill=white, inner xsep=1pt, outer xsep=0pt, anchor={anchor}]",
            f"{{\\textsc{{{method.name}}}}};",
        ]
        tex.extend(draw)
        tex.append("")

    sorted_cliques = sorted(
        method_cliques, key=lambda c: min(avg_ranks[m] for m in c)
    )

    clique_stack = defaultdict(list)
    for c in sorted_cliques:
        mi, ma = min(avg_ranks[m] for m in c), max(avg_ranks[m] for m in c)
        if not clique_stack:
            clique_stack[0].append((mi, ma, c))
            continue

        included = False
        for lvl in clique_stack:
            overlap = False
            for omin, omax, _ in clique_stack[lvl]:
                # check if we have overlap with slack
                if not (ma < omin - 0.5 or mi > omax + 0.5):
                    overlap = True

            if not overlap:
                clique_stack[lvl].append((mi, ma, c))
                included = True
                break

        if not included:
            clique_stack[lvl + 1].append((mi, ma, c))

    for lvl in clique_stack:
        for _, _, c in clique_stack[lvl]:
            minrank = min([avg_ranks[m] for m in c])
            maxrank = max([avg_ranks[m] for m in c])
            ypos = -1.5 * (lvl + 1) / (len(clique_stack.keys()) + 1)

            draw = [
                "\\draw[ultra thick, line cap=round]",
                f"(axis cs:{minrank}, {ypos}) -- (axis cs:{maxrank}, {ypos});",
            ]
            tex.extend(draw)
            tex.append("")

    tex.append("\\end{axis}")
    tex.append("\\end{tikzpicture}")
    tex.append("\\end{document}")
    return tex


def make_cd_diagram_tex(
    filtered_scores: Dict[Dataset, Dict[Method, float]], test: str
) -> None:
    assert test in ["nemenyi", "wilcoxon"]

    n_datasets = len(filtered_scores)
    avg_ranks, all_ranks = compute_ranks(filtered_scores, higher_better=True)
    n_methods = len(avg_ranks)

    if test == "nemenyi":
        sigdiff, _ = pairwise_difference_nemenyi(
            avg_ranks, n_datasets, alpha=0.05
        )
    else:
        sigdiff = pairwise_difference_wilcoxon_holm(
            filtered_scores, alpha=0.05
        )

    sorted_methods = sorted(avg_ranks.keys(), key=lambda m: m.name)

    G = nx.Graph()
    G.add_nodes_from(list(range(n_methods)))

    # Add edges for all methods that are not significantly different from each
    # other
    for method in sigdiff:
        midx = sorted_methods.index(method)
        for other in sigdiff[method]:
            oidx = sorted_methods.index(other)
            if not sigdiff[method][other]:
                G.add_edge(midx, oidx)

    cliques = list(nx.algorithms.clique.find_cliques(G))
    method_cliques = [[sorted_methods[i] for i in c] for c in cliques]

    # Check if any cliques are contained in another clique
    minranks = [min([avg_ranks[m] for m in c]) for c in method_cliques]
    maxranks = [max([avg_ranks[m] for m in c]) for c in method_cliques]

    drop = set()
    for i in range(len(cliques)):
        if minranks[i] == maxranks[i]:
            drop.add(i)
        for j in range(len(cliques)):
            if i == j:
                continue
            if minranks[i] <= minranks[j] and maxranks[i] >= maxranks[j]:
                drop.add(j)

    cliques = [cliques[i] for i in range(len(cliques)) if not i in drop]
    method_cliques = [
        method_cliques[i] for i in range(len(method_cliques)) if not i in drop
    ]

    tex = generate_tex(avg_ranks, method_cliques)
    return tex


def main():
    args = parse_args()

    scores = load_score_file(args.input)
    experiment = Experiment[args.experiment]
    dimensionality = Dimensionality[args.dim]
    missing_strategy = MissingStrategy[args.missing]
    filtered_scores = filter_scores(
        scores, experiment, dimensionality, missing_strategy=missing_strategy
    )

    texlines = make_cd_diagram_tex(filtered_scores, test=args.test)
    tex = "\n".join(texlines)

    with open(args.output, "w") as fp:
        fp.write(tex)

    pdf_name = os.path.splitext(args.output)[0] + ".pdf"
    build_latex_doc(tex, output_name=pdf_name)


if __name__ == "__main__":
    main()
