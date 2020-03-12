#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Validate all result files against a given JSON schema.

Author: Gertjan van den Burg

"""


import argparse
import json
import jsonschema
import os


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s", "--schema-file", help="Schema file", default="./schema.json"
    )
    parser.add_argument("-r", "--result-dir", help="Directory with results")
    parser.add_argument(
        "-v", "--verbose", help="Enable verbose mode", action="store_true"
    )
    return parser.parse_args()


def load_schema(schema_file):
    with open(schema_file, "rb") as fp:
        schema = json.load(fp)
    return schema


def scantree(path):
    """Recursively yield DirEntry objects for given directory."""
    for entry in os.scandir(path):
        if entry.is_dir(follow_symlinks=False):
            yield from scantree(entry.path)
        else:
            yield entry


def validate_file(filename, schema):
    with open(filename, "rb") as fp:
        data = json.load(fp)
    jsonschema.validate(instance=data, schema=schema)


def main():
    args = parse_args()

    log = lambda *a, **kw: print(*a, **kw) if args.verbose else None

    schema = load_schema(args.schema_file)
    for entry in scantree(args.result_dir):
        log("Checking file: %s" % entry.path)
        validate_file(entry.path, schema)


if __name__ == "__main__":
    main()
