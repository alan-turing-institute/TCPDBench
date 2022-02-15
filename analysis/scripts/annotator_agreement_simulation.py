# -*- coding: utf-8 -*-

"""Simulation argument to explore annotator agreement

We draw the number of change points for each simulated annotator from a Poisson 
distribution, and subsequently draw the change point locations uniformly over 
the time series. The rate of the Poisson is set to the average number of change 
points over all time series as marked by the human annotators.

Author: Gertjan van den Burg
Copyright (c) 2021 - The Alan Turing Institute
License: See LICENSE file.

"""

import argparse
import numpy as np
import random

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from scipy.stats import poisson

from tqdm import trange

from common import Dataset
from common import Metric
from common import load_summaries
from common import compute_ovr_metric
from latex import build_latex_table


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
        "--output",
        help="Output .tex file to save table to",
        required=True,
    )
    parser.add_argument(
        "--seed",
        help="Seed for the random number generation",
        required=False,
        default=None,
        type=int,
    )
    parser.add_argument(
        "-r",
        "--repeats",
        help="Number of repeats in the simulation",
        type=int,
        default=100_000,
    )
    parser.add_argument(
        "-d", "--dataset", help="Dataset to consider, otherwise all"
    )
    parser.add_argument(
        "--eta", help="Rate for the Poisson distribution", type=float
    )
    return parser.parse_args()


def draw_cps(rate, N):
    # Ensure we never have more CPs than data points
    while (K := poisson.rvs(rate)) > N - 2:
        continue

    # NOTE: here we use [1, N-1) = [1, N - 2] because we use 0-based indexing.
    # This thus corresponds to [2, N-1] in the text.
    cps = random.sample(list(range(1, N - 1)), K)
    return sorted(cps)


def simulate(
    num_annotators: int,
    avg_cp: float,
    n_obs: int,
    repeats: int = 10_000,
    metric: Optional[Metric] = None,
) -> List[float]:

    assert metric in [Metric.f1, Metric.cover]

    ovr_scores = []
    for i in trange(repeats, leave=False):
        sim_anno = {}
        for j in range(num_annotators):
            sim_anno[j] = draw_cps(avg_cp, n_obs)

        sim_ovr = compute_ovr_metric(sim_anno, n_obs, metric)
        avg_ovr = sum(sim_ovr.values()) / num_annotators
        ovr_scores.append(avg_ovr)

    return ovr_scores


def compute_average_annotator_cp(summaries: Dict[Dataset, Dict[str, Any]]):
    # Compute avg_cp, the rate of the Poisson, as an average of averages (so it
    # reflects the expected number of change points declared per annotator)
    num_annos = []
    for dataset in summaries:
        summary = summaries[dataset]
        annotations = summary["annotations"]
        for uid in annotations:
            num_annos.append(len(annotations[uid]))

    return sum(num_annos) / len(num_annos)


def main():
    args = parse_args()

    # set the seed for reproducibility
    seed = args.seed or random.randint(1, 10000)
    print(f"Using random seed: {seed}")
    random.seed(seed)
    np.random.seed(seed)

    # Load the summaries and compute the Poisson rate
    summaries = load_summaries(args.summary_dir)
    if args.eta is None:
        eta = compute_average_annotator_cp(summaries)
    else:
        eta = args.eta
    print(f"Poisson rate = {eta}")

    metrics = {"Covering": Metric.cover, "F1": Metric.f1}
    results = {m: {} for m in metrics}

    for metric_name, metric in metrics.items():
        print(f"Metric: {metric}")
        for dataset in summaries:
            if args.dataset and not args.dataset == dataset.name:
                continue

            summary = summaries[dataset]
            annotations = summary["annotations"]
            n_obs = summary["dataset_nobs"]
            num_ann = len(annotations)

            assert num_ann == 5  # this is just a sanity check for us

            sim_ovr = simulate(
                num_ann,
                eta,
                n_obs,
                repeats=args.repeats,
                metric=metric,
            )

            assert len(sim_ovr) == args.repeats

            # Compute the human annotator average OvR
            human_ann_ovrs = compute_ovr_metric(
                annotations, n_obs, metric=metric
            )
            human_ann_ovr = np.mean(list(human_ann_ovrs.values()))

            n_larger = sum(s >= human_ann_ovr for s in sim_ovr)
            frac = n_larger / args.repeats

            print(
                f"{dataset}: Simulated fraction larger or equal than observed: {frac}"
            )

            results[metric_name][dataset] = frac

    verb = lambda m: "\\verb+%s+" % m
    table = []
    headers = ["Dataset"] + list(metrics.keys())

    for dataset in summaries:
        row = [verb(dataset.name)]
        for metric_name in metrics:
            row.append(results[metric_name][dataset])
        table.append(row)

    spec = "l" + "r" * len(metrics)
    highlight_func = lambda vs: [
        i for i, v in enumerate(vs) if isinstance(v, float) and v >= 0.05
    ]
    tex = build_latex_table(
        table,
        headers,
        floatfmt=".3f",
        highlight=highlight_func,
        table_spec=spec,
        booktabs=True,
    )
    with open(args.output, "w") as fp:
        fp.write(tex)


if __name__ == "__main__":
    main()
