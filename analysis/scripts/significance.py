#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Code to compute significant differences

Author: Gertjan van den Burg
Copyright (c) 2020 - The Alan Turing Institute
License: See the LICENSE file.

"""

import argparse
import math
import scipy.stats as stats

from tabulate import tabulate

from rank_common import (
    load_data,
    preprocess_data,
    compute_ranks,
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("-o", "--output", help="Output basename")
    parser.add_argument(
        "-i", "--input", help="Input JSON file with results for each method"
    )
    parser.add_argument(
        "-m",
        "--mode",
        choices=["global", "reference"],
        help="Whether to do a global difference F test or a reference test to the best performing method",
    )
    parser.add_argument(
        "--type",
        help="Type of table to make",
        choices=["best", "default"],
        required=True,
    )
    return parser.parse_args()


def global_difference(avg_ranks, n_datasets):
    N = n_datasets
    k = len(avg_ranks)
    avg_sq_sum = sum([pow(float(avg_ranks[m]), 2.0) for m in avg_ranks])

    chi2 = (
        12.0 * N / (k * (k + 1)) * (avg_sq_sum - (k * pow(k + 1, 2.0) / 4.0))
    )
    chiprob = 1.0 - stats.chi2.cdf(chi2, k - 1)

    Fstat = (N - 1.0) * chi2 / (N * (k - 1) - chi2)
    Fprob = 1.0 - stats.f.cdf(Fstat, k - 1, (k - 1) * (N - 1))

    return Fstat, Fprob


def argmin(func, args):
    m, inc = float("inf"), None
    for a in args:
        v = func(a)
        if v < m:
            m, inc = v, a
    return inc


def reference_difference(avg_ranks, n_datasets, significance_level=0.05):
    N = n_datasets
    k = len(avg_ranks)

    methods = sorted(avg_ranks.keys())
    ranks = [avg_ranks[m] for m in methods]
    ref_method = argmin(lambda m: avg_ranks[m], methods)
    ref_idx = methods.index(ref_method)
    others = [m for m in methods if not m == ref_method]

    Z_scores = [0.0] * (k - 1)
    P_values = [0.0] * (k - 1)

    constant = math.sqrt(6 * N / (k * (k + 1)))
    for j, method in enumerate(others):
        i = methods.index(method)
        Z_scores[j] = (ranks[ref_idx] - ranks[i]) * constant
        P_values[j] = stats.norm.cdf(Z_scores[j])

    # sort the p-values in ascending order
    sorted_pvals = sorted((p, i) for i, p in enumerate(P_values))

    # Calculate significance differences following Holm's procedure
    significant_differences = [False] * (k - 1)
    thresholds = [0] * (k - 1)
    CD_threshold = None
    for i in range(k - 1):
        threshold = significance_level / float(k - (i + 1))
        pval, idx = sorted_pvals[i]
        significant_differences[idx] = pval < threshold
        thresholds[idx] = threshold
        if pval > threshold and CD_threshold is None:
            CD_threshold = threshold

    # Calculate the critical difference from the first threshold that failed to
    # reject. This works because if the p-value would be below the threshold we
    # would consider it significantly different and above the threshold we
    # would not.
    CD = -1 * stats.norm.ppf(CD_threshold) / constant

    txt = [
        "Number of datasets: %i" % N,
        "Number of methods: %i" % k,
        "Reference method: %s" % ref_method,
        "Significance level: %g" % significance_level,
        "",
        "Reference method rank: %.6f" % avg_ranks[ref_method],
        "Holm's procedure:",
    ]

    table = []
    for o, p, t, s in zip(
        others, P_values, thresholds, significant_differences
    ):
        table.append([o, avg_ranks[o], p, t, s])

    txt.append(
        tabulate(
            table,
            headers=["Method", "Rank", "p-Value", "Threshold", "Significant"],
        )
    )

    txt.append("")
    txt.append(
        "Critical difference: %.6f (at threshold = %.6f)" % (CD, CD_threshold)
    )
    txt.append("")

    return ref_method, CD, txt


def main():
    args = parse_args()

    data = load_data(args.input)
    clean, methods = preprocess_data(data, args.type)

    n_datasets = len(clean)

    avg_ranks, all_ranks = compute_ranks(
        clean, keep_methods=methods, higher_better=True
    )

    if args.mode == "global":
        Fstat, Fprob = global_difference(avg_ranks, n_datasets)
        if args.output:
            with open(args.output, "w") as fp:
                fp.write("F = %.1f (p = %g)" % (Fstat, Fprob))
        else:
            print("Fstat = %.2f, Fprob = %.2g" % (Fstat, Fprob))
    elif args.mode == "reference":
        ref_method, CD, txt = reference_difference(avg_ranks, n_datasets)
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
