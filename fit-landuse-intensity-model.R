#!/usr/bin/env Rscript

##
## "Parse" command-line arguments
##
library(argparser, quietly=TRUE)
p <- arg_parser("Run PREDICTS land-use intensity models")
p <- add_argument(p, "--type", help="Type of land-use")
p <- add_argument(p, "--zip", help="Path to zip file containing land-use .csv files")
argv <- parse_args(p)
if (is.na(argv$type)) {
    print(p)
    stop("Please speficy the land-use type.")
}
if (is.na(argv$zip)) {
    print(p)
    stop("Please provide the path to the zip file with the .csv files.")
}

##
## Run the model
##
library(dovedale, quietly = TRUE)
data <- read.csv(unz(argv$zip, paste(argv$type, ".csv", sep = "")), header=TRUE)
models <- model_lu_intensity2(argv$type, data)
lightModel <- models$light
intenseModel <- models$intense
saveRDS(models, file = paste(argv$type, ".rds", sep=""))
