#' ---
#' title: Wrapper for wbs package in TCPDBench
#' author: G.J.J. van den Burg
#' date: 2019-09-28
#' license: See the LICENSE file.
#' copyright: 2019, The Alan Turing Institute
#' ---

library(argparse)
library(wbs)

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
    parser <- ArgumentParser(description='Wrapper for wbs package')
    parser$add_argument('-i', 
                        '--input',
                        help='path to the input data file',
                        required=TRUE
    )
    parser$add_argument('-o',
                        '--output',
                        help='path to the output file'
    )
    parser$add_argument('-K', '--Kmax', choices=c('default', 'max'),
                        help='the maximum number of changepoints',
                        default='max')
    parser$add_argument('-p', '--penalty', choices=c('SSIC', 'BIC', 'MBIC'),
                        help='The penalty to use in WBS')
    parser$add_argument("-g", "--integrated", choices=c("true", "false"),
                        help="Whether to use integrated WBS or not")
    return(parser$parse_args())
}

main <- function() {
    args <- parse.args()

    # load the data
    data <- load.dataset(args$input)

    # copy defaults from the wbs package and set params
    defaults <- list(M=5000, rand.intervals=T)
    if (args$Kmax == 'default')
        args$Kmax <- 50
    else
        args$Kmax <- data$original$n_obs

    if (args$integrated == "true")
        args$integrated = TRUE
    else
        args$integrated = FALSE
    params <- make.param.list(args, defaults)

    if (data$original$n_dim > 1) {
        # wbs package doesn't handle multidimensional data
        exit.error.multidim(data$original, args, params)
    }

    vec <- as.vector(data$mat)
    start.time <- Sys.time()

    # We use the SSIC penalty as this is used in the WBS paper and is the 
    # default in the WBS package (for plot.wbs, for instance).

    result <- tryCatch({
        out <- wbs(vec, M=params$M, rand.intervals=params$rand.intervals,
                   integrated=params$integrated)
        cpt <- changepoints(out, Kmax=params$Kmax)
        if (params$penalty == "SSIC")
            locs <- cpt$cpt.ic$ssic.penalty
        else if (params$penalty == "BIC")
            locs <- cpt$cpt.ic$bic.penalty
        else if (params$penalty == "MBIC")
            locs <- cpt$cpt.ic$mbic.penalty
        locs <- sort(locs)
        list(locations=locs, error=NULL)
    }, error=function(e) {
        return(list(locations=NULL, error=e$message))
    })
    stop.time <- Sys.time()
    runtime <- difftime(stop.time, start.time, units='secs')

    if (!is.null(result$error)) {
        exit.with.error(data$original, args, params, result$error)
    }

    # convert to 0-based indices.
    locations <- as.list(result$locations - 1)

    exit.success(data$original, args, params, locations, runtime)
}

load.utils()
main()
