#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Code for compiling latex from Python.

Based on: https://github.com/GjjvdBurg/labella.py

Author: Gertjan van den Burg
Copyright (c) 2020 - The Alan Turing Institute
License: See the LICENSE file.

"""

import os
import shutil
import subprocess
import tabulate
import tempfile


def compile_latex(fname, tmpdirname, silent=True):
    compiler = "latexmk"
    compiler_args = [
        "--pdf",
        "--outdir=" + tmpdirname,
        "--interaction=nonstopmode",
        fname,
    ]
    command = [compiler] + compiler_args
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT)
    except (OSError, IOError) as e:
        raise (e)
    except subprocess.CalledProcessError as e:
        print(e.output.decode())
        raise (e)
    else:
        if not silent:
            print(output.decode())


def build_latex_doc(tex, output_name=None, silent=True):
    with tempfile.TemporaryDirectory() as tmpdirname:
        basename = "labella_text"
        fname = os.path.join(tmpdirname, basename + ".tex")
        with open(fname, "w") as fid:
            fid.write(tex)

        compile_latex(fname, tmpdirname, silent=silent)

        pdfname = os.path.join(tmpdirname, basename + ".pdf")
        if output_name:
            shutil.copy2(pdfname, output_name)


def build_latex_table(
    table,
    headers,
    floatfmt="g",
    missingval="",
    bests="default",
    table_spec=None,
):
    """Construct the LaTeX code for a table

    This function creates the LaTeX code for a data table while taking number 
    formatting, headers, missing values, and "best value formatting" into 
    account.

    The numbers in the table are formatted following the provided float format 
    and the missing value indicator using the ``_format`` function from the 
    ``tabulate`` package. To indicate a missing value the data row should mark 
    this value as ``None``.

    The ``bests`` parameter is used to decide how to highlight the best values 
    in each row. It can be either ``'default'``, ``None``, a list of length 1 
    where the element is either ``min`` or ``max``, or a list of length ``K`` 
    with similar elements where ``K`` is the length of the data table. If it is 
    ``'default'`` then ``max`` will be considered best for each row. If a list 
    of length 1 is supplied then the provided function will be used for each 
    row. If ``None``, no highlighting will be done.

    The ``table_spec`` parameter allows the user to specify the table 
    specification. This value is not checked. If it is None, the first column 
    will get 'l' spec and the remaining columns will get the 'r' spec.

    """
    if bests == "default":
        bests = [max]
    elif bests is None:
        bests = []

    if len(bests) > 1:
        assert len(bests) == len(table)
    assert all((x in [min, max] for x in bests))

    if len(bests) == 0:
        best_funcs = [None for x in range(len(table))]
    elif len(bests) == 1:
        best_funcs = [bests[0] for x in range(len(table))]
    else:
        best_funcs = bests[:]

    _typ = lambda v: tabulate._type(v)
    _fmt = lambda v: tabulate._format(v, _typ(v), floatfmt, missingval)

    list_of_lists, headers = table, headers
    cols = list(zip(*list_of_lists))
    coltypes = list(map(tabulate._column_type, cols))

    cols = [
        [_fmt(v) for v in c]
        for c, ct in zip(cols, coltypes)
    ]

    n_cols = len(cols)

    data_rows = table
    text_rows = list(zip(*cols))

    text = []
    if table_spec is None:
        text.append("\\begin{tabular}{l%s}" % ("r" * (n_cols - 1)))
    else:
        text.append("\\begin{tabular}{%s}" % table_spec)
    text.append(" & ".join(headers) + "\\\\")
    text.append("\\hline")
    for data_row, text_row, best_func in zip(data_rows, text_rows, best_funcs):
        text_row = list(text_row)
        if not best_func is None:
            best_val = best_func([x for x in data_row if isinstance(x, float)])
            best_idx = [i for i, v in enumerate(data_row) if v == best_val]
            for idx in best_idx:
                text_row[idx] = "\\textbf{" + text_row[idx] + "}"
        text.append(" & ".join(text_row) + "\\\\")
    text.append("\\hline")
    text.append("\\end{tabular}")

    return "\n".join(text)
