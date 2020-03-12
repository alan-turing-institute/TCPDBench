#' ---
#' title: Utilities shared between R code
#' author: G.J.J. van den Burg
#' date: 2019-09-29
#' license: See the LICENSE file.
#' copyright: 2019, The Alan Turing Institute
#' ---

library(RJSONIO)

printf <- function(...) invisible(cat(sprintf(...)));

load.dataset <- function(filename)
{
    data <- fromJSON(filename)

    # reformat the data to a data frame with a time index and the data values
    tidx <- data$time$index
    exp <- 0:(data$n_obs - 1)
    if (all(tidx == exp) && length(tidx) == length(exp)) {
        tidx <- NULL
    } else {
        tidx <- data$time$index
    }

    mat <- NULL

    for (j in 1:data$n_dim) {
        s <- data$series[[j]]
        v <- NULL
        for (i in 1:data$n_obs) {
            val <- s$raw[[i]]
            if (is.null(val)) {
                v <- c(v, NA)
            } else {
                v <- c(v, val)
            }
        }
        mat <- cbind(mat, v)
    }

    # We normalize to avoid issues with numerical precision.
    mat <- scale(mat)

    out <- list(original=data,
                time=tidx,
                mat=mat)
    return(out)
}

prepare.result <- function(data, data.filename, status, error,
                           params, locations, runtime) {
    out <- list(error=NULL)
    cmd.args <- commandArgs(trailingOnly=F)

    # the full command used
    out$command <- paste(cmd.args, collapse=' ')

    # get the name of the current script
    file.arg <- "--file="
    out$script <- sub(file.arg, "", cmd.args[grep(file.arg, cmd.args)])

    # hash of the script
    script.hash <- tools::md5sum(out$script)
    names(script.hash) <- NULL
    out$script_md5 <- script.hash

    # hostname of the machine
    hostname <- Sys.info()['nodename']
    names(hostname) <- NULL
    out$hostname <- hostname

    # dataset name
    out$dataset <- data$name

    # dataset hash
    data.hash <- tools::md5sum(data.filename)
    names(data.hash) <- NULL
    out$dataset_md5 <- data.hash

    # status of running the script
    out$status <- status

    # error (if any)
    if (!is.null(error))
        out$error <- error

    # parameters used
    out$parameters <- params

    # result
    out$result <- list(cplocations=locations, runtime=runtime)

    return(out)
}

make.param.list <- function(args, defaults)
{
    params <- defaults

    args.copy <- args
    args.copy['input'] <- NULL
    args.copy['output'] <- NULL

    params <- modifyList(params, args.copy)
    return(params)
}

dump.output <- function(out, filename) {
    json.out <- toJSON(out, pretty=T)
    if (!is.null(filename))
        write(json.out, filename)
    else
        cat(json.out, '\n')
}

exit.error.multidim <- function(data, args, params) {
    status = 'SKIP'
    error = 'This method has no support for multidimensional data.'
    out <- prepare.result(data, args$input, status, error, params, NULL, NA)
    dump.output(out, args$output)
    quit(save='no')
}

exit.with.error <- function(data, args, params, error) {
    status = 'FAIL'
    out <- prepare.result(data, args$input, status, error, params, NULL, NULL)
    dump.output(out, args$output)
    quit(save='no')
}

exit.success <- function(data, args, params, locations, runtime) {
    status = 'SUCCESS'
    error = NULL
    out <- prepare.result(data, args$input, status, error, params, locations,
                          runtime)
    dump.output(out, args$output)
}
