#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Wrapper for RBOCPDMS in CPDBench.

Author: G.J.J. van den Burg
Date: 2019-10-03
License: See the LICENSE file.
Copyright: 2019, The Alan Turing Institute

"""

import argparse
import numpy as np
import time

from rbocpdms import CpModel, BVARNIGDPD, Detector
from multiprocessing import Process, Manager

from cpdbench_utils import (
    load_dataset,
    make_param_dict,
    exit_with_error,
    exit_with_timeout,
    exit_success,
)

TIMEOUT = 60 * 30  # 30 minutes


def parse_args():
    parser = argparse.ArgumentParser(description="Wrapper for BOCPDMS")
    parser.add_argument(
        "-i", "--input", help="path to the input data file", required=True
    )
    parser.add_argument("-o", "--output", help="path to the output file")
    parser.add_argument(
        "--intensity", help="parameter for the hazard function", type=float
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
    parser.add_argument(
        "--alpha-param", help="alpha parameter", type=float, default=0.5
    )
    parser.add_argument(
        "--alpha-rld", help="alpha rld parameter", type=float, default=0.0
    )
    parser.add_argument("--use-timeout", action="store_true")
    parser.add_argument(
        "--timeout", type=int, help="timeout in minutes", default=30
    )
    return parser.parse_args()


def wrapper(args, return_dict, **kwargs):
    detector = run_rbocpdms(*args, **kwargs)
    return_dict["detector"] = detector


def wrap_with_timeout(args, kwargs, limit):
    manager = Manager()
    return_dict = manager.dict()

    p = Process(target=wrapper, args=(args, return_dict), kwargs=kwargs)
    p.start()
    p.join(limit)
    if p.is_alive():
        p.terminate()
        status = "timeout"
        return None, status
    if "detector" in return_dict:
        status = "success"
        return return_dict["detector"], status
    status = "fail"
    return None, status


def run_rbocpdms(mat, params):
    """Set up and run RBOCPDMS
    """
    S1 = params["S1"]
    S2 = params["S2"]

    # we use "DPD" from the well log example, as that seems to be the robust
    # version.
    model_universe = [
        BVARNIGDPD(
            prior_a=params["prior_a"],
            prior_b=params["prior_b"],
            S1=S1,
            S2=S2,
            alpha_param=params["alpha_param"],
            prior_mean_beta=params["prior_mean_beta"],
            prior_var_beta=params["prior_var_beta"],
            prior_mean_scale=params["prior_mean_scale"],
            prior_var_scale=params["prior_var_scale"],
            general_nbh_sequence=[[[]]] * S1 * S2,
            general_nbh_restriction_sequence=[[0]],
            general_nbh_coupling="weak coupling",
            hyperparameter_optimization="online",
            VB_window_size=params["VB_window_size"],
            full_opt_thinning=params["full_opt_thinning"],
            SGD_batch_size=params["SGD_batch_size"],
            anchor_batch_size_SCSG=params["anchor_batch_size_SCSG"],
            anchor_batch_size_SVRG=None,
            first_full_opt=params["first_full_opt"],
        )
    ]

    model_universe = np.array(model_universe)
    model_prior = np.array([1 / len(model_universe)] * len(model_universe))

    cp_model = CpModel(params["intensity"])

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
        generalized_bayes_rld=params["rld_DPD"],
        alpha_param_learning="individual",
        alpha_param=params["alpha_param"],
        alpha_param_opt_t=100,
        alpha_rld=params["alpha_rld"],
        alpha_rld_learning=True,
        loss_der_rld_learning=params["loss_der_rld_learning"],
    )
    detector.run()

    return detector


def main():
    args = parse_args()

    data, mat = load_dataset(args.input)

    # setting S1 as dimensionality follows the 30portfolio_ICML18.py script.
    # other settings mostly taken from the well log example
    defaults = {
        "S1": mat.shape[1],
        "S2": 1,
        "SGD_batch_size": 10,
        "VB_window_size": 360,
        "anchor_batch_size_SCSG": 25,
        "first_full_opt": 10,
        "full_opt_thinning": 20,
        "intercept_grouping": None,
        "loss_der_rld_learning": "absolute_loss",
        "prior_mean_beta": None,
        "prior_mean_scale": 0,  # data has been standardized
        "prior_var_beta": None,
        "prior_var_scale": 1.0,  # data has been standardized
        "rld_DPD": "power_divergence",  # this ensures doubly robust
    }

    parameters = make_param_dict(args, defaults)

    start_time = time.time()

    error = None
    try:
        if args.use_timeout:
            detector, status = wrap_with_timeout(
                (mat, parameters), {}, TIMEOUT
            )
        elif args.timeout:
            detector, status = wrap_with_timeout(
                (mat, parameters), {}, args.timeout * 60
            )
        else:
            detector = run_rbocpdms(mat, parameters)
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
