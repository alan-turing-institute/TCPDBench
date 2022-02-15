# -*- coding: utf-8 -*-

"""Shared code to do with ranks

Author: Gertjan van den Burg
Copyright (c) 2020 - The Alan Turing Institute
License: See the LICENSE file.

"""

import numpy as np

from typing import Dict

from scipy.stats import rankdata

from common import Dataset
from common import Method


def compute_ranks(
    scores: Dict[Dataset, Dict[Method, float]],
    higher_better=True,
):
    """Compute the ranks

    Parameters
    ----------
    scores : dict
        Mapping from dataset name to dict, where each dict in turn is a map
        from method name to a score value. It is assumed there are no None
        values in this input.

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

    known_methods = set([m for d in scores for m in scores[d]])
    method_names = sorted([m.name for m in known_methods])
    methods_by_name = {name: Method[name] for name in method_names}

    for dataset in scores:
        values = []
        for method_name in method_names:
            method = methods_by_name[method_name]
            # scipy's rankdata assigns rank 1 to the lowest value by default
            sign = -1 if higher_better else 1
            values.append(sign * scores[dataset][method])

        ranks = rankdata(values, method="average")

        vec_ranks.append(ranks)
        rank_dict = {}
        for i, method_name in enumerate(method_names):
            method = methods_by_name[method_name]
            rank_dict[method] = ranks[i]

        all_ranks[dataset] = rank_dict

    avg_ranks = np.mean(vec_ranks, axis=0)
    average_ranks = {}
    for i, method_name in enumerate(method_names):
        method = methods_by_name[method_name]
        average_ranks[method] = avg_ranks[i]

    return average_ranks, all_ranks
