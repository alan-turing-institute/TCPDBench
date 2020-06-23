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
    """Compute the MD5 checksum of a given file"""
    blocksize = 65536
    hasher = hashlib.md5()
    with open(filename, "rb") as fp:
        buf = fp.read(blocksize)
        while len(buf) > 0:
            hasher.update(buf)
            buf = fp.read(blocksize)
    return hasher.hexdigest()


def load_dataset(filename):
    """ Load a CPDBench dataset """
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
    """Prepare the experiment output as a dictionary

    Parameters
    ----------
    data : dict
        The CPDBench dataset object

    data_filename : str
        Absolute path to the dataset file

    status : str
        Status of the experiments. Commonly used status codes are: SUCCESS if 
        the experiment was succesful, SKIP is the method was provided improper 
        parameters, FAIL if the method failed for whatever reason, and TIMEOUT 
        if the method ran too long.

    error : str
        If an error occurred, this field can be used to describe what it is. 

    params : dict
        Dictionary of parameters provided to the method. It is good to be as 
        complete as possible, so even default methods should be added to this 
        field. This enhances reproducibility.

    locations : list
        Detected change point locations. Remember that change locations are 
        indices of time points and are 0-based (start counting at zero, thus 
        change locations are integers on the interval [0, T-1], including both 
        endpoints).

    runtime : float
        Runtime of the method. This should be computed as accurately as 
        possible, excluding any method-specific setup code.

    script_filename :
        Path to the script of the method. This is hashed to enable rough 
        versioning.

    """
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
    """Save result to output file or write to stdout (json format)"""
    if filename is None:
        print(json.dumps(output, sort_keys=True, indent="\t"))
    else:
        with open(filename, "w") as fp:
            json.dump(output, fp, sort_keys=True, indent="\t")


def make_param_dict(args, defaults):
    """Create the parameter dict combining CLI arguments and defaults"""
    params = copy.deepcopy(vars(args))
    del params["input"]
    if "output" in params:
        del params["output"]
    params.update(defaults)
    return params


def exit_with_error(data, args, parameters, error, script_filename):
    """Exit and save result using the 'FAIL' exit status"""
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
    """Exit and save result using the 'TIMEOUT' exit status"""
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
    """Exit and save result using the 'SUCCESS' exit status"""
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
