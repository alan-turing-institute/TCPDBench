#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper for BOCPDMS in CPDBench.

Author: G.J.J. van den Burg
Date: 2019-10-02
License: See the LICENSE file.
Copyright: 2019, The Alan Turing Institute

"""

import argparse
import numpy as np
import time

from bocpdms import CpModel, BVARNIG, Detector
from multiprocessing import Process, Manager

from cpdbench_utils import (
    load_dataset,
    make_param_dict,
    exit_with_error,
    exit_with_timeout,
    exit_success,
)

# Ensure overflow errors are raised
# np.seterr(over="raise")

TIMEOUT = 60 * 30  # 30 minutes


def parse_args():
    parser = argparse.ArgumentParser(description="Wrapper for BOCPDMS")
    parser.add_argument(
        "-i", "--input", help="path to the input data file", required=True
    )
    parser.add_argument("-o", "--output", help="path to the output file")
    parser.add_argument(
        "--intensity",
        help="parameter for the hazard function",
        type=float,
        required=True,
    )
    parser.add_argument(
        "--prior-a", help="initial value of a", type=float, required=True
    )
    parser.add_argument(
        "--prior-b", help="initial value of b", type=float, required=True
    )
    parser.add_argument(
        "--threshold", help="threshold to apply", type=int, default=0
    )
    parser.add_argument("--use-timeout", action="store_true")

    return parser.parse_args()


def wrapper(args, return_dict, **kwargs):
    detector = run_bocpdms(*args, **kwargs)
    return_dict["detector"] = detector


def wrap_with_timeout(args, kwargs, limit):
    manager = Manager()
    return_dict = manager.dict()

    p = Process(target=wrapper, args=(args, return_dict), kwargs=kwargs)
    p.start()
    p.join(limit)
    if p.is_alive():
        p.terminate()
        return None, "timeout"
    if "detector" in return_dict:
        return return_dict["detector"], "success"
    return None, "fail"


def run_bocpdms(mat, params):
    """Set up and run BOCPDMS
    """

    AR_models = []
    for lag in range(params["lower_AR"], params["upper_AR"] + 1):
        AR_models.append(
            BVARNIG(
                prior_a=params["prior_a"],
                prior_b=params["prior_b"],
                S1=params["S1"],
                S2=params["S2"],
                prior_mean_scale=params["prior_mean_scale"],
                prior_var_scale=params["prior_var_scale"],
                intercept_grouping=params["intercept_grouping"],
                nbh_sequence=[0] * lag,
                restriction_sequence=[0] * lag,
                hyperparameter_optimization="online",
            )
        )

    cp_model = CpModel(params["intensity"])

    model_universe = np.array(AR_models)
    model_prior = np.array([1 / len(AR_models) for m in AR_models])

    detector = Detector(
        data=mat,
        model_universe=model_universe,
        model_prior=model_prior,
        cp_model=cp_model,
        S1=params["S1"],
        S2=params["S2"],
        T=mat.shape[0],
        store_rl=True,
        store_mrl=True,
        trim_type="keep_K",
        threshold=params["threshold"],
        save_performance_indicators=True,
        generalized_bayes_rld="kullback_leibler",
        # alpha_param_learning="individual",  # not sure if used
        # alpha_param=0.01,  # not sure if used
        # alpha_param_opt_t=30,  # not sure if used
        # alpha_rld_learning=True,  # not sure if used
        loss_der_rld_learning="squared_loss",
        loss_param_learning="squared_loss",
    )
    detector.run()

    return detector


def main():
    args = parse_args()

    data, mat = load_dataset(args.input)

    # setting S1 as dimensionality follows the 30portfolio_ICML18.py script.
    defaults = {
        "S1": mat.shape[1],
        "S2": 1,
        "intercept_grouping": None,
        "prior_mean_scale": 0,  # data is standardized
        "prior_var_scale": 1,  # data is standardized
    }

    # pick the lag lengths based on the paragraph below the proof of Theorem 1,
    # using C = 1, as in ``30portfolio_ICML18.py``.
    T = mat.shape[0]
    Lmin = 1
    Lmax = int(pow(T / np.log(T), 0.25) + 1)
    defaults["lower_AR"] = Lmin
    defaults["upper_AR"] = Lmax

    parameters = make_param_dict(args, defaults)

    start_time = time.time()

    error = None
    status = "fail" # if not overwritten, it must have failed
    try:
        if args.use_timeout:
            detector, status = wrap_with_timeout(
                (mat, parameters), {}, TIMEOUT
            )
        else:
            detector = run_bocpdms(mat, parameters)
            status = "success"
    except Exception as err:
        error = repr(err)

    stop_time = time.time()
    runtime = stop_time - start_time

    if status == "timeout":
        exit_with_timeout(data, args, parameters, runtime, __file__)

    if not error is None or status == "fail":
        exit_with_error(data, args, parameters, error, __file__)

    # According to the Nile unit test, the MAP change points are in
    # detector.CPs[-2], with time indices in the first of the two-element
    # vectors.
    locations = [x[0] for x in detector.CPs[-2]]

    # Based on the fact that time_range in plot_raw_TS of the EvaluationTool
    # starts from 1 and the fact that CP_loc that same function is ensured to
    # be in time_range, we assert that the change point locations are 1-based.
    # We want 0-based, so subtract 1 from each point.
    locations = [loc - 1 for loc in locations]

    # convert to Python ints
    locations = [int(loc) for loc in locations]

    exit_success(data, args, parameters, locations, runtime, __file__)


if __name__ == "__main__":
    main()
