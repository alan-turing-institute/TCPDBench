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
    highlight="default",
    table_spec=None,
    booktabs=False,
) -> str:
    """Construct the LaTeX code for a table

    This function creates the LaTeX code for a data table while taking number
    formatting, headers, missing values, and "best value formatting" into
    account.

    The numbers in the table are formatted following the provided float format
    and the missing value indicator using the ``_format`` function from the
    ``tabulate`` package. To indicate a missing value the data row should mark
    this value as ``None``.

    The ``highlight`` parameter is used to decide how to highlight certain
    values in each row. It can take the following values:
        * ``None``: no highlighting
        * ``default``, ``"max"``, ``max``: highlight the largest value(s)
        * ``"min"``, ``min``: highlight the smallest value(s)
        * A callable that given a list returns the _indices_ of the values to
        highlight. NOTE: The callable is responsible for skipping non-float
        values and returning the proper indices.
        * A list of length equal to the number of rows in the table where each
        element is one of the above. This enables using different highlighting
        for different rows.

    The ``table_spec`` parameter allows the user to specify the table
    specification. This value is not checked. If it is None, the first column
    will get 'l' spec and the remaining columns will get the 'r' spec.

    """
    noop = lambda vs: []

    def is_max(vs):
        max_val = max([v for v in vs if isinstance(v, float)])
        return [i for i, v in enumerate(vs) if v == max_val]

    def is_min(vs):
        min_val = min([v for v in vs if isinstance(v, float)])
        return [i for i, v in enumerate(vs) if v == min_val]

    def make_hl_func(x):
        if x is None:
            return noop
        elif x in ["default", "max", max]:
            return is_max
        elif x in ["min", min]:
            return is_min
        elif callable(x):
            return x
        raise ValueError(f"Unknown highlight function: {x}")

    if isinstance(highlight, list):
        assert len(highlight) == len(table)
        highlight_funcs = [make_hl_func(x) for x in highlight]
    else:
        highlight_funcs = [make_hl_func(highlight)] * len(table)

    _typ = lambda v: tabulate._type(v)
    _fmt = lambda v: tabulate._format(v, _typ(v), floatfmt, missingval)

    list_of_lists, headers = table, headers
    cols = list(zip(*list_of_lists))
    coltypes = list(map(tabulate._column_type, cols))

    cols = [[_fmt(v) for v in c] for c, ct in zip(cols, coltypes)]

    n_cols = len(cols)

    data_rows = table
    text_rows = list(zip(*cols))

    text = []
    if table_spec is None:
        text.append("\\begin{tabular}{l%s}" % ("r" * (n_cols - 1)))
    else:
        text.append("\\begin{tabular}{%s}" % table_spec)
    text.append(" & ".join(headers) + "\\\\")
    text.append("\\toprule" if booktabs else "\\hline")
    for data_row, text_row, hl_func in zip(
        data_rows, text_rows, highlight_funcs
    ):
        text_row = list(text_row)
        if not hl_func is None:
            hl_idx = hl_func(data_row)
            for idx in hl_idx:
                text_row[idx] = "\\textbf{" + text_row[idx] + "}"
        text.append(" & ".join(text_row) + "\\\\")
    text.append("\\bottomrule" if booktabs else "\\hline")
    text.append("\\end{tabular}")

    return "\n".join(text)
