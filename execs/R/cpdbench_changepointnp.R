#' ---
#' title: Wrapper for changepoint.np package in TCPDBench
#' author: G.J.J. van den Burg
#' date: 2019-09-30
#' license: See LICENSE file.
#' copyright: 2019, The Alan Turing Institute
#' ---

library(argparse)
library(changepoint.np)

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
    parser <- ArgumentParser(description='Wrapper for changepoint.np package')
    parser$add_argument('-i', 
                        '--input',
                        help='path to the input data file',
                        required=TRUE
    )
    parser$add_argument('-o',
                        '--output',
                        help='path to the output file')
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
    parser$add_argument('-q',
                        '--nquantiles',
                        type='integer',
                        help='Number of quantiles to use',
                        default=10
    )
    return(parser$parse_args())
}

main <- function() {
    args <- parse.args()

    # load the data
    data <- load.dataset(args$input)

    # get the parameter list
    defaults <- list(method='PELT',
                     test.stat='empirical_distribution',
                     minseglen=1)
    params <- make.param.list(args, defaults)

    if (data$origina$n_dim > 1) {
        # changepoint.np package can't handle multidimensional data
        exit.error.multidim(data$original, args, params)
    }

    vec <- as.vector(data$mat)
    start.time <- Sys.time()

    result <- tryCatch({
        locs <- cpt.np(vec,
                       penalty=params$penalty,
                       method=params$method,
                       test.stat=params$test.stat,
                       minseglen=params$minseglen,
                       nquantiles=params$nquantiles,
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

    # convert indices to 0-based indices
    locations <- as.list(result$locations - 1)

    exit.success(data$original, args, params, locations, runtime)
}

load.utils()
main()
