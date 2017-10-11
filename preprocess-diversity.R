#!/usr/bin/env Rscript

##
## "Parse" command-line arguments
##
library(argparser, quietly=TRUE)
p <- arg_parser("Pre-process PREDICTS diversity data")
p <- add_argument(p, "--input", help="diversity rds file to read")
p <- add_argument(p, "--output", help="diversity rds file to write")
argv <- parse_args(p)

if (is.na(argv$input) || is.na(argv$output)) {
    cat("failing\n")
    print(p)
    stop()
}

##
## Read the diversity DB
##
diversity <-  readRDS(argv$input)

##
## Correct sampling effort and merge sites
##
library(yarg, quietly = TRUE)
cat("***\nCorrecting sampling effort\n")
diversity <- CorrectSamplingEffort(diversity)
cat("***\nMerging sites\n")
if ('Sample_midpoint' %in% names(diversity)) {
    merge.extra <- c('Sample_midpoint')
} else {
    merge.extra <- c()
}
if ('Wilderness_area' %in% names(diversity)) {
    match.extra <- c('Wilderness_area')
} else {
    match.extra <- c()
}
diversity <- MergeSites(diversity, merge.extra = merge.extra,
                        match.extra = match.extra)
saveRDS(diversity, file = argv$output)

