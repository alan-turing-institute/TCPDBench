#' ---
#' title: Wrapper for ocp package in TCPDBench
#' author: G.J.J. van den Burg
#' date: 2019-10-05
#' license: See the LICENSE file.
#' copyright: 2019, The Alan Turing Institute
#' ---

library(argparse)
library(ocp)

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
    parser$add_argument('-l',
                        '--lambda',
                        help='lambda parameter for constant hazard function',
                        type='double',
                        default=100
                        )
    parser$add_argument('--prior-a',
                        help='Prior alpha for student-t',
                        type='double',
                        default=1)
    parser$add_argument('--prior-b',
                        help='Prior beta for student-t',
                        type='double',
                        default=1
    )
    parser$add_argument('--prior-k',
                        help='Prior kappa for student-t',
                        type='double',
                        default=1
    )

    return(parser$parse_args())
}

main <- function()
{
    args <- parse.args()
    data <- load.dataset(args$input)

    # set the defaults that we don't change
    defaults <- list(missPts="none",
                     cpthreshold=0.5, # unused by us
                     truncRlim=10^(-4),
                     minRlength=1,
                     maxRlength=10^4, # bigger than any of our datasets
                     minsep=1,
                     maxsep=10^4 # bigger than any of our datasets
                     )
    defaults$multivariate = data$original$n_dim > 1

    # combine defaults and cmd args
    params <- make.param.list(args, defaults)

    # define our hazard function with the lambda in the parameters
    hazard_func <- function(x, lambda) {
        const_hazard(x, lambda=params$lambda)
    }

    # we only use the gaussian model since the data is scaled
    model.params <- list(list(m=0, k=params$prior_k, a=params$prior_a,
                                  b=params$prior_b))

    start.time <- Sys.time()
    result <- tryCatch({
        fit <- onlineCPD(data$mat, oCPD=NULL, missPts=params$missPts,
                         hazard_func=hazard_func, 
                         probModel=list("gaussian"),
                         init_params=model.params,
                         multivariate=params$multivariate,
                         cpthreshold=params$cpthreshold,
                         truncRlim=params$truncRlim,
                         minRlength=params$minRlength,
                         maxRlength=params$maxRlength,
                         minsep=params$minsep,
                         maxsep=params$maxsep
                         )
        locs <- as.vector(fit$changepoint_lists$maxCPs[[1]])
        list(locations=locs, error=NULL)
    }, error=function(e) {
        return(list(locations=NULL, error=e$message))
    })
    stop.time <- Sys.time()
    runtime <- difftime(stop.time, start.time, units="secs")

    if (!is.null(result$error))
        exit.with.error(data$original, args, params, result$error)

    # convert indices to 0-based indices
    locations <- as.list(result$locations - 1)

    exit.success(data$original, args, params, locations, runtime)
}

load.utils()
main()
