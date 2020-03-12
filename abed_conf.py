import copy

##############################################################################
#                                General Settings                            #
##############################################################################
PROJECT_NAME = "cpdbench"
TASK_FILE = "abed_tasks.txt"
AUTO_FILE = "abed_auto.txt"
RESULT_DIR = "./abed_results"
STAGE_DIR = "./stagedir"
PRUNE_DIR = "./pruned"
MAX_FILES = 1000
ZIP_DIR = "./zips"
LOG_DIR = "./logs"
OUTPUT_DIR = "./output"
AUTO_SLEEP = 120
HTML_PORT = 8000
COMPRESSION = "bzip2"
RESULT_EXTENSION = ".json"

##############################################################################
#                          Server parameters and settings                    #
##############################################################################
REMOTE_USER = "username"
REMOTE_HOST = "address.of.host"
REMOTE_DIR = "/home/%s/projects/%s" % (REMOTE_USER, PROJECT_NAME)
REMOTE_PORT = 22
REMOTE_SCRATCH = None
REMOTE_SCRATCH_ENV = "TMPDIR"

##############################################################################
#                      Settings for Master/Worker program                    #
##############################################################################
MW_SENDATONCE = 1  # number of tasks (hashes!) to send at once
MW_COPY_WORKER = False
MW_COPY_SLEEP = 120
MW_NUM_WORKERS = None

##############################################################################
#                               Experiment type                              #
##############################################################################
# Uncomment the desired type
# Model assessment #
TYPE = "ASSESS"

# Cross validation with train and test dataset #
# TYPE = 'CV_TT'
# CV_BASESEED = 123456
# YTRAIN_LABEL = 'y_train'

# Commands defined in a text file #
# TYPE = 'RAW'
# RAW_CMD_FILE = '/path/to/file.txt'

##############################################################################
#                                Build settings                              #
##############################################################################
NEEDS_BUILD = False  # If remote compilation is required
BUILD_DIR = "build"  # Relative directory where build takes place
BUILD_CMD = "make all"  # Build command

##############################################################################
#                      Experiment parameters and settings                    #
##############################################################################
DATADIR = "datasets"
EXECDIR = "execs"

DATASETS = [
    "apple",
    "bank",
    "bee_waggle_6",
    "bitcoin",
    "brent_spot",
    "businv",
    "centralia",
    "children_per_woman",
    "co2_canada",
    "construction",
    "debt_ireland",
    "gdp_argentina",
    "gdp_croatia",
    "gdp_iran",
    "gdp_japan",
    "global_co2",
    "homeruns",
    "iceland_tourism",
    "jfk_passengers",
    "lga_passengers",
    "measles",
    "nile",
    "occupancy",
    "ozone",
    "quality_control_1",
    "quality_control_2",
    "quality_control_3",
    "quality_control_4",
    "quality_control_5",
    "rail_lines",
    "ratner_stock",
    "robocalls",
    "run_log",
    "scanline_126007",
    "scanline_42049",
    "seatbelts",
    "shanghai_license",
    "uk_coal_employ",
    "unemployment_nl",
    "usd_isk",
    "us_population",
    "well_log",
]
DATASET_NAMES = {k: k for k in DATASETS}

METHODS = [
    "best_bocpd",
    "best_bocpdms",
    "best_rbocpdms",
    "best_cpnp",
    "best_pelt",
    "best_amoc",
    "best_segneigh",
    "best_binseg",
    "best_rfpop",
    "best_ecp",
    "best_kcpa",
    "best_wbs",
    "best_prophet",
    "default_bocpd",
    "default_bocpdms",
    "default_rbocpdms",
    "default_cpnp",
    "default_pelt",
    "default_amoc",
    "default_segneigh",
    "default_binseg",
    "default_rfpop",
    "default_ecp",
    "default_kcpa",
    "default_wbs",
    "default_prophet",
]

# many of these combinations will be invalid for the changepoint package, but
# it's easier to do it this way than to generate only the valid configurations.
R_changepoint_params = {
    "function": ["mean", "var", "meanvar"],
    "penalty": [
        "None",
        "SIC",
        "BIC",
        "MBIC",
        "AIC",
        "Hannan-Quinn",
        "Asymptotic",
    ],
    "statistic": ["Normal", "CUSUM", "CSS", "Gamma", "Exponential", "Poisson"],
}
R_changepoint_params_seg = copy.deepcopy(R_changepoint_params)
R_changepoint_params_seg["Q"] = ["max", "default"]

PARAMS = {
    "best_bocpd": {
        "intensity": [50, 100, 200],
        "prior_a": [0.01, 1.0, 100],
        "prior_b": [0.01, 1.0, 100],
        "prior_k": [0.01, 1.0, 100],
    },
    "best_bocpdms": {
        "intensity": [50, 100, 200],
        "prior_a": [0.01, 1.0, 100],
        "prior_b": [0.01, 1.0, 100],
    },
    "best_rbocpdms": {
        "intensity": [50, 100, 200],
        "prior_a": [0.01, 1.0, 100],
        "prior_b": [0.01, 1.0, 100],
        "alpha_param": [0.5],
        "alpha_rld": [0.5],
    },
    "best_cpnp": {
        "penalty": [
            "None",
            "SIC",
            "BIC",
            "MBIC",
            "AIC",
            "Hannan-Quinn",
            "Asymptotic",
        ],
        "quantiles": [10, 20, 30, 40],
    },
    "best_pelt": R_changepoint_params,
    "best_amoc": R_changepoint_params,
    "best_segneigh": R_changepoint_params_seg,
    "best_binseg": R_changepoint_params_seg,
    "best_rfpop": {"loss": ["L1", "L2", "Huber", "Outlier"]},
    "best_ecp": {
        "algorithm": ["e.agglo", "e.divisive"],
        "siglvl": [0.01, 0.05],
        "minsize": [2, 30],
        "alpha": [0.5, 1.0, 1.5],
    },
    "best_kcpa": {
        "maxcp": ["max", "default"],
        "cost": [1e-3, 1e-2, 1e-1, 1, 1e1, 1e2, 1e3],
    },
    "best_wbs": {
        "Kmax": ["max", "default"],
        "penalty": ["SSIC", "BIC", "MBIC"],
        "integrated": ["true", "false"],
    },
    "best_prophet": {"Nmax": ["max", "default"]},
    "default_bocpd": {"no_param": [0]},
    "default_bocpdms": {"no_param": [0]},
    "default_rbocpdms": {"no_param": [0]},
    "default_cpnp": {"no_param": [0]},
    "default_pelt": {"no_param": [0]},
    "default_amoc": {"no_param": [0]},
    "default_segneigh": {"no_param": [0]},
    "default_binseg": {"no_param": [0]},
    "default_rfpop": {"no_param": [0]},
    "default_ecp": {"no_param": [0]},
    "default_kcpa": {"no_param": [0]},
    "default_wbs": {"no_param": [0]},
    "default_prophet": {"no_param": [0]},
}

COMMANDS = {
    "best_amoc": "Rscript --no-save --slave {execdir}/R/cpdbench_changepoint.R -i {datadir}/{dataset}.json -p {penalty} -f {function} -t {statistic} -m AMOC",
    "best_binseg": "Rscript --no-save --slave {execdir}/R/cpdbench_changepoint.R -i {datadir}/{dataset}.json -p {penalty} -f {function} -t {statistic} -m BinSeg -Q {Q}",
    "best_cpnp": "Rscript --no-save --slave {execdir}/R/cpdbench_changepointnp.R -i {datadir}/{dataset}.json -p {penalty} -q {quantiles}",
    "best_ecp": "Rscript --no-save --slave {execdir}/R/cpdbench_ecp.R -i {datadir}/{dataset}.json -a {algorithm} --siglvl {siglvl} --minsize {minsize} --alpha {alpha}",
    "best_kcpa": "Rscript --no-save --slave {execdir}/R/cpdbench_ecp.R -i {datadir}/{dataset}.json -a kcpa --maxcp {maxcp} --cost {cost}",
    "best_pelt": "Rscript --no-save --slave {execdir}/R/cpdbench_changepoint.R -i {datadir}/{dataset}.json -p {penalty} -f {function} -t {statistic} -m PELT",
    "best_prophet": "Rscript --no-save --slave {execdir}/R/cpdbench_prophet.R -i {datadir}/{dataset}.json -N {Nmax}",
    "best_rfpop": "Rscript --no-save --slave {execdir}/R/cpdbench_rfpop.R -i {datadir}/{dataset}.json -l {loss}",
    "best_segneigh": "Rscript --no-save --slave {execdir}/R/cpdbench_changepoint.R -i {datadir}/{dataset}.json -p {penalty} -f {function} -t {statistic} -m SegNeigh -Q {Q}",
    "best_wbs": "Rscript --no-save --slave {execdir}/R/cpdbench_wbs.R -i {datadir}/{dataset}.json -K {Kmax} --penalty {penalty} -g {integrated}",
    "best_bocpd": "Rscript --no-save --slave {execdir}/R/cpdbench_ocp.R -i {datadir}/{dataset}.json -l {intensity} --prior-a {prior_a} --prior-b {prior_b} --prior-k {prior_k}",
    "best_bocpdms": (
        "source {execdir}/python/bocpdms/venv/bin/activate && python {execdir}/python/cpdbench_bocpdms.py -i {datadir}/{dataset}.json --intensity {intensity} --prior-a {prior_a} --prior-b {prior_b} --threshold 100 --use-timeout"
    ),
    "best_rbocpdms": (
        "source {execdir}/python/rbocpdms/venv/bin/activate && python {execdir}/python/cpdbench_rbocpdms.py -i {datadir}/{dataset}.json --intensity {intensity} --prior-a {prior_a} --prior-b {prior_b} --threshold 100 --alpha-param {alpha_param} --alpha-rld {alpha_rld} --use-timeout"
    ),
    "default_amoc": "Rscript --no-save --slave {execdir}/R/cpdbench_changepoint.R -i {datadir}/{dataset}.json -p MBIC -f mean -t Normal -m AMOC",
    "default_binseg": "Rscript --no-save --slave {execdir}/R/cpdbench_changepoint.R -i {datadir}/{dataset}.json -p MBIC -f mean -t Normal -m BinSeg -Q default",
    "default_cpnp": "Rscript --no-save --slave {execdir}/R/cpdbench_changepointnp.R -i {datadir}/{dataset}.json -p MBIC -q 10",
    "default_pelt": "Rscript --no-save --slave {execdir}/R/cpdbench_changepoint.R -i {datadir}/{dataset}.json -p MBIC -f mean -t Normal -m PELT",
    "default_segneigh": "Rscript --no-save --slave {execdir}/R/cpdbench_changepoint.R -i {datadir}/{dataset}.json -p BIC -f mean -t Normal -m SegNeigh -Q default",
    "default_wbs": "Rscript --no-save --slave {execdir}/R/cpdbench_wbs.R -i {datadir}/{dataset}.json -K default -p SSIC -g true",
    "default_prophet": "Rscript --no-save --slave {execdir}/R/cpdbench_prophet.R -i {datadir}/{dataset}.json -N default",
    "default_rfpop": "Rscript --no-save --slave {execdir}/R/cpdbench_rfpop.R -i {datadir}/{dataset}.json -l Outlier",
    "default_ecp": "Rscript --no-save --slave {execdir}/R/cpdbench_ecp.R -i {datadir}/{dataset}.json -a e.divisive --alpha 1.0 --minsize 30 --runs 199 --siglvl 0.05",
    "default_kcpa": "Rscript --no-save --slave {execdir}/R/cpdbench_ecp.R -i {datadir}/{dataset}.json -a kcpa -C 1.0 -L max",
    "default_bocpd": "Rscript --no-save --slave {execdir}/R/cpdbench_ocp.R -i {datadir}/{dataset}.json -l 100 --prior-a 1.0 --prior-b 1.0 --prior-k 1.0",
    "default_bocpdms": "source {execdir}/python/bocpdms/venv/bin/activate && python {execdir}/python/cpdbench_bocpdms.py -i {datadir}/{dataset}.json --intensity 100 --prior-a 1.0 --prior-b 1.0 --threshold 0",
    "default_rbocpdms": "source {execdir}/python/rbocpdms/venv/bin/activate && python {execdir}/python/cpdbench_rbocpdms.py -i {datadir}/{dataset}.json --intensity 100 --prior-a 1.0 --prior-b 1.0 --threshold 100 --alpha-param 0.5 --alpha-rld 0.5 --timeout 240",
}

METRICS = {}

SCALARS = {"time": {"best": min}}

RESULT_PRECISION = 15

DATA_DESCRIPTION_CSV = None

REFERENCE_METHOD = None

SIGNIFICANCE_LEVEL = 0.05

###############################################################################
#                                PBS Settings                                 #
###############################################################################
PBS_NODES = 1
PBS_WALLTIME = 360  # Walltime in minutes
PBS_CPUTYPE = None
PBS_CORETYPE = None
PBS_PPN = None
PBS_MODULES = ["mpicopy", "python/2.7.9"]
PBS_EXPORTS = ["PATH=$PATH:/home/%s/.local/bin/abed" % REMOTE_USER]
PBS_MPICOPY = ["datasets", "execs", TASK_FILE]
PBS_TIME_REDUCE = 600  # Reduction of runtime in seconds
PBS_LINES_BEFORE = []
PBS_LINES_AFTER = []
