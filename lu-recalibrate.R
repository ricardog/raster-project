#!/usr/bin/env Rscript

##
## "Parse" command-line arguments
##
library(argparser, quietly=TRUE)
p <- arg_parser("Calibrate land-use intensity baseline")
p <- add_argument(p, "--type",
                  help="Type of land-use to project, e.g. cropland, pasture")
p <- add_argument(p, "--model-dir",
                  help="Directory where to find the model file")
p <- add_argument(p, "--hpd",
                  help="Path to baseline human population density raster")
p <- add_argument(p, "--lu",
                  help="Path to baseline land use raster")
p <- add_argument(p, "--lu-band",
                  help="Band of baseline land use raster")
p <- add_argument(p, "--lui",
                  help="Path to the baseline land use intensity raster")
p <- add_argument(p, "--un-subregion", help="Path to UN subregions map")
p <- add_argument(p, "--mask", help="Path to ice/water mask map")
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
if (is.na(argv$lu)) {
    print(p)
    stop("Please speficy path to baseline land use raster")
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
if (is.na(argv$mask)) {
    print(p)
    stop("Please provide the path to the ice/water mask raster")
}

if (!is.na(argv$lu_band)) {
    lu.band <- argv$lu_band
} else {
    lu.band <- 1
}

##
## Load models and rasters
##
model <- readRDS(paste(argv$model_dir, '/', argv$type, '.rds', sep=''))
library(rgdal)
hpd.baseline <- readGDAL(argv$hpd)
lu.baseline <- readGDAL(argv$lu, band=lu.band)
lui <- readGDAL(argv$lui)
un.subregion <- readGDAL(argv$un_subregion)

##
## Load dovedale
##
library(dovedale)
out <- calibrate_lu_intensity(argv$type, model, hpd.baseline,
                              lu.baseline, lui, un.subregion)
out$band1[out$band1 == "Nan"] <- NA
out$band2[out$band2 == "Nan"] <- NA
out$band3[out$band3 == "Nan"] <- NA

out$band1[lu.baseline$band1 == 0] <- 0
out$band2[lu.baseline$band1 == 0] <- 0
out$band3[lu.baseline$band1 == 0] <- 0

##
## Set projection for output raster based on hpd projection
##
library(raster)
icew <- raster(argv$mask)
srs <- projection(hpd.baseline)
projection(out) <- srs
masked <- raster::mask(stack(out), icew, maskvalue=1.0)
writeRaster(masked, argv$output, format='GTiff', NAflag=-9999,
            overwrite=TRUE, datatype = 'FLT4S')
## Setting the following options causes writeRaster() to fail
## options=c("COMPRESS=lzw", "PREDICTOR=2"))
