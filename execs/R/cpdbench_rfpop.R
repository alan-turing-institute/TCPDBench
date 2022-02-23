#' ---
#' title: Wrapper for robust-fpop package in TCPDBench
#' author: G.J.J. van den Burg
#' date: 2019-09-30
#' license: See the LICENSE file.
#' copyright: 2019, The Alan Turing Institute
#' ---

library(argparse)
library(robseg)

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
    parser <- ArgumentParser(description='Wrapper for robseg package')
    parser$add_argument('-i', 
                        '--input',
                        help='path to the input data file',
                        required=TRUE
    )
    parser$add_argument('-o',
                        '--output',
                        help='path to the output file'
    )
    parser$add_argument('-l',
                        '--loss',
                        help='loss function to use',
                        choices=c('L1', 'L2', 'Huber', 'Outlier'),
                        required=TRUE
    )
    parser$add_argument('-P',
                        '--pen.value',
                        help='Penalty value (lambda = beta) to use',
                        default=NULL
    )
    parser$add_argument('-K',
                        '--lthreshold',
                        help='Parameter K in loss function, relative to sigma hat',
                        default=NULL
    )
    return(parser$parse_args())
}

main <- function() {
    args <- parse.args()
    data <- load.dataset(args$input)

    # copy the defaults from the robust-fpop repo and the JASA paper.
    defaults <- list()
    if (args$loss == 'Outlier') {
        defaults$lambda <- 2 * log(data$original$n_obs)
        defaults$lthreshold <- 3
    } else if (args$loss == 'Huber') {
        defaults$lambda <- 1.4 * log(data$original$n_obs)
        defaults$lthreshold <- 1.345
    } else if (args$loss == 'L1') {
        defaults$lambda <- log(data$original$n_obs)
    } else if (args$loss == 'L2') {
        defaults$lambda <- log(data$original$n_obs)
    }

    # Rename pen.value to lambda in args
    args$lambda <- args$pen.value
    args$pen.value <- NULL

    # Deal with supplying NULL from command line
    if (!is.null(args$lambda) && args$lambda == "NULL") {
      args["lambda"] <- list(NULL)
    }
    if (!is.null(args$lthreshold) && args$lthreshold == "NULL") {
      args["lthreshold"] <- list(NULL)
    }

    # If lambda/lthreshold are NULL, they should be dropped in favor of the 
    # defaults. Otherwise, they should be converted to doubles.
    if (is.null(args$lambda)) {
      args$lambda <- NULL
    } else {
      args$lambda <- as.double(args$lambda)
    }
    if (is.null(args$lthreshold)) {
      args$lthreshold <- NULL
    } else {
      args$lthreshold <- as.double(args$lthreshold)
    }

    params <- make.param.list(args, defaults)

    # With the L1/L2 penalties, lthreshold should never not be NULL at this 
    # point, as it is unused.
    if (params$loss == "L1" || params$loss == "L2")
      stopifnot(is.null(params$lthreshold))

    if (data$original$n_dim > 1) {
        # robseg package can't handle multidimensional data
        exit.error.multidim(data$original, args, params)
    }

    vec <- as.vector(data$mat)

    start.time <- Sys.time()

    # estimate the standard deviation as in the README of the robseg package.
    est.std <- mad(diff(vec)/sqrt(2))
    # and normalise the data with this. Note that this means that we don't need 
    # to scale lambda and the threshold by the estimated standard deviation.
    x <- vec / est.std

    result <- tryCatch({
        out <- Rob_seg.std(x=x,
                           loss=params$loss,
                           lambda=params$lambda,
                           lthreshold=params$lthreshold
                           )
        locs <- out$t.est
        list(locations=locs, error=NULL)
    }, error=function(e) {
        return(list(locations=NULL, error=e$message))
    })

    stop.time <- Sys.time()
    runtime <- difftime(stop.time, start.time, units='secs')

    if (!is.null(result$error)) {
        exit.with.error(data$original, args, params, result$error)
    }

    # convert indices to 0-based
    locations <- as.list(result$locations - 1)

    exit.success(data$original, args, params, locations, runtime)
}

load.utils()
main()
