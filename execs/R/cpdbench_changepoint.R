#' ---
#' title: Wrapper for changepoint package in TCPDBench
#' author: G.J.J. van den Burg
#' date: 2019-09-28
#' license: See LICENSE file.
#' copyright: 2019, The Alan Turing Institute
#' ---

library(argparse)
library(changepoint)

load.utils <- function() {
    # get the name of the current script so we can load utils.R (yay, R!)
    cmd.args <- commandArgs(trailingOnly=F)
    file.arg <- "--file="
    this.script <- sub(file.arg, "", cmd.args[grep(file.arg, cmd.args)])
    this.dir <- dirname(this.script)
    utils.script <- file.path(this.dir, 'utils.R')
    source(utils.script)
}

parse.args <- function() {
    parser <- ArgumentParser(description='Wrapper for changepoint package')
    parser$add_argument('-i', 
                        '--input',
                        help='path to the input data file',
                        required=TRUE
    )
    parser$add_argument('-o',
                        '--output',
                        help='path to the output file')
    parser$add_argument('-f',
                        '--func',
                        choices=c('mean', 'var', 'meanvar'), 
                        help='Function to call in the changepoint package',
                        required=TRUE
    )
    parser$add_argument('-p',
                        '--penalty',
                        choices=c(
                                  'None',
                                  'SIC',
                                  'BIC',
                                  'MBIC',
                                  'AIC',
                                  'Hannan-Quinn',
                                  'Asymptotic'
                                  ),
                        help='Choice of penalty in the cpt function',
                        default='MBIC'
    )
    parser$add_argument(
                        '-m',
                        '--method',
                        choices=c('AMOC', 'PELT', 'SegNeigh', 'BinSeg'),
                        help="Choice of method in the cpt function",
                        default='AMOC'
    )
    parser$add_argument(
                        '-t',
                        '--test-statistic',
                        choices=c('Normal', 'CUSUM', 'CSS', 'Gamma',
                                  'Exponential', 'Poisson'),
                        help="Test statistic to use",
                        default='Normal'
    )
    parser$add_argument('-Q',
                        '--max-cp',
                        help='Maximum number of change points',
                        choices=c('max', 'default'),
                        default='max')
    return(parser$parse_args())
}

main <- function()
{
    args <- parse.args()

    # load the data
    data <- load.dataset(args$input)

    n.obs <- data$original$n_obs

    # get the parameter list
    defaults <- list()
    # we set this to the maximum because we have no a priori knowledge of the 
    # maximum number of change points we expect.
    if (args$method == 'BinSeg' || args$method == 'SegNeigh') {
        if (args$max_cp == 'max')
            defaults$Q <- n.obs/2 + 1
        else
            defaults$Q <- 5
    }
    if (args$penalty == "Asymptotic")
        defaults$pen.value <- 0.05
    else
        defaults$pen.value <- 0 # not used for other penalties
    params <- make.param.list(args, defaults)

    if (args$func == "mean") {
        cpt.func <- cpt.mean
    } else if (args$func == "var") {
        cpt.func <- cpt.var
    } else if (args$func == "meanvar") {
        cpt.func <- cpt.meanvar
    }

    if (data$original$n_dim > 1) {
        # changepoint package can't handle multidimensional data
        exit.error.multidim(data$original, args, params)
    }

    vec <- as.vector(data$mat)
    start.time <- Sys.time()

    # call the appropriate function with the specified parameters
    result <- tryCatch({
        locs <- cpt.func(vec,
                 penalty=params$penalty,
                 pen.value=params$pen.value,
                 method=params$method,
                 test.stat=params$test_statistic,
                 Q=params$Q,
                 class=FALSE
        )
        list(locations=locs, error=NULL)
    }, error=function(e) {
        return(list(locations=NULL, error=e$message))
    })
    stop.time <- Sys.time()
    runtime <- difftime(stop.time, start.time, units="secs")

    if (!is.null(result$error)) {
        exit.with.error(data$original, args, params, result$error)
    }

    # convert indices to 0-based indices.
    if (params$method == 'AMOC') {
        locations <- c(result$locations[1]) - 1
        names(locations) <- NULL
        locations <- as.list(locations)
    } else {
        if (is.list(result$locations)) {
            result$locations <- result$locations$cpts
        }
        locations <- as.list(result$locations - 1)
    }

    exit.success(data$original, args, params, locations, runtime)
}

load.utils()
main()
