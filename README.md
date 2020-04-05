# Turing Change Point Detection Benchmark

[![Build Status](https://travis-ci.org/alan-turing-institute/TCPDBench.svg?branch=master)](https://travis-ci.org/alan-turing-institute/TCPDBench)
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
in ``analysis/scripts`` and can be run through the provided ``Makefile``. 

First make sure you have all requirements:

```
$ pip install -r ./analysis/requirements.txt
```

and then use make:

```
$ make results
```

The results will be placed in ``./analysis/output``. Note that to generate the 
figures a working LaTeX and ``latexmk`` installation is needed.

### Reproducing the experiments

To fully reproduce the experiments, some additional steps are needed. Note 
that the Docker procedure outlined below automates this process substantially.

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
   $ pip install abed
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
   installed.

5. Run abed through ``mpiexec``, as follows:

   ```
   $ mpiexec -np 4 abed local
   ```

   This will run abed using 4 cores, which can of course be increased if 
   desired. Note that a minimum of two cores is needed for abed to operate. 
   Furthermore, you may want to run these experiments in parallel on a large 
   number of cores, as the expected runtime is on the order of 21 days on a 
   single core.

### Running the experiments with Docker

If you like to use [Docker](https://www.docker.com/) to manage the environment 
and dependencies, you can do so easily with the provided Dockerfile. You can 
build the Docker image using:

```
$ docker build -t alan-turing-institute/tcpdbench github.com/alan-turing-institute/TCPDBench
```

You can then follow the same procedure as above but using the relevant docker 
commands to run them in the container:

* For reproducing just the tables and figures, use:
  ```
  $ docker run -v /absolute/path/to/TCPDBench:/TCPDBench alan-turing-institute/tcpdbench /bin/bash -c "make results"
  ```

* For reproducing all the experiments:
  ```
  $ docker run -v /absolute/path/to/TCPDBench:/TCPDBench alan-turing-institute/tcpdbench /bin/bash -c "mv abed_results old_abed_results && mkdir abed_results && abed reload_tasks && abed status && make venvs && mpiexec --allow-run-as-root -np 4 abed local && make results"
  ```

where in both cases ``/absolute/path/to/TCPDBench`` is replaced with the path 
on your machine where you want to store the files (so that results are not 
lost when the docker container closes, see [docker 
volumes](https://docs.docker.com/storage/volumes/)).

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
to ``gvandenburg at turing dot ac dot uk``.
