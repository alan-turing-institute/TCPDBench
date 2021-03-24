#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to generate tables from summary files

Metrics, experiments, methods, and datasets are hard-coded as a means of 
validation.

For the "best" experiment, the RBOCPDMS method is excluded because it fails too 
often. For the other experiments, datasets with incomplete results are removed.

Author: G.J.J. van den Burg
Copyright (c) 2020 - The Alan Turing Institute
License: See the LICENSE file.

"""

import argparse
import colorama
import json
import os
import sys
import termcolor

from enum import Enum
from typing import Optional

# from pydantic.dataclasses import dataclass
from dataclasses import dataclass

from latex import build_latex_table

colorama.init()


class Metric(Enum):
    f1 = "f1"
    cover = "cover"
    precision = "precision"
    recall = "recall"


class Experiment(Enum):
    default = "default"
    best = "best"


class Dataset(Enum):
    apple = "apple"
    bank = "bank"
    bee_waggle_6 = "bee_waggle_6"
    bitcoin = "bitcoin"
    brent_spot = "brent_spot"
    businv = "businv"
    centralia = "centralia"
    children_per_woman = "children_per_woman"
    co2_canada = "co2_canada"
    construction = "construction"
    debt_ireland = "debt_ireland"
    gdp_argentina = "gdp_argentina"
    gdp_croatia = "gdp_croatia"
    gdp_iran = "gdp_iran"
    gdp_japan = "gdp_japan"
    global_co2 = "global_co2"
    homeruns = "homeruns"
    iceland_tourism = "iceland_tourism"
    jfk_passengers = "jfk_passengers"
    lga_passengers = "lga_passengers"
    nile = "nile"
    occupancy = "occupancy"
    ozone = "ozone"
    quality_control_1 = "quality_control_1"
    quality_control_2 = "quality_control_2"
    quality_control_3 = "quality_control_3"
    quality_control_4 = "quality_control_4"
    quality_control_5 = "quality_control_5"
    rail_lines = "rail_lines"
    ratner_stock = "ratner_stock"
    robocalls = "robocalls"
    run_log = "run_log"
    scanline_126007 = "scanline_126007"
    scanline_42049 = "scanline_42049"
    seatbelts = "seatbelts"
    shanghai_license = "shanghai_license"
    uk_coal_employ = "uk_coal_employ"
    measles = "measles"
    unemployment_nl = "unemployment_nl"
    us_population = "us_population"
    usd_isk = "usd_isk"
    well_log = "well_log"


class Method(Enum):
    amoc = "amoc"
    binseg = "binseg"
    bocpd = "bocpd"
    bocpdms = "bocpdms"
    cpnp = "cpnp"
    ecp = "ecp"
    kcpa = "kcpa"
    pelt = "pelt"
    prophet = "prophet"
    rbocpdms = "rbocpdms"
    rfpop = "rfpop"
    segneigh = "segneigh"
    wbs = "wbs"
    zero = "zero"


# Methods that support multidimensional datasets
MULTIMETHODS = [
    Method.bocpd,
    Method.bocpdms,
    Method.ecp,
    Method.kcpa,
    Method.rbocpdms,
    Method.zero,
]

# Multidimensional datasets
MULTIDATASETS = [
    Dataset.apple,
    Dataset.bee_waggle_6,
    Dataset.occupancy,
    Dataset.run_log,
]

# Datasets with missing values
MISSING_DATASETS = [Dataset.uk_coal_employ]

# Methods that handle missing values
MISSING_METHODS = [
    Method.bocpdms,
    Method.ecp,
    Method.kcpa,
    Method.prophet,
    Method.zero,
]


@dataclass
class Result:
    dataset: Dataset
    experiment: Experiment
    is_multidim: bool
    method: Method
    metric: Metric
    score: Optional[float]
    summary_file: str
    placeholder: Optional[str]


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
        choices=["f1", "cover", "precision", "recall"],
        required=True,
    )
    parser.add_argument(
        "-e",
        "--experiment",
        help="Experiment to make table for",
        choices=["best", "default"],
        required=True,
    )
    parser.add_argument(
        "-d",
        "--dim",
        help="Dimensionality",
        choices=["uni", "multi", "combined"],
        required=True,
    )
    parser.add_argument(
        "-f",
        "--format",
        help="Output format",
        choices=["json", "tex"],
        required=True,
    )
    parser.add_argument(
        "-t",
        "--type",
        help="Type of table to make",
        choices=["avg", "full"],
        required=True,
    )
    return parser.parse_args()


def warning(msg):
    termcolor.cprint(msg, "yellow", file=sys.stderr)


def load_summary(filename):
    with open(filename, "r") as fp:
        data = json.load(fp)
    return data


def extract_score(method_results, metric=None, experiment=None):
    """Extract a single numeric score from a list of dictionaries"""

    if not isinstance(metric, Metric):
        raise ValueError("Unknown metric: %s" % metric)
    if not experiment in ["default", "best"]:
        raise ValueError("Unknown experiment: %s" % experiment)

    # Collect all values for the chosen metric
    scores = []
    for result in method_results:
        if not result["status"] == "SUCCESS":
            continue
        scores.append(result["scores"][metric.name])

    if len(scores) == 0:
        return None

    # check that we have only one score for the 'default' experiment
    if experiment == "default":
        if len(scores) > 1:
            raise ValueError("Default experiment with more than one score!")
        return scores[0]
    return max(scores)


def collect_results(summary_dir=None, metric=None, experiment=None):
    """Collect the results for the experiment on the specified metric.

    Returns a list of Result objects.
    """
    if not isinstance(metric, Metric):
        raise ValueError("Unknown metric: %s" % metric)
    if not experiment in ["default", "best"]:
        raise ValueError("Unknown experiment: %s" % experiment)
    if not os.path.isdir(summary_dir):
        raise FileNotFoundError(summary_dir)

    results = []
    for fname in sorted(os.listdir(summary_dir)):
        path = os.path.join(summary_dir, fname)
        summary_data = load_summary(path)

        dataset_name = summary_data["dataset"]
        summary_results = summary_data["results"]

        is_multi = summary_data["dataset_ndim"] > 1

        for method in summary_results:
            # method names are prefixed with the experiment type, so we skip
            # the ones we don't want
            if not method.startswith(experiment + "_"):
                continue

            # extract the metric score for this experiment from the summary
            # results for the method
            score = extract_score(
                summary_results[method], metric=metric, experiment=experiment
            )

            # strip the experiment from the method name
            method_name = method[len(experiment + "_") :]

            # determine the placeholder value if there is no score.
            placeholder = set()
            if score is None:
                if (Dataset(dataset_name) in MISSING_DATASETS) and (
                    not Method(method_name) in MISSING_METHODS
                ):
                    # dataset has missing values and method can't handle it
                    placeholder.add("M")
                else:
                    for result in summary_results[method]:
                        if result["status"] == "FAIL":
                            placeholder.add("F")
                        elif result["status"] == "TIMEOUT":
                            placeholder.add("T")
            placeholder = "/".join(sorted(placeholder))

            # create a Result object
            res = Result(
                dataset=Dataset(dataset_name),
                experiment=Experiment(experiment),
                is_multidim=is_multi,
                method=Method(method_name),
                metric=Metric(metric),
                score=score,
                summary_file=fname,
                placeholder=placeholder or None,
            )
            results.append(res)
    return results


def average_results(results):
    """Average the results

    NOTE: This function filters out some methods/datasets for which we have
    insufficient results.
    """
    experiment = list(set(r.experiment for r in results))[0]
    # determine if we're dealing with multidimensional datasets
    is_multi = all(r.is_multidim for r in results)

    expected_methods = MULTIMETHODS if is_multi else list(Method)

    # keep only expected methods
    results = list(filter(lambda r: r.method in expected_methods, results))

    # remove RBOCPDMS for 'best', because it fails too often
    if experiment == Experiment.best:
        warning(
            "\nWarning: Removing RBOCPDMS (experiment = %s) due to insufficient results\n"
            % experiment
        )
        results = list(filter(lambda r: r.method != Method.rbocpdms, results))
        expected_methods.remove(Method.rbocpdms)

    # remove datasets for which we do not have complete results
    to_remove = []
    for dataset in set(r.dataset for r in results):
        dset_results = filter(lambda r: r.dataset == dataset, results)
        if any(r.score is None for r in dset_results):
            to_remove.append(dataset)
    if to_remove:
        warning(
            "\nWarning: Filtering out datasets: %r due to incomplete results for some detectors.\n"
            % to_remove
        )
    results = list(filter(lambda r: not r.dataset in to_remove, results))

    # check that we are now complete: for all datasets and all methods in the
    # remaining results, we have a non-None score.
    assert all(r.score is not None for r in results)

    # compute the average per method
    methods = set(r.method for r in results)
    avg = {}
    for method in methods:
        method_scores = [r.score for r in results if r.method == method]
        avg_score = sum(method_scores) / len(method_scores)
        avg[method.name] = avg_score

    return avg


def write_json(results, is_avg=None):
    if not is_avg in [True, False]:
        raise ValueError("is_avg should be either True or False")

    output = {}
    if is_avg:
        output = results
    else:
        datasets = set(r.dataset for r in results)
        methods = set(r.method for r in results)
        for d in datasets:
            output[d.name] = {}
            for m in methods:
                r = next(
                    (r for r in results if r.dataset == d and r.method == m),
                    None,
                )
                # intended to fail if r is None, because that shouldn't happen
                output[d.name][m.name] = r.score
    print(json.dumps(output, indent="\t", sort_keys=True))


def write_latex(results, dim=None, is_avg=None):
    if is_avg:
        raise NotImplementedError(
            "write_latex is not supported for is_avg = True"
        )

    methods = sorted(set(r.method.name for r in results))
    datasets = sorted(set(r.dataset.name for r in results))
    if dim == "combined":
        uni_datasets = [
            d.name for d in list(Dataset) if not d in MULTIDATASETS
        ]
        multi_datasets = [d.name for d in MULTIDATASETS]
        datasets = sorted(uni_datasets) + sorted(multi_datasets)
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
    tex = build_latex_table(table, headers, floatfmt=".3f", table_spec=spec)

    if dim == "combined":
        # add a horizontal line for these datasets
        lines = tex.split("\n")
        newlines = []
        for line in lines:
            if line.startswith(verb(first_multi)):
                newlines.append("\\hline")
            newlines.append(line)
        tex = "\n".join(newlines)

    print(tex)


def main():
    args = parse_args()
    if args.type == "avg" and args.dim == "combined":
        raise ValueError("Using 'avg' and 'combined' is not supported.")

    results = collect_results(
        summary_dir=args.summary_dir,
        metric=Metric(args.metric),
        experiment=args.experiment,
    )

    if args.dim == "uni":
        # filter out multi
        results = list(filter(lambda r: not r.is_multidim, results))
    elif args.dim == "multi":
        # filter out uni
        results = list(filter(lambda r: r.is_multidim, results))

    if args.type == "avg":
        results = average_results(results)

    if args.format == "json":
        write_json(results, is_avg=args.type == "avg")
    else:
        write_latex(results, args.dim, is_avg=args.type == "avg")


if __name__ == "__main__":
    main()
