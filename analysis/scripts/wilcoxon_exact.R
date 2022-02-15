#' ---
#' title: Utility for exact Wilcoxon signed-rank test
#' author: G.J.J. van den Burg
#' date: 2021-04-07
#' license: MIT
#' copyright: 2021, The Alan Turing Institute
#' ---

library(argparse)
library(exactRankTests)

parse.args <- function() {
  parser <- ArgumentParser(description='Compute exact Wilcoxon signed-rank test')
  parser$add_argument('-i', '--input', help='Input CSV file', required=T)
  return(parser$parse_args())
}

main <- function()
{
  args <- parse.args()
  data <- read.csv(args$input)

  x <- data$x
  y <- data$y

  W <- wilcox.exact(x, y, alternative="two.sided", paired=T, exact=T)
  cat(sprintf("%.16f\n", W$p.value))
  quit(save='no')
}

main()
