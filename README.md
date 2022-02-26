# Turing Change Point Detection Benchmark

[![Reproducible Research](https://github.com/alan-turing-institute/TCPDBench/workflows/Reproducible%20Research/badge.svg)](https://github.com/alan-turing-institute/TCPDBench/actions?query=workflow%3A%22Reproducible+Research%22)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.3740582.svg)](https://doi.org/10.5281/zenodo.3740582)

Welcome to the repository for the Turing Change Point Detection Benchmark, a 
benchmark evaluation of change point detection algorithms developed at [The 
Alan Turing Institute](https://turing.ac.uk). This benchmark uses the time 
series from the [Turing Change Point 
Dataset](https://github.com/alan-turing-institute/TCPD) (TCPD).

**Useful links:**
- [Turing Change Point Detection 
  Benchmark](https://github.com/alan-turing-institute/TCPDBench)
- [Turing Change Point Dataset](https://github.com/alan-turing-institute/TCPD)
- [An Evaluation of Change Point Detection Algorithms](https://arxiv.org/abs/2003.06222) by 
  [Gertjan van den Burg](https://gertjan.dev) and [Chris 
  Williams](https://homepages.inf.ed.ac.uk/ckiw/).
- [Annotation Tool](https://github.com/alan-turing-institute/annotatechange)

If you encounter a problem when using this repository or simply want to ask a 
question, please don't hesitate to [open an issue on 
GitHub](https://github.com/alan-turing-institute/TCPDBench/issues) or send an 
email to ``gertjanvandenburg at gmail dot com``.

## Introduction

Change point detection focuses on accurately detecting moments of abrupt 
change in the behavior of a time series. While many methods for change point 
detection exist, past research has paid little attention to the evaluation of 
existing algorithms on real-world data. This work introduces a benchmark study 
and a dataset ([TCPD](https://github.com/alan-turing-institute/TCPD)) that are 
explicitly designed for the evaluation of change point detection algorithms. 
We hope that our work becomes a proving ground for the comparison and 
development of change point detection algorithms that work well in practice.

This repository contains the code necessary to evaluate and analyze a 
significant number of change point detection algorithms on the TCPD, and 
serves to reproduce the work in [Van den Burg and Williams 
(2020)](https://arxiv.org/abs/2003.06222). Note that work based on either the 
dataset or this benchmark should cite that paper:

```bib
@article{vandenburg2020evaluation,
        title={An Evaluation of Change Point Detection Algorithms},
        author={{Van den Burg}, G. J. J. and Williams, C. K. I.},
        journal={arXiv preprint arXiv:2003.06222},
        year={2020}
}
```

For the experiments we've used the [abed](https://github.com/GjjvdBurg/abed) 
command line program, which makes it easy to organize and run the experiments. 
This means that all experiments are defined through the 
[abed_conf.py](abed_conf.py) file. In particular, the hyperparameters and the 
command line arguments to all methods are defined in that file. Next, all 
methods are called as command line scripts and they are defined in the 
[execs](execs) directory. The raw results from the experiments are collected 
in JSON files and placed in the [abed_results](abed_results) directory, 
organized by dataset and method. Finally, we use 
[Make](https://www.gnu.org/software/make/) to coordinate our analysis scripts: 
first we generate [summary files](analysis/output/summaries) using 
[summarize.py](analysis/scripts/summarize.py), and then use these to generate 
all the tables and figures in the paper.

## Getting Started

This repository contains all the code to generate the results 
(tables/figures/constants) from the paper, as well as to reproduce the 
experiments entirely. You can either install the dependencies directly on your 
machine or use the provided Dockerfile (see below). If you don't use Docker, 
first clone this repository using:

```
$ git clone --recurse-submodules https://github.com/alan-turing-institute/TCPDBench
```

### Generating Tables/Figures

Generating the tables and figures from the paper is done through the scripts 
in ``analysis/scripts`` and can be run through the provided ``Makefile``. A 
working Python and R installation is necessary to reproduce the analysis. For 
Python, install the required dependencies by running:

```
$ pip install -r ./analysis/requirements.txt
```

For R, we need the 
[argparse](https://cran.r-project.org/web/packages/argparse/index.html) and
[exactRankTests](https://cran.r-project.org/web/packages/exactRankTests/index.html) 
packages, which we can install as follows from the command line:

```
$ Rscript -e "install.packages(c('argparse', 'exactRankTests'))"
```

Subsequently we can use make to reproduce the experimental results:

```
$ make results
```

The results will be placed in ``./analysis/output``. Note that to generate the 
figures a working LaTeX and ``latexmk`` installation is needed.

### Reproducing the experiments

To fully reproduce the experiments, some additional steps are needed. Note 
that the Docker procedure outlined below automates this process somewhat.

First, obtain the [Turing Change Point 
Dataset](https://github.com/alan-turing-institute/TCPD) and follow the 
instructions provided there. Copy the dataset files to a ``datasets`` 
directory in this repository.

To run all the tasks we use the [abed](https://github.com/GjjvdBurg/abed) 
command line tool. This allows us to define the experiments in a single 
configuration file (``abed_conf.py``) and makes it easy to keep track of which 
tasks still need to be run.

Note that this repository contains all the result files, so it is not 
necessary to redo all the experiments. If you still wish to do so, the 
instructions are as follows:

1. Move the current result directory out of the way:

   ```
   $ mv abed_results old_abed_results
   ```

2. Install [abed](https://github.com/GjjvdBurg/abed). This requires an 
   existing installation of openmpi, but otherwise should be a matter of 
   running:

   ```
   $ pip install 'abed>=0.1.3'
   ```

3. Tell abed to rediscover all the tasks that need to be done:

   ```
   $ abed reload_tasks
   ```

   This will populate the ``abed_tasks.txt`` file and will automatically 
   commit the updated file to the Git repository. You can show the number of 
   tasks that need to be completed through:

   ```
   $ abed status
   ```

4. Initialize the virtual environments for Python and R, which installs all 
   required dependencies:

   ```
   $ make venvs
   ```

   Note that this will also create an R virtual environment (using 
   [RSimpleVenv](https://github.com/GjjvdBurg/RSimpleVenv)), which ensures 
   that the exact versions of the packages used in the experiments will be 
   installed. This step can take a little while (:coffee:), but is important 
   to ensure reproducibility.

5. Run abed through ``mpiexec``, as follows:

   ```
   $ mpiexec -np 4 abed local
   ```

   This will run abed using 4 cores, which can of course be increased or 
   decreased if desired. Note that a minimum of two cores is needed for abed 
   to operate. You may want to run these experiments in parallel on a large 
   number of cores, as the expected runtime is on the order of 21 days on a 
   single core. Once this command starts running the experiments you will see 
   result files appear in the ``staging`` directory.

### Running the experiments with Docker

If you like to use [Docker](https://www.docker.com/) to manage the environment 
and dependencies, you can do so easily with the provided Dockerfile. You can 
build the Docker image using:

```
$ docker build -t alan-turing-institute/tcpdbench github.com/alan-turing-institute/TCPDBench
```

To ensure that the results created in the docker container persist to the 
host, we need to create a volume first (following [these 
instructions](https://stackoverflow.com/a/47528568/1154005)):

```
$ mkdir /path/to/tcpdbench/results     # *absolute* path where you want the results
$ docker volume create --driver local \
                       --opt type=none \
                       --opt device=/path/to/tcpdbench/results \
                       --opt o=bind tcpdbench_vol
```

You can then follow the same procedure as described above to reproduce the 
experiments, but using the relevant docker commands to run them in the 
container:

* For reproducing just the tables and figures, use:
  ```
  $ docker run -i -t -v tcpdbench_vol:/TCPDBench alan-turing-institute/tcpdbench /bin/bash -c "make results"
  ```

* For reproducing all the experiments, use:
  ```
  $ docker run -i -t -v tcpdbench_vol:/TCPDBench alan-turing-institute/tcpdbench /bin/bash -c "mv abed_results old_abed_results && mkdir abed_results && abed reload_tasks && abed status && make venvs && mpiexec --allow-run-as-root -np 4 abed local && make results"
  ```
  where ``-np 4`` sets the number of cores used for the experiments to four. 
  This can be changed as desired to increase efficiency.


## Extending the Benchmark

It should be relatively straightforward to extend the benchmark with your own 
methods and datasets. Remember to [cite our 
paper](https://arxiv.org/abs/2003.06222) if you do end up using this work.

### Adding a new method

To add a new method to the benchmark, you'll need to write a script in the 
``execs`` folder that takes a dataset file as input and computes the change 
point locations.  Currently the methods are organized by language (R and 
python), but you don't necessarily need to follow this structure when adding a 
new method. Please do check the existing code for inspiration though, as 
adding a new method is probably easiest when following the same structure.

Experiments are managed using the [abed](https://github.com/GjjvdBurg/abed) 
command line application. This facilitates running all the methods with all 
their hyperparameter settings on all datasets.

Note that currently the methods print the output file to stdout, so if you 
want to print from your script, use stderr.

#### Python

When adding a method in Python, you can start with the 
[cpdbench_zero.py](./execs/python/cpdbench_zero.py) file as a template, as 
this contains most of the boilerplate code. A script should take command line 
arguments where ``-i/--input`` marks the path to a dataset file and optionally 
can take further command line arguments for hyperparameter settings. 
Specifying these items from the command line facilitates reproducibility.

Roughly, the main function of a Python method could look like this:

```python
# Adding a new Python method to CPDBench

def main():
  args = parse_args()

  # data is the raw dataset dictionary, mat is a T x d matrix of observations
  data, mat = load_dataset(args.input)

  # set algorithm parameters that are not varied in the grid search
  defaults = {
    'param_1': value_1,
    'param_2': value_2
  }

  # combine command line arguments with defaults
  parameters = make_param_dict(args, defaults)

  # start the timer
  start_time = time.time()
  error = None
  status = 'fail' # if not overwritten, it must have failed

  # run the algorithm in a try/except
  try:
      locations = your_custom_method(mat, parameters)
      status = 'success'
  except Exception as err:
      error = repr(err)

  stop_time = time.time()
  runtime = stop_time - start_time

  # exit with error if the run failed
  if status == 'fail':
    exit_with_error(data, args, parameters, error, __file__)

  # make sure locations are 0-based and integer!

  exit_success(data, args, parameters, locations, runtime, __file__)
```

Remember to add the following to the bottom of the script so it can be run 
from the command line:

```python
if __name__ == '__main__':
  main()
```

If you need to add a timeout to your method, take a look at the 
[BOCPDMS](./execs/python/cpdbench_bocpdms.py) example.

#### R

Adding a method implemented in R to the benchmark can be done similarly to how 
it is done for Python. Again, the input file path and the hyperparameters are 
specified by command line arguments, which are parsed using 
[argparse](https://cran.r-project.org/web/packages/argparse/index.html). For R 
scripts we use a number of utility functions in the 
[utils.R](./execs/R/utils.R) file. To reliably load this file you can use the 
``load.utils()`` function available in all R scripts.

The main function of a method implemented in R could be roughly as follows:

```R
main <- function()
{
  args <- parse.args()

  # load the data
  data <- load.dataset(args$input)

  # create list of default algorithm parameters
  defaults <- list(param_1=value_1, param_2=value_2)

  # combine defaults and command line arguments
  params <- make.param.list(args, defaults)

  # Start the timer
  start.time <- Sys.time()

  # call the detection function in a tryCatch
  result <- tryCatch({
    locs <- your.custom.method(data$mat, params)
    list(locations=locs, error=NULL)
  }, error=function(e) {
    return(list(locations=NULL, error=e$message))
  })

  stop.time <- Sys.time()

  # Compute runtime, note units='secs' is not optional!
  runtime <- difftime(stop.time, start.time, units='secs')

  if (!is.null(result$error))
    exit.with.error(data$original, args, params, result$error)

  # convert result$locations to 0-based if needed

  exit.success(data$original, args, params, locations, runtime)
}
```

Remember to add the following to the bottom of the script so it can be run 
from the command line:

```R
load.utils()
main()
```

#### Adding the method to the experimental configuration

When you've written the command line script to run your method and verified 
that it works correctly, it's time to add it to the experiment configuration. 
For this, we'll have to edit the [abed_conf.py](./abed_conf.py) file.

1. To add your method, located the ``METHODS`` list in the configuration file 
   and add an entry ``oracle_<yourmethod>`` and ``default_<yourmethod>``, 
   replacing ``<yourmethod>`` with the name of your method (without spaces or 
   underscores).
2. Next, add the method to the ``PARAMS`` dictionary. This is where you 
   specify all the hyperparameters that your method takes (for the ``oracle`` 
   experiment). The hyperparameters are specified with a name and a list of 
   values to explore (see the current configuration for examples). For the 
   default experiment, add an entry ``"default_<yourmethod>" : {"no_param": 
   [0]}``. This ensures it will be run without any parameters.
3. Finally, add the command that needs to be executed to run your method to 
   the ``COMMANDS`` dictionary. You'll need an entry for 
   ``oracle_<yourmethod>`` and for ``default_<yourmethod>``. Please use the 
   existing entries as examples. Methods implemented in R are run with 
   Rscript. The ``{execdir}``, ``{datadir}``, and ``{dataset}`` values will be 
   filled in by abed based on the other settings. Use curly braces to specify 
   hyperparameters, matching the names of the fields in the ``PARAMS`` 
   dictionary.


#### Dependencies

If your method needs external R or Python packages to operate, you can add 
them to the respective dependency lists.

* For R, simply add the package name to the [Rpackages.txt](./Rpackages.txt) 
  file. Next, run ``make clean_R_venv`` and ``make R_venv`` to add the package 
  to the R virtual environment. It is recommended to be specific in the 
  version of the package you want to use in the ``Rpackages.txt`` file, for 
  future reference and reproducibility.
* For Python, individual methods use individual virtual environments, as can 
  be seen from the bocpdms and rbocpdms examples. These virtual environments 
  need to be activated in the ``COMMANDS`` section of the ``abed_conf.py`` 
  file. Setting up these environments is done through the Makefile. Simply add 
  a ``requirements.txt`` file in your package similarly to what is done for 
  bocpdms and rbocpdms, copy and edit the corresponding lines in the Makefile, 
  and run ``make venv_<yourmethod>`` to build the virtual environment.


#### Running experiments

When you've added the method and set up the environment, run

```
$ abed reload_tasks
```

to have abed generate the new tasks for your method (see above under [Getting 
Started](#getting-started)). Note that abed automatically does a Git commit 
when you do this, so you may want to switch to a separate branch. You can see 
the tasks that abed has generated (and thus the command that will be executed) 
using the command:

```
$ abed explain_tbd_tasks
```

If you're satisfied with the commands, you can run the experiments using:

```
$ mpiexec -np 4 abed local
```

You can subsequently use the Makefile to generate updated figures and tables 
with your method or dataset.

### Adding a new dataset

To add a new dataset to the benchmark you'll need both a dataset file (in JSON 
format) and annotations (for evaluation). More information on how the datasets 
are constructed can be found in the 
[TCPD](https://github.com/alan-turing-institute/TCPD) repository, which also 
includes a schema file. A high-level overview is as follows:

* Each dataset has a short name in the ``name`` field and a longer more 
  descriptive name in the ``longname`` field. The ``name`` field must be 
  unique.
* The number of observations and dimensions is defined in the ``n_obs`` and 
  ``n_dim`` fields.
* The time axis is defined in the ``time`` field. This has at least an 
  ``index`` field to mark the indices of each data point. At the moment, these 
  indices need to be consecutive integers. This entry mainly exist for a 
  future scenario where we may want to consider non-consecutive timesteps. If 
  the time axis can be mapped to a date or time, then a type and format of 
  this field can be specified (see e.g. the [nile 
  dataset](https://github.com/alan-turing-institute/TCPD/blob/master/datasets/nile/nile.json#L8), 
  which has year labels).
* The actual observations are specified in the ``series`` field. This is an 
  ordered list of JSON objects, one for each dimension. Every dimension has a 
  label, a data type, and a ``"raw"`` field with the actual observations. 
  Missing values in the time series can be marked with ``null`` (see e.g. 
  [uk_coal_employ](https://github.com/alan-turing-institute/TCPD/blob/master/datasets/uk_coal_employ/uk_coal_employ.json#L236) 
  for an example).
* The wrapper around [Prophet](https://facebook.github.io/prophet/) uses the 
  formatted time (for instance YYYY-MM-DD) where available, since Prophet can 
  use this to determine seasonality components. Thus it is recommended to add 
  formatted timesteps to the ``raw`` field in the ``time`` object if possible 
  (see, e.g., the [brent_spot 
  dataset](https://github.com/alan-turing-institute/TCPD/blob/master/datasets/brent_spot/brent_spot.json#L511)). 
  If this is not available, the time series name should be added to the 
  ``NO.DATETIME`` variable in the Prophet wrapper 
  [here](https://github.com/alan-turing-institute/TCPDBench/blob/master/execs/R/cpdbench_prophet.R#L13).

If you want to evaluate the methods in the benchmark on a new dataset, you may 
want to collect annotations for the dataset. These annotations can be 
collected in the [annotations.json](./analysis/annotations/annotations.json) 
file, which is an object that maps each dataset name to a map from the 
annotator ID to the marked change points. You can collect annotations using 
the [annotation tool](https://github.com/alan-turing-institute/annotatechange) 
created for this project.

Finally, add your method to the ``DATASETS`` field in the ``abed_conf.py`` 
file. Proceed with running the experiments as described above.

## License

The code in this repository is licensed under the MIT license, unless 
otherwise specified. See the [LICENSE file](LICENSE) for further details. 
Reuse of the code in this repository is allowed, but should cite [our 
paper](https://arxiv.org/abs/2003.06222).

## Notes

If you find any problems or have a suggestion for improvement of this 
repository, please let us know as it will help us make this resource better 
for everyone. You can open an issue on 
[GitHub](https://github.com/alan-turing-institute/TCPDBench) or send an email 
to ``gertjanvandenburg at gmail dot com``.
