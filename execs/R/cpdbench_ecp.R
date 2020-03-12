#' ---
#' title: Wrapper for ecp package in TCPDBench
#' author: G.J.J. van den Burg
#' date: 2019-09-29
#' license: See LICENSE file.
#' copyright: 2019, The Alan Turing Institute
#' ---

library(argparse)
library(ecp)

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
    parser <- ArgumentParser(description='Wrapper for ecp package')
    parser$add_argument('-i', 
                        '--input',
                        help='path to the input data file',
                        required=TRUE
    )
    parser$add_argument('-o',
                        '--output',
                        help='path to the output file'
    )
    parser$add_argument('-a',
                        '--algorithm',
                        help='algorithm to use',
                        choices=c('e.agglo', 'e.divisive', 'kcpa'),
                        required=TRUE
                        )
    parser$add_argument('--alpha',
                        type='double',
                        help='alpha parameter for agglo and divisive')
    parser$add_argument('--minsize',
                        help='minsize argument for e.divisive',
                        type='integer', default=30)
    parser$add_argument('-R', '--runs',
                        help='number of random permutations to use',
                        type='integer', default=199)
    parser$add_argument('--siglvl',
                        type='double',
                        help='Significance level to use for tests')
    # No examples are provided in the ecp package documentation about 
    # reasonable values for C, so we use 1 as default.
    parser$add_argument('-C', '--cost',
                        type='double',
                        help='cost to use in the kcpa algorithm',
                        default=1)
    parser$add_argument('-L', '--maxcp',
                        help='maximum number of cps in kcpa algorithm',
                        choices=c('max', 'default')
    )
    return(parser$parse_args())
}

main <- function() {
    args <- parse.args()

    # load the dataset
    data <- load.dataset(args$input)

    # copy defaults from the ecp package
    defaults <- list()
    if (args$algorithm == 'e.divisive') {
        defaults$k <- 'null'
    }
    if (args$algorithm == 'kcpa') {
        # Again, we don't want to limit the number of change points a priori, 
        # so set the maximum to the length of the series.
        if (args$maxcp == 'max')
            defaults$L <- data$original$n_obs
        else
            defaults$L <- 5 # following binseg and segneigh default
    }
    params <- make.param.list(args, defaults)

    start.time <- Sys.time()
    result <- tryCatch({
        if (args$algorithm == 'e.agglo') {
            out <- e.agglo(data$mat, alpha=params$alpha)
            locs <- out$estimates
        } else if (args$algorithm == 'e.divisive') {
            out <- e.divisive(data$mat, sig.lvl=params$siglvl, R=params$runs,
                              min.size=params$minsize, alpha=params$alpha)
            locs <- out$estimates
        } else {
            # kcpa
            out <- kcpa(data$mat, params$L, params$cost)
            locs <- out
        }
        list(locations=locs, error=NULL)
    }, error=function(e) {
        return(list(locations=NULL, error=e$message))
    })

    stop.time <- Sys.time()
    runtime <- difftime(stop.time, start.time, units='secs')

    if (!is.null(result$error))
        exit.with.error(data$original, args, params, result$error)

    # convert to 0-based indices
    locations <- as.list(result$locations - 1)

    exit.success(data$original, args, params, locations, runtime)
}

load.utils()
main()
