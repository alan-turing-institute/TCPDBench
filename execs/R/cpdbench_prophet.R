#' ---
#' title: Wrapper for the Prophet package in TCPDBench
#' author: G.J.J. van den Burg
#' date: 2019-09-30
#' license: See the LICENSE file.
#' copyright: 2019, The Alan Turing Institute
#' ---

library(argparse)
library(prophet)
library(lubridate)

NO.DATETIME <- c('scanline_126007', 'scanline_42049', 'well_log',
                 'quality_control_1', 'quality_control_2', 'quality_control_3',
                 'quality_control_4', 'quality_control_5')

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
    parser <- ArgumentParser(description='Wrapper for Prophet package')
    parser$add_argument('-i', 
                        '--input',
                        help='path to the input data file',
                        required=TRUE
    )
    parser$add_argument('-o',
                        '--output',
                        help='path to the output file'
    )
    parser$add_argument('-N',
                        '--Nmax',
                        help='maximum number of changepoints',
                        choices=c('default', 'max')
    )
    return(parser$parse_args())
}

frac.to.dt <- function(raw) {
    out <- c()
    for (i in 1:length(raw)) {
        replaced <- gsub('-', '.', raw[i]);
        number <- as.double(replaced)
        year <- floor(number)
        remainder <- number - year
        begin <- as_datetime(paste(year, '-01-01', sep=''))
        end <- as_datetime(paste(year+1, '-01-01', sep=''))
        offset <- remainder * (end - begin)
        dt <- begin + offset
        # you'd think there'd be a well-documented easy-to-find function for 
        # this
        datepart <- date(dt)
        timepart <- sprintf("%02d:%02d:%02d", hour(dt), minute(dt),
                            round(second(dt)))
        iso <- paste(datepart, timepart, sep=' ')
        out <- c(out, iso)
    }
    return(out)
}

preprocess.data <- function(data)
{
    if ("format" %in% names(data$original$time)) {
        if (data$original$time$format == "%Y-%m-%d %H:%M:%S") {
            tidx <- data$original$time$raw
        } else if (data$original$time$format == "%Y-%m-%d") {
            tidx <- data$original$time$raw
        } else if (data$original$time$format == "%Y-%m") {
            tidx <- paste(data$original$time$raw, '-01', sep='')
        } else if (data$original$time$format == "%Y") {
            tidx <- paste(data$original$time$raw, '-01-01', sep='')
        } else if (data$original$time$format == "%Y-%F") {
            tidx <- frac.to.dt(data$original$time$raw)
        } else {
            stop(cat("Unknown time format: ", data$original$time$format, '\n'))
        }
    } else {
        if (data$original$name == 'bank') {
            # bank is daily data
            dt <- as_date("2019-01-01")
            tidx <- c(dt)
            for (i in 2:data$original$n_obs) {
                dt <- dt + ddays(1)
                tidx <- c(tidx, dt)
            }
        } else if (data$original$name == 'bee_waggle') {
            # bee_waggle is seconds data (I believe)
            dt <- as_date("2019-01-01 00:00:00")
            tidx <- c(dt)
            for (i in 2:data$original$n_obs) {
                dt <- dt + dseconds(1)
                tidx <- c(tidx, dt)
            }
        } else if (data$original$name %in% NO.DATETIME) {
            # these datasets have no corresponding time axis, so we disable 
            # periodicity in prophet for fairness.
            # We'll make it "daily", because prophet needs a datetime format
            dt <- as_date("2019-01-01")
            tidx <- c(dt)
            for (i in 2:data$original$n_obs) {
                dt <- dt + ddays(1)
                tidx <- c(tidx, dt)
            }
        } else {
            stop(cat("Unhandled time series: ", data$original$name, '\n'))
        }
    }

    raw <- as.vector(data$mat)

    df <- data.frame(ds=tidx, y=raw)

    return(df)
}

main <- function() {
    args <- parse.args()
    data <- load.dataset(args$input)

    defaults <- list()
    # we want to allow change points throughout the entire range of the series
    defaults$changepoint.range <- 1
    # threshold used in add_changepoints_to_plot
    defaults$threshold <- 0.01
    defaults$yearly.seasonality <- 'auto'
    defaults$weekly.seasonality <- 'auto'
    defaults$daily.seasonality <- 'auto'

    if (args$Nmax == 'default')
        args$Nmax <- 25
    else
        args$Nmax <- data$original$n_obs - 1

    if (data$original$name %in% NO.DATETIME) {
        defaults$yearly.seasonality <- FALSE
        defaults$weekly.seasonality <- FALSE
        defaults$daily.seasonality <- FALSE
    }

    params <- make.param.list(args, defaults)

    if (data$original$n_dim > 1) {
        # package doesn't handle multidimensional data
        exit.error.multidim(data$original, args, params)
    }

    df <- preprocess.data(data)

    start.time <- Sys.time()
    result <- tryCatch({
        model <- prophet(df, changepoint.range=params$changepoint.range, 
                         n.changepoints=params$Nmax,
                         yearly.seasonality=params$yearly.seasonality,
                         weekly.seasonality=params$weekly.seasonality,
                         daily.seasonality=params$daily.seasonality
        )
        threshold <- params$threshold
        cpt <- model$changepoints[abs(model$params$delta) >= threshold]
        cpt <- as.character(as.POSIXct(cpt))
        locs <- match(cpt, as.character(df$ds))
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
