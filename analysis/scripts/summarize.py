#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Summarize the results into a single file per dataset.

For each dataset we want::

    {
        "dataset": "<name>",
        "dataset_nobs": N,
        "dataset_ndim": N,
        "annotations": {
            "<user_id>": [...],
            "<user_id>": [...],
            },
        "results": {
            "<method>": [
                {
                    "parameters": {
                        "<param>": value,
                        },
                    "cplocations": [...],
                    "scores": {
                        "<score_1>": value,
                    },
                    "status": <status>
                },
                {
                    "parameters": {
                        "<param>": value,
                        },
                    "cplocations": [...],
                    "scores": {
                        "<score_1>": value,
                    },
                    "status": <status>
                },
                ],
        }
    }

Basic cleanup on the change point locations will also be performed:

    - deduplication
    - removal of invalid indices. Recall that indices are 0-based. We remove 
      any indices smaller than 1 and larger than n_obs - 2. The reason that we 
      don't allow 0 or n_obs - 1 (both valid endpoints) is that several 
      algorithms declare these locations as change points by default and they 
      are meaningless.

Author: Gertjan van den Burg
Copyright (c) 2020 - The Alan Turing Institute
License: See the LICENSE file.

"""

import argparse
import json
import os
import sys

from metrics import f_measure, covering


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-a",
        "--annotation-file",
        help="Path to annotation file",
        required=True,
    )
    parser.add_argument(
        "-d", "--dataset-file", help="Path to dataset file", required=True
    )
    parser.add_argument(
        "-r", "--result-dir", help="Directory of abed results", required=True
    )
    parser.add_argument("-o", "--output-file", help="File to write to")
    return parser.parse_args()


def load_json(filename):
    with open(filename, "r") as fp:
        try:
            data = json.load(fp)
        except json.decoder.JSONDecodeError:
            print("Error parsing json file: %s" % filename, file=sys.stderr)
            return {"error": "parsing error"}
    return data


def load_annotations(filename, dataset):
    with open(filename, "r") as fp:
        data = json.load(fp)
    return data[dataset]


def clean_cps(locations, dataset):
    n_obs = dataset["n_obs"]
    valid = set([x for x in locations if 1 <= x < n_obs - 1])
    return sorted(valid)


def main():
    args = parse_args()

    dataset = load_json(args.dataset_file)
    annotations = load_annotations(args.annotation_file, dataset["name"])

    out = {
        "dataset": dataset["name"],
        "dataset_nobs": dataset["n_obs"],
        "dataset_ndim": dataset["n_dim"],
        "annotations": annotations,
        "results": {},
    }

    data_results = next(
        (d for d in os.listdir(args.result_dir) if d == dataset["name"]), None
    )
    if data_results is None:
        print(
            "Couldn't find the result directory for dataset %s"
            % dataset["name"],
            file=sys.stderr,
        )
        raise SystemExit(1)

    dataset_dir = os.path.join(args.result_dir, data_results)

    for method in sorted(os.listdir(dataset_dir)):
        method_dir = os.path.join(dataset_dir, method)
        for result_file in sorted(os.listdir(method_dir)):
            # print("Processing result file: %s" % result_file)
            fname = os.path.join(method_dir, result_file)
            result = load_json(fname)
            if not method in out["results"]:
                out["results"][method] = []

            if result["status"].lower() == "success":
                locations = clean_cps(result["result"]["cplocations"], dataset)

                f1, precision, recall = f_measure(
                    annotations, locations, return_PR=True
                )
                n_obs = dataset["n_obs"]
                cover = covering(annotations, locations, n_obs)
                scores = {
                    "f1": f1,
                    "precision": precision,
                    "recall": recall,
                    "cover": cover,
                }
            else:
                locations = None
                scores = None

            out["results"][method].append(
                {
                    "parameters": result["parameters"],
                    "task_file": result_file,
                    "cplocations": locations,
                    "scores": scores,
                    "status": result['status'],
                }
            )

    if args.output_file:
        with open(args.output_file, "w") as fp:
            json.dump(out, fp, indent="\t")
    else:
        print(json.dumps(out, indent="\t"))


if __name__ == "__main__":
    main()
