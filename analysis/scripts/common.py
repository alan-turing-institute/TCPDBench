# -*- coding: utf-8 -*-

"""Shared functionality between different scripts

Author: G.J.J. van den Burg
Copyright (c) 2021 - The Alan Turing Institute
License: See the LICENSE file.

"""

import colorama
import enum
import json
import os
import sys
import termcolor

from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from dataclasses import dataclass

from metrics import covering
from metrics import f_measure


class Dataset(enum.Enum):
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


class Dimensionality(enum.Enum):
    univariate = "univariate"
    multivariate = "multivariate"


class Experiment(enum.Enum):
    default = "default"
    oracle = "oracle"


class Method(enum.Enum):
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


class Metric(enum.Enum):
    f1 = "f1"
    cover = "cover"


class MissingStrategy(enum.Enum):
    complete = "complete"  # do complete-case analysis
    zero = "zero"  # give failing methods a score of zero
    zero_no_coal = "zero_no_coal"  # skip uk_coal_employ, zero other failures


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


# Methods that support multidimensional datasets
MULTIMETHODS = (
    Method.bocpd,
    Method.bocpdms,
    Method.ecp,
    Method.kcpa,
    Method.rbocpdms,
    Method.zero,
)

# Multidimensional datasets
MULTIDATASETS = (
    Dataset.apple,
    Dataset.bee_waggle_6,
    Dataset.occupancy,
    Dataset.run_log,
)
UNIDATASETS = tuple(d for d in list(Dataset) if not d in MULTIDATASETS)
QC_DATASETS = (
    Dataset.quality_control_1,
    Dataset.quality_control_2,
    Dataset.quality_control_3,
    Dataset.quality_control_4,
    Dataset.quality_control_5,
)

# Methods that handle missing values
MISSING_METHODS = (
    Method.bocpdms,
    Method.ecp,
    Method.kcpa,
    Method.prophet,
    Method.zero,
)

# Datasets with missing values
MISSING_DATASETS = (Dataset.uk_coal_employ,)


def load_score_file(
    filename: str,
) -> Dict[Dataset, Dict[Method, Optional[float]]]:
    with open(filename, "r") as fp:
        results = json.load(fp)

    typed_results = {}
    for dataset_name in results:
        dataset = Dataset[dataset_name]
        typed_results[dataset] = {}
        for method_name in results[dataset_name]:
            method = Method[method_name]
            typed_results[dataset][method] = results[dataset_name][method_name]
    return typed_results


def load_summaries(summary_dir: str) -> Dict[Dataset, Dict[str, Any]]:
    summaries = {}
    files = os.listdir(summary_dir)
    assert len(files) == len(Dataset)

    for f in sorted(files):
        path = os.path.join(summary_dir, f)
        with open(path, "r") as fp:
            summary_data = json.load(fp)
        dataset = Dataset[summary_data["dataset"]]
        summaries[dataset] = summary_data

    return summaries


def compute_ovr_metric(
    annotations: Dict[int, List[int]], n_obs: int, metric: Metric
) -> Dict[int, float]:
    """Compute the one-vs-rest annotator score for each annotator in the
    provided dictionary of annotations on the given metric.

    Parameters
    ----------
    annotations : Dict[int, List[int]]
        Mapping from annotator ID to a list of change point indices.

    n_obs : int
        Length of the time series in question. This is needed for the covering
        metric.

    metric : Metric
        The metric to use for the evaluation.

    Returns
    -------
    ovr_scores : Dict[int, float]
        Mapping from the annotator ID to the one-vs-rest annotator score on the
        chosen metric.

    """
    ovr = {}
    for j in annotations:
        others = [k for k in annotations if not k == j]
        Ak = {u: annotations[u] for u in others}
        X = annotations[j]
        if metric == Metric.f1:
            ovr[j] = f_measure(Ak, X)
        elif metric == Metric.cover:
            ovr[j] = covering(Ak, X, n_obs)
        else:
            raise ValueError(f"Unknown metric: {metric}")
    return ovr


def filter_scores(
    scores: Dict[Dataset, Dict[Method, Optional[float]]],
    experiment: Experiment,
    dimensionality: Dimensionality,
    missing_strategy: Optional[MissingStrategy] = MissingStrategy.complete,
) -> Dict[Dataset, Dict[Method, float]]:
    """Filter the results, if necessary, according to experiment and dimensionality

    This functionality is needed in a number of tables and figures in the paper
    in order to do the analysis for averages, ranks, etc. Handling failure
    cases can be done either using 'complete case' analysis, by setting a
    score of zero, or a hybrid of the two (this is handled by the
    missing_strategy parameter).

    Parameters
    ----------
    scores: Dict[Dataset, Dict[Method, Optional[float]]
        Scores for all datasets and methods for a particular metric on a
        particular experiment

    experiment: Experiment
        The experiment that the scores refer to

    dimensionalty: Dimensionality
        The dimensionality to consider when filtering.

    missing_strategy: MissingStrategy
        How to deal with missing values (method failures). Either a complete
        case analysis can be done, we can give the failing methods a score of
        zero, or we use a hybrid that skips ``uk_coal_employ`` and uses a score
        of zero for other failures.

    Returns
    -------
    filtered_scores: Dict[Dataset, Dict[Method, float]]
        Returns the scores with the filters applied, which should remove any
        None values.

    """
    cprint(
        f"Filtering results with missing strategy: {missing_strategy}", "cyan"
    )

    # Check which datasets/methods we need based on the desired dimensionality
    if dimensionality == Dimensionality.multivariate:
        expected_methods = list(MULTIMETHODS)
        expected_datasets = list(MULTIDATASETS)
    else:
        expected_methods = list(Method)
        expected_datasets = list(UNIDATASETS)

    # Remove quality control datasets
    expected_datasets = [d for d in expected_datasets if not d in QC_DATASETS]

    # Keep only the scores for the expected methods
    scores = {d: {m: scores[d][m] for m in expected_methods} for d in scores}

    # Keep only the scores for the expected datasets
    scores = {d: scores[d] for d in expected_datasets}

    # Remove datasets for which we do not have complete results
    is_none = lambda v: v is None

    if missing_strategy == MissingStrategy.complete:
        incomplete = [
            d for d in scores if any(map(is_none, scores[d].values()))
        ]

        if incomplete:
            names = [d.name for d in incomplete]
            warning(
                "Warning: Filtering out datasets %r due to "
                "incomplete results for some detectors on %r experiment.\n"
                % (names, experiment.name)
            )
        scores = {d: scores[d] for d in scores if not d in incomplete}
    elif missing_strategy == MissingStrategy.zero:
        for d in scores:
            for m in scores[d]:
                if is_none(scores[d][m]):
                    scores[d][m] = 0.0
                    warning(
                        "Warning: Setting score for method %r on dataset %r to "
                        "zero due to incomplete results on %r experiment.\n"
                        % (m, d, experiment.name)
                    )
    elif missing_strategy == MissingStrategy.zero_no_coal:
        new_scores = {}
        for d in scores:
            if d == Dataset.uk_coal_employ:
                warning(
                    "Warning: Filtering out dataset %r due to "
                    "incomplete results for some detectors on %r experiment.\n"
                    % (d, experiment.name)
                )
                continue

            new_scores[d] = {}
            for m in scores[d]:
                if is_none(scores[d][m]):
                    new_scores[d][m] = 0.0
                    warning(
                        "Warning: Setting score for method %r on dataset %r to "
                        "zero due to incomplete results on %r experiment.\n"
                        % (m, d, experiment.name)
                    )
                else:
                    new_scores[d][m] = scores[d][m]
        scores = new_scores

    # Check that there are no None scores any more
    assert not any(any(map(is_none, scores[d].values())) for d in scores)
    return scores


def cprint(*args, **kwargs):
    # This is needed for windows support (https://stackoverflow.com/q/21858567)
    colorama.init()
    termcolor.cprint(*args, **kwargs)


def warning(msg):
    cprint(msg, "yellow", file=sys.stderr)
