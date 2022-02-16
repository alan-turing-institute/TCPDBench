#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Code to compute significant differences

Author: Gertjan van den Burg
Copyright (c) 2020 - The Alan Turing Institute
License: See the LICENSE file.

"""

import argparse
import numpy as np
import os
import scipy.stats as stats
import subprocess
import tempfile

from collections import defaultdict

from typing import Any
from typing import Dict
from typing import Tuple

from statsmodels.stats.libqsturng import qsturng
from statsmodels.stats.multitest import multipletests
from tabulate import tabulate

from common import Dataset
from common import Dimensionality
from common import Experiment
from common import Method
from common import MissingStrategy
from common import filter_scores
from common import load_score_file
from rank_common import compute_ranks


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", help="Output basename")
    parser.add_argument(
        "-i", "--input", help="Score file with scores for each dataset/method"
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["global", "pairwise", "reference"],
        help=(
            "Whether to do a global difference F test, a pairwise (Nemenyi) "
            "test or a reference test to the best performing method"
        ),
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
        "--missing",
        help=(
            "How to handle failures (do 'complete' case analysis or "
            "give score of 'zero')"
        ),
        choices=[ms.name for ms in MissingStrategy],
        required=True,
    )
    return parser.parse_args()


def global_difference(avg_ranks, n_datasets):
    N = n_datasets
    k = len(avg_ranks)
    avg_sq_sum = sum(r * r for r in avg_ranks.values())

    chi2 = 12 * N / (k * (k + 1)) * (avg_sq_sum - (k * (k + 1) * (k + 1) / 4))
    chiprob = 1.0 - stats.chi2.cdf(chi2, k - 1)

    Fstat = (N - 1.0) * chi2 / (N * (k - 1) - chi2)
    Fprob = 1.0 - stats.f.cdf(Fstat, k - 1, (k - 1) * (N - 1))

    out = {
        "F": {"stat": Fstat, "prob": Fprob},
        "chi": {"stat": chi2, "prob": chiprob},
    }
    return out


def argmin(func, args):
    m, inc = float("inf"), None
    for a in args:
        v = func(a)
        if v < m:
            m, inc = v, a
    return inc


def pairwise_difference_nemenyi(
    avg_ranks: Dict[Method, float], n_datasets: int, alpha=0.05
):
    """Compute the Nemenyi test on all pairwise differences"""
    N = n_datasets
    k = len(avg_ranks)
    q_alpha = qsturng(1 - alpha, k, np.inf) / np.sqrt(2)
    CD = q_alpha * np.sqrt(k * (k + 1) / (6 * N))

    sigdiff = {}
    for method in avg_ranks:
        sigdiff[method] = {}
        for other in avg_ranks:
            if method == other:
                continue
            rank_diff = abs(avg_ranks[method] - avg_ranks[other])
            sigdiff[method][other] = rank_diff >= CD
    return sigdiff, CD


def _compute_wilcoxon_exact(x, y):
    csv = "x,y\n"
    for xi, yi in zip(x, y):
        csv += "%.16f,%.16f\n" % (xi, yi)

    here = os.path.dirname(os.path.abspath(__file__))
    wilcoxon_exact_R = os.path.join(here, "wilcoxon_exact.R")

    if not os.path.exists(wilcoxon_exact_R):
        raise FileNotFoundError(wilcoxon_exact_R)

    with tempfile.TemporaryDirectory() as tmpdir:
        filename = os.path.join(tmpdir, "xy.csv")
        with open(filename, "w") as fp:
            fp.write(csv)

        cmd = [
            "Rscript",
            "--no-save",
            "--slave",
            wilcoxon_exact_R,
            "-i",
            filename,
        ]
        os.system(" ".join(cmd))
        #output = subprocess.check_output(cmd, stderr=subprocess.PIPE)

    output = output.decode()
    return float(output.strip())


def pairwise_difference_wilcoxon_holm(
    filtered_scores: Dict[Dataset, Dict[Method, float]], alpha=0.05
) -> Dict[Method, Dict[Method, bool]]:

    methods = set([m for d in filtered_scores for m in filtered_scores[d]])
    methods = sorted(methods, key=lambda m: m.name)
    datasets = sorted(filtered_scores.keys(), key=lambda d: d.name)

    # Compute p-values for all pairwise tests
    p_values = {}
    for i in range(len(methods)):
        method = methods[i]
        p_values[method] = {}
        for j in range(i + 1, len(methods)):
            other = methods[j]
            method_scores = [filtered_scores[d][method] for d in datasets]
            other_scores = [filtered_scores[d][other] for d in datasets]

            pval = _compute_wilcoxon_exact(method_scores, other_scores)
            p_values[method][other] = pval

    # turn p_values into an array
    P = []
    for i in range(len(methods)):
        method = methods[i]
        for j in range(i + 1, len(methods)):
            other = methods[j]
            P.append(p_values[method][other])

    # Apply Holm's procedure
    reject, corrected, _, _ = multipletests(P, alpha=alpha, method="holm")

    sigdiff = defaultdict(dict)
    c = 0
    for i in range(len(methods)):
        method = methods[i]
        for j in range(i + 1, len(methods)):
            other = methods[j]
            sigdiff[method][other] = reject[c]
            sigdiff[other][method] = reject[c]
            c += 1
    return sigdiff


def pairwise_difference_report(avg_ranks, n_datasets, alpha=0.05):
    sigdiff, CD = pairwise_difference_nemenyi(
        avg_ranks, n_datasets, alpha=alpha
    )

    txt = [
        f"Number of datasets: {n_datasets}",
        f"Number of methods: {len(avg_ranks)}",
        f"Significance level: {alpha}",
        "",
        "Pairwise differences:",
    ]

    for method in sorted(avg_ranks, key=avg_ranks.get):
        txt.append(f"{method.name} (avg. rank = {avg_ranks[method]:.2f})")
        for other in sigdiff[method]:
            is_diff = sigdiff[method][other]
            txt.append(f"\t{other.name} sig. different = {is_diff}")
        txt.append("")

    return CD, txt


def reference_difference(
    avg_ranks: Dict[Method, float],
    n_datasets: int,
    significance_level: float = 0.05,
) -> Tuple[Method, Dict[Method, Dict[str, Any]], float]:
    """Run Holm's procedure agains the method with the lowest rank"""
    N = n_datasets
    k = len(avg_ranks)

    # Create an alphabetically-ordered list of methods and ranks
    method_names = sorted([m.name for m in avg_ranks.keys()])
    methods = [Method[name] for name in method_names]
    ranks = [avg_ranks[m] for m in methods]

    # Identify the reference method (smallest rank) and the "others"
    reference_method = min(avg_ranks, key=avg_ranks.get)
    reference_index = methods.index(reference_method)
    others = [m for m in methods if not m == reference_method]

    # Initialize arrays
    Z_scores = [None] * (k - 1)
    P_values = [None] * (k - 1)
    constant = np.sqrt(6 * N / (k * (k + 1)))

    # Compute the Z-score and corresponding p-value for each method
    for j, method in enumerate(others):
        idx = methods.index(method)
        Z_scores[j] = (ranks[reference_index] - ranks[idx]) * constant
        P_values[j] = stats.norm.cdf(Z_scores[j])

    # Sort the p-values in ascending order
    sorted_p_values = sorted((p, i) for i, p in enumerate(P_values))

    # Calculate significant differences following Holm's procedure
    significantly_different = [None] * (k - 1)
    thresholds = [None] * (k - 1)
    cd_threshold = None
    for i in range(k - 1):
        threshold = significance_level / float(k - (i + 1))
        pvalue, index = sorted_p_values[i]
        significantly_different[index] = pvalue < threshold
        thresholds[index] = threshold
        if pvalue > threshold and cd_threshold is None:
            cd_threshold = threshold

    critical_difference = -1 * stats.norm.ppf(cd_threshold) / constant

    # Collect results
    output = {}
    for j, method in enumerate(others):
        idx = methods.index(method)
        out = dict(
            average_rank=avg_ranks[method],
            Z_score=Z_scores[j],
            P_value=P_values[j],
            threshold=thresholds[j],
            significantly_different=significantly_different[j],
        )
        output[method] = out
    return reference_method, output, critical_difference


def reference_difference_report(
    avg_ranks, n_datasets, significance_level=0.05
):
    reference_method, refdiff_output, CD = reference_difference(
        avg_ranks, n_datasets, significance_level=significance_level
    )

    txt = [
        f"Number of datasets: {n_datasets}",
        f"Number of methods: {len(refdiff_output)+1}",
        f"Reference method: {reference_method}",
        f"Significance level: {significance_level}",
        "",
        f"Reference method rank: {avg_ranks[reference_method]:.6f}",
        "Holm's procedure:",
    ]

    table = []
    for method in refdiff_output:
        row = [
            method.name,
            avg_ranks[method],
            refdiff_output[method]["P_value"],
            refdiff_output[method]["threshold"],
            refdiff_output[method]["significantly_different"],
        ]
        table.append(row)

    txt.append(
        tabulate(
            table,
            headers=["Method", "Rank", "p-Value", "Threshold", "Significant"],
        )
    )
    txt.append("")
    txt.append(f"Critical difference: {CD}")
    txt.append("")

    return reference_method, CD, txt


def main():
    args = parse_args()

    scores = load_score_file(args.input)
    experiment = Experiment[args.experiment]
    dimensionality = Dimensionality[args.dim]
    missing_strategy = MissingStrategy[args.missing]
    filtered_scores = filter_scores(
        scores, experiment, dimensionality, missing_strategy=missing_strategy
    )

    n_datasets = len(filtered_scores)
    avg_ranks, all_ranks = compute_ranks(filtered_scores, higher_better=True)

    if args.mode == "global":
        global_tests = global_difference(avg_ranks, n_datasets)
        if args.output:
            with open(args.output, "w") as fp:
                fp.write(
                    "F = %.1f (p = %g)\n"
                    % (global_tests["F"]["stat"], global_tests["F"]["prob"])
                )
                fp.write(
                    "χ = %.1f (p = %g)"
                    % (
                        global_tests["chi"]["stat"],
                        global_tests["chi"]["prob"],
                    )
                )
        else:
            print(
                "F = %.1f (p = %g)"
                % (global_tests["F"]["stat"], global_tests["F"]["prob"])
            )
            print(
                "χ = %.1f (p = %g)"
                % (
                    global_tests["chi"]["stat"],
                    global_tests["chi"]["prob"],
                )
            )
    elif args.mode == "pairwise":
        CD, txt = pairwise_difference_report(avg_ranks, n_datasets)
        print("\n".join(txt))
    elif args.mode == "reference":
        ref_method, CD, txt = reference_difference_report(
            avg_ranks, n_datasets
        )
        if args.output:
            outRef = args.output + "_ref.tex"
            with open(outRef + "w") as fp:
                fp.write(outRef + "%")
            outCD = args.output + "_CD.tex"
            with open(outCD + "w") as fp:
                fp.write(outCD + "%")
        else:
            print("Reference method = %s, CD = %.2f" % (ref_method, CD))
            print("")
            print("\n".join(txt))


if __name__ == "__main__":
    main()
