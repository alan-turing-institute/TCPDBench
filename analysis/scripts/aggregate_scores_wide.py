# -*- coding: utf-8 -*-

"""
Script to generate the aggregate table (wide version)

Author: Gertjan van den Burg
Copyright (c) 2020 - The Alan Turing Institute
License: See the LICENSE file.

"""

import argparse
import statistics
import tabulate

from typing import Any
from typing import Dict
from typing import Optional

from common import Dataset
from common import Dimensionality
from common import Experiment
from common import Method
from common import Metric
from common import MissingStrategy
from common import filter_scores
from common import load_score_file
from rank_common import compute_ranks
from significance import reference_difference

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
        "--oracle-cover",
        help="Path to score file with results for: oracle/cover",
        required=True,
    )
    parser.add_argument(
        "--oracle-f1",
        help="Path to score file with results for: oracle/f1",
        required=True,
    )
    parser.add_argument(
        "--default-cover",
        help="Path to score file with results for: default/cover",
        required=True,
    )
    parser.add_argument(
        "--default-f1",
        help="Path to score file with results for: default/f1",
        required=True,
    )
    parser.add_argument(
        "-o", "--output", help="Output file to write the table to"
    )
    parser.add_argument(
        "-s",
        "--standalone",
        help="Create a standalone latex file",
        action="store_true",
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


def prepare_table_data(
    default_cover: Dict[Dataset, Dict[Method, Optional[float]]],
    default_f1: Dict[Dataset, Dict[Method, Optional[float]]],
    oracle_cover: Dict[Dataset, Dict[Method, Optional[float]]],
    oracle_f1: Dict[Dataset, Dict[Method, Optional[float]]],
    missing_strategy: Optional[MissingStrategy] = MissingStrategy.complete,
) -> Dict[Dimensionality, Dict[Experiment, Dict[Metric, Dict[str, Any]]]]:
    all_experiments = {
        Experiment.default: {
            Metric.cover: default_cover,
            Metric.f1: default_f1,
        },
        Experiment.oracle: {
            Metric.cover: oracle_cover,
            Metric.f1: oracle_f1,
        },
    }

    table_data = {}
    for dim in Dimensionality:
        table_data[dim] = {}
        for exp in Experiment:
            table_data[dim][exp] = {}
            for metric in Metric:
                # scores are {dataset : {method : score}}
                all_scores = all_experiments[exp][metric]
                filtered_scores = filter_scores(
                    all_scores, exp, dim, missing_strategy=missing_strategy
                )

                # we want {method : {dataset: score}}
                inv_scores = {}
                for dataset in filtered_scores:
                    for method in filtered_scores[dataset]:
                        if not method in inv_scores:
                            inv_scores[method] = {}
                        inv_scores[method][dataset] = filtered_scores[dataset][
                            method
                        ]

                averages = {}
                stdevs = {}
                for method in inv_scores:
                    method_scores = list(inv_scores[method].values())
                    real_scores = [s for s in method_scores if not s is None]

                    if not real_scores:
                        averages[method] = None
                        stdevs[method] = None
                    else:
                        averages[method] = statistics.mean(real_scores)
                        stdevs[method] = statistics.stdev(real_scores)

                table_data[dim][exp][metric] = {
                    "average": averages,
                    "stdev": stdevs,
                    "filtered_scores": filtered_scores,
                }
    return table_data


def make_table(
    default_cover,
    default_f1,
    oracle_cover,
    oracle_f1,
    show_std: Optional[bool] = False,
    missing_strategy: Optional[MissingStrategy] = MissingStrategy.complete,
):
    """Create the aggregate table"""
    tex = []
    tex.append("%% This table requires booktabs!")

    tex.append("\\begin{tabular}{lrrcrrcrrcrr}")
    tex.append("\\toprule")
    superheader = " & ".join(
        [
            "",
            "\\multicolumn{5}{c}{Default}",
            "",
            "\\multicolumn{5}{c}{Oracle} \\\\",
        ]
    )
    tex.append(superheader)
    tex.append("\\cmidrule(lr){2-6} \\cmidrule(lr){8-12}")
    header = " & ".join(
        [
            "",
            "\\multicolumn{2}{c}{Univariate}",
            "",
            "\\multicolumn{2}{c}{Multivariate}",
            "",
            "\\multicolumn{2}{c}{Univariate}",
            "",
            "\\multicolumn{2}{c}{Multivariate} \\\\",
        ]
    )
    tex.append(header)
    tex.append(
        "\\cmidrule(lr){2-3} \\cmidrule(lr){5-6} "
        "\\cmidrule(lr){8-9} \\cmidrule(lr){11-12}"
    )
    subheader = " & " + " & & ".join(["Cover & F1"] * 4) + "\\\\"
    tex.append(subheader)
    tex.append("\\midrule")

    method_names = sorted([m.name for m in list(Method)])
    L = max(map(len, method_names))
    textsc = lambda m: "\\textsc{%s}%s" % (m, (L - len(m)) * " ")
    textbf = lambda s: "\\textbf{%s}" % s
    std_fmt = lambda v: "{\\tiny (%.2f)}" % v
    pad = lambda s: s + " " * 9

    lvl0 = [Experiment.default, Experiment.oracle]
    lvl1 = [Dimensionality.univariate, Dimensionality.multivariate]
    lvl2 = [Metric.cover, Metric.f1]

    table_data = prepare_table_data(
        default_cover,
        default_f1,
        oracle_cover,
        oracle_f1,
        missing_strategy=missing_strategy,
    )

    table = []
    table.append(list(map(textsc, method_names)))
    for exp in lvl0:
        for dim in lvl1:
            for metric in lvl2:
                results = table_data[dim][exp][metric]
                row = []

                avg_ranks, all_ranks = compute_ranks(
                    results["filtered_scores"]
                )
                n_datasets = len(all_ranks)
                refmethod, refdiffs, _ = reference_difference(
                    avg_ranks, n_datasets
                )
                need_bold = lambda m: (m == refmethod) or (
                    not refdiffs[m]["significantly_different"]
                )

                for m in method_names:
                    method = Method[m]
                    avg = results["average"].get(method, None)
                    std = results["stdev"].get(method, None)
                    if avg is None:
                        score_str = " " * (29 if show_std else 14)
                        row.append(score_str)
                        continue

                    avg_str = tabulate._format(avg, float, ".3f", "")

                    avg_str = textbf(avg_str) if need_bold(method) else avg_str
                    if show_std:
                        std_str = std_fmt(std)
                        score_str = "%s %s" % (avg_str, std_str)
                    else:
                        score_str = avg_str
                    score_str = (
                        score_str if need_bold(method) else pad(score_str)
                    )
                    row.append(score_str)
                table.append(row)
            table.append([""] * len(method_names))

    # remove the last empty row
    table.pop(-1)

    transposed = list(zip(*table))
    for row in transposed:
        tex.append(" & ".join(row) + " \\\\")
    tex.append("\\bottomrule")
    tex.append("\\end{tabular}")

    return tex


def main():
    args = parse_args()

    default_cover = load_score_file(args.default_cover)
    default_f1 = load_score_file(args.default_f1)
    oracle_cover = load_score_file(args.oracle_cover)
    oracle_f1 = load_score_file(args.oracle_f1)
    missing_strategy = MissingStrategy[args.missing]

    tex = make_table(
        default_cover,
        default_f1,
        oracle_cover,
        oracle_f1,
        missing_strategy=missing_strategy,
    )
    tex = PREAMBLE + tex + EPILOGUE if args.standalone else tex

    if args.output:
        with open(args.output, "w") as fp:
            fp.write("\n".join(tex))
    else:
        print("\n".join(tex))


if __name__ == "__main__":
    main()
