# -*- coding: utf-8 -*-

"""Script to create "rank files" from score files

Rank files are JSON files with the following structure:

    {
        <dataset>: {
            <method1> : <rank>,
            <method2> : <rank>
            ...
            },
        ...
    }

Author: G.J.J. van den Burg
Copyright (c) 2021 - The Alan Turing Institute
License: See the LICENSE file.

"""

import argparse
import json

from typing import Dict
from typing import Optional

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
        help="Experiment to make score file for",
        choices=["oracle", "default"],
        required=True,
    )
    parser.add_argument("-o", "--output-file", help="Output file to write to")
    parser.add_argument(
        "-s",
        "--score-file",
        help="Score file to process",
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


def expand_ranks(
    ranks: Dict[Dataset, Dict[Method, float]]
) -> Dict[Dataset, Dict[Method, Optional[float]]]:

    complete_ranks = {}

    dataset_names = sorted([d.name for d in Dataset])
    method_names = sorted([m.name for m in Method])
    for dataset_name in dataset_names:
        dataset = Dataset[dataset_name]
        complete_ranks[dataset] = {}
        for method_name in method_names:
            method = Method[method_name]
            if not dataset in ranks:
                complete_ranks[dataset][method] = None
                continue
            if not method in ranks[dataset]:
                complete_ranks[dataset][method] = None
                continue
            rank = ranks[dataset][method]
            complete_ranks[dataset][method] = rank
    return complete_ranks


def write_json(
    ranks: Dict[Dataset, Dict[Method, Optional[float]]],
    output_file: Optional[str] = None,
):
    output = {}
    for d in ranks:
        output[d.name] = {}
        for m in ranks[d]:
            output[d.name][m.name] = ranks[d][m]

    json_data = json.dumps(output, indent="\t", sort_keys=True)
    if output_file is None:
        return print(json_data)

    with open(output_file, "w") as fp:
        fp.write(json_data)


def main():
    args = parse_args()
    experiment = Experiment[args.experiment]
    dimensionality = Dimensionality[args.dim]
    missing_strategy = MissingStrategy[args.missing]

    scores = load_score_file(args.score_file)
    filtered_scores = filter_scores(scores, experiment, dimensionality, 
            missing_strategy=missing_strategy)
    _, all_ranks = compute_ranks(filtered_scores, higher_better=True)
    complete_ranks = expand_ranks(all_ranks)
    write_json(complete_ranks, output_file=args.output_file)


if __name__ == "__main__":
    main()
