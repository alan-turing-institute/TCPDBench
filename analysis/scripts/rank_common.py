# -*- coding: utf-8 -*-

"""Shared code to do with ranks

Author: Gertjan van den Burg
Copyright (c) 2020 - The Alan Turing Institute
License: See the LICENSE file.

"""

import colorama
import json
import numpy as np
import sys
import termcolor

from scipy.stats import rankdata

colorama.init()


def load_data(filename):
    with open(filename, "r") as fp:
        return json.load(fp)


def compute_ranks(results, keep_methods=None, higher_better=True):
    """Compute the ranks

    Parameters
    ----------
    results : dict
        Mapping from dataset name to dict, where each dict in turn is a map 
        from method name to a score value.

    keep_methods: list
        Methods to include in the ranks

    higher_better: bool
        Whether a higher or a lower value is considered better

    Returns
    -------
    avg_ranks : dict
        Map from method name to average rank

    all_ranks: dict
        Map from dataset name to dictionary, which is in turn a map from method 
        name to rank for that dataset and that method.

    """
    vec_ranks = []
    all_ranks = {}

    for dset in results:
        methods = results[dset].keys()
        methods = sorted(methods)

        methods = [m for m in methods if m in keep_methods]
        assert methods == keep_methods

        if higher_better:
            values = [-results[dset][m] for m in methods]
        else:
            values = [results[dset][m] for m in methods]

        if any(np.isnan(v) for v in values):
            print(
                "Skipping dataset %s because of nans" % dset, file=sys.stderr
            )
            continue

        ranks = rankdata(values, method="average")

        vec_ranks.append(ranks)
        rank_dict = {m: ranks[i] for i, m in enumerate(methods)}

        all_ranks[dset] = rank_dict

    avg_ranks = np.mean(vec_ranks, axis=0)
    avg_ranks = {m: r for m, r in zip(methods, avg_ranks)}
    return avg_ranks, all_ranks


def warning(msg):
    termcolor.cprint(msg, "yellow", file=sys.stderr)


def preprocess_data(data, _type):
    methods = set([m for dset in data.keys() for m in data[dset].keys()])
    methods = sorted(methods)

    # filter out rbocpdms on "best" (uni or multi)
    if _type == "best":
        warning(
            "\nWarning: Filtering out RBOCPDMS due to insufficient results.\n"
        )
        methods = [m for m in methods if not m == "rbocpdms"]

    # filter out methods that have no results on any dataset
    methods_no_result = set()
    for m in methods:
        if all(data[d][m] is None for d in data):
            methods_no_result.add(m)
    if methods_no_result:
        print(
            "\nWarning: Filtering out %r due to no results on any series\n"
            % methods_no_result,
            file=sys.stderr,
        )
        methods = [m for m in methods if not m in methods_no_result]

    data_w_methods = {}
    for dset in data:
        data_w_methods[dset] = {}
        for method in methods:
            data_w_methods[dset][method] = data[dset][method]

    data_no_missing = {}
    for dset in data_w_methods:
        if any((x is None for x in data_w_methods[dset].values())):
            continue
        data_no_missing[dset] = data_w_methods[dset]
    return data_no_missing, methods
