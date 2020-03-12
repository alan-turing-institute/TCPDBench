#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Utility functions for CPDBench.

Author: Gertjan van den Burg
Copyright (c) 2020 - The Alan Turing Institute
License: See the LICENSE file.

"""

import copy
import hashlib
import json
import numpy as np
import socket
import sys


def md5sum(filename):
    blocksize = 65536
    hasher = hashlib.md5()
    with open(filename, "rb") as fp:
        buf = fp.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = fp.read(blocksize)
    return hasher.hexdigest()


def load_dataset(filename):
    with open(filename, "r") as fp:
        data = json.load(fp)

    if data["time"]["index"] != list(range(0, data["n_obs"])):
        raise NotImplementedError(
            "Time series with non-consecutive time axis are not yet supported."
        )

    mat = np.zeros((data["n_obs"], data["n_dim"]))
    for j, series in enumerate(data["series"]):
        mat[:, j] = series["raw"]

    # We normalize to avoid numerical errors.
    mat = (mat - np.nanmean(mat)) / np.sqrt(np.nanvar(mat))

    return data, mat


def prepare_result(
    data,
    data_filename,
    status,
    error,
    params,
    locations,
    runtime,
    script_filename,
):
    out = {}

    # record the command that was used
    out["command"] = " ".join(sys.argv)

    # save the script and the hash of the script as very rough versioning
    out["script"] = script_filename
    out["script_md5"] = md5sum(script_filename)

    # record the hostname
    out["hostname"] = socket.gethostname()

    # record the dataset name and hash of the dataset
    out["dataset"] = data["name"]
    out["dataset_md5"] = md5sum(data_filename)

    # record the status of the detection and any potential error message
    out["status"] = status
    out["error"] = error

    # save the parameters that were used
    out["parameters"] = params

    # save the detection results
    out["result"] = {"cplocations": locations, "runtime": runtime}

    return out


def dump_output(output, filename=None):
    """Save result to output file or write to stdout """
    if filename is None:
        print(json.dumps(output, sort_keys=True, indent="\t"))
    else:
        with open(filename, "w") as fp:
            json.dump(output, fp, sort_keys=True, indent="\t")


def make_param_dict(args, defaults):
    params = copy.deepcopy(vars(args))
    del params["input"]
    if "output" in params:
        del params["output"]
    params.update(defaults)
    return params


def exit_with_error(data, args, parameters, error, script_filename):
    status = "FAIL"
    out = prepare_result(
        data,
        args.input,
        status,
        error,
        parameters,
        None,
        None,
        script_filename,
    )
    dump_output(out, args.output)
    raise SystemExit

def exit_with_timeout(data, args, parameters, runtime, script_filename):
    status = "TIMEOUT"
    out = prepare_result(
        data,
        args.input,
        status,
        None,
        parameters,
        None,
        runtime,
        script_filename,
    )
    dump_output(out, args.output)
    raise SystemExit


def exit_success(data, args, parameters, locations, runtime, script_filename):
    status = "SUCCESS"
    error = None
    out = prepare_result(
        data,
        args.input,
        status,
        error,
        parameters,
        locations,
        runtime,
        script_filename,
    )
    dump_output(out, args.output)
