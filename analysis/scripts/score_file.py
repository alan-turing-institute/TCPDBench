# -*- coding: utf-8 -*-

"""Script to create "score files" from summary files

Score files are JSON files with the following structure:

    {
        <dataset>: {
            <method1> : <score>,
            <method2> : <score>
            ...
            },
        ...
    }

Author: G.J.J. van den Burg
Copyright (c) 2020 - The Alan Turing Institute
License: See the LICENSE file.

"""

import argparse
import json
import os

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from common import Dataset
from common import Experiment
from common import MISSING_DATASETS
from common import MISSING_METHODS
from common import Method
from common import Metric
from common import Result


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
        help="Metric to use for the score file",
        choices=["f1", "cover"],
        required=True,
    )
    parser.add_argument(
        "-e",
        "--experiment",
        help="Experiment to make score file for",
        choices=["oracle", "default"],
        required=True,
    )
    return parser.parse_args()


def load_summary(filename: str) -> Dict[str, Any]:
    with open(filename, "r") as fp:
        data = json.load(fp)
    return data


def extract_score(
    method_results: List[Dict[str, Any]],
    metric: Metric,
    experiment: Experiment,
) -> Optional[float]:
    """Extract a single numeric score from a list of dictionaries"""

    if not isinstance(metric, Metric):
        raise ValueError("Unknown metric: %s" % metric)
    if not isinstance(experiment, Experiment):
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


def collect_results(
    summary_dir: str, metric: Metric, experiment: Experiment
) -> List[Result]:
    """Collect the results for the experiment on the specified metric.

    Returns a list of Result objects.
    """
    if not isinstance(metric, Metric):
        raise ValueError("Unknown metric: %s" % metric)
    if not isinstance(experiment, Experiment):
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

        for abed_method in summary_results:
            # method names returned from Abed are prefixed with the experiment
            # type, so we skip the ones we don't want
            if not abed_method.startswith(experiment.name + "_"):
                continue

            # extract the metric score for this experiment from the summary
            # results for the method
            score = extract_score(
                summary_results[abed_method],
                metric=metric,
                experiment=experiment,
            )

            # strip the experiment from the method name
            method_name = abed_method[len(experiment.name + "_") :]

            dataset = Dataset[dataset_name]
            method = Method[method_name]

            # determine the placeholder value if there is no score.
            placeholder = set()
            if score is None:
                if (dataset in MISSING_DATASETS) and (
                    not method in MISSING_METHODS
                ):
                    # dataset has missing values and method can't handle it
                    placeholder.add("M")
                else:
                    for result in summary_results[abed_method]:
                        if result["status"] == "FAIL":
                            placeholder.add("F")
                        elif result["status"] == "TIMEOUT":
                            placeholder.add("T")
            placeholder = "/".join(sorted(placeholder))

            # create a Result object
            res = Result(
                dataset=dataset,
                experiment=experiment,
                is_multidim=is_multi,
                method=method,
                metric=metric,
                score=score,
                summary_file=fname,
                placeholder=placeholder or None,
            )
            results.append(res)
    return results


def write_json(results: List[Result]):
    output = {}

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


def main():
    args = parse_args()

    metric = Metric[args.metric]
    experiment = Experiment[args.experiment]

    results = collect_results(
        summary_dir=args.summary_dir, metric=metric, experiment=experiment
    )
    write_json(results)


if __name__ == "__main__":
    main()
