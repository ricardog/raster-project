#!/usr/bin/env Rscript

##
## "Parse" command-line arguments
##
library(argparser, quietly=TRUE)
p <- arg_parser("Run PREDICTS land-use intensity models")
p <- add_argument(p, "--type",
                  help="Type of land-use to project, e.g. cropland, pasture")
p <- add_argument(p, "--model-dir",
                  help="Directory where to find the model file")
p <- add_argument(p, "--hpd",
                  help="Path to baseline human population density raster")
p <- add_argument(p, "--projected-hpd",
                  help="Path to projected human population density raster")
p <- add_argument(p, "--hpd-band", default=1,
                  help="Select band in human population raster")
p <- add_argument(p, "--lu",
                  help="Path to baseline land use raster")
p <- add_argument(p, "--projected-lu",
                  help="Path to projected land use raster")
p <- add_argument(p, "--lui",
                  help="Path to the baseline land use intensity raster")
p <- add_argument(p, "--un-subregion", help="Path to UN subregions map")
p <- add_argument(p, "--output", help="Name of output raster")
argv <- parse_args(p)
if (is.na(argv$type)) {
    print(p)
    stop("Please speficy the land-use type, e.g. cropland, pasture, etc.")
}
if (is.na(argv$hpd)) {
    print(p)
    stop("Please speficy path to baseline human population density raster")
}
if (is.na(argv$projected_hpd)) {
    print(p)
    stop("Please speficy path to projected human population density raster")
}
if (is.na(argv$lu)) {
    print(p)
    stop("Please speficy path to baseline land use raster")
}
if (is.na(argv$projected_lu)) {
    print(p)
    stop("Please speficy path to projected land use raster")
}
if (is.na(argv$lui)) {
    print(p)
    stop("Please specify the baseline land use intensity raster")
}
if (is.na(argv$un_subregion)) {
    print(p)
    stop("Please provide the path to the UN subregion raster")
}
if (is.na(argv$output)) {
    print(p)
    stop("Please provide the name of the output raster")
}

##
## Load models and rasters
##
model <- readRDS(paste(argv$model_dir, '/', argv$type, '.rds', sep=''))
library(rgdal)
hpd.baseline <- readGDAL(argv$hpd)
hpd.projected <- readGDAL(argv$projected_hpd, band=argv$hpd_band)
lu.baseline <- readGDAL(argv$lu)
lu.projected <- readGDAL(argv$projected_lu)
lui <- readGDAL(argv$lui)
un.subregion <- readGDAL(argv$un_subregion)

lui.minimal <- lu.baseline
lui.minimal$band1 <- lui$band1
lui.light <- lu.baseline
lui.light$band1 <- lui$band2
lui.intense <- lu.baseline
lui.intense$band1 <- lui$band3

##
## Load dovedale
##
library(dovedale)
projection <- predict_lu_intensity(argv$type, model, hpd.baseline,
                                   hpd.projected, lu.baseline, lu.projected,
                                   lui.minimal, lui.light, lui.intense,
                                   un.subregion)
out <- lu.baseline
out$band1 <- projection$minimal$band1
out$band2 <- projection$light$band1
out$band3 <- projection$intense$band1

##
## Set projection for output raster based on hpd projection
##
library(raster)
srs <- projection(hpd.baseline)
out$band1[out$band1 == "Nan"] <- NA
out$band2[out$band2 == "Nan"] <- NA
out$band3[out$band3 == "Nan"] <- NA
projection(out) <- srs
writeGDAL(out, argv$output, drivername='GTiff', type="Float32", mvFlag=-9999)
