#!/bin/bash

set -euo pipefail

OUTDIR=$1

SG_URL="/vsicurl?max_retry=3&retry_delay=1&list_dir=no&url=https://files.isric.org/soilgrids/latest/data"


cd ${OUTDIR}

# Create one VRT per-depth.
gdalbuildvrt -separate soil-grid_0-5cm_mean.vrt $SG_URL"/bdod/bdod_0-5cm_mean.vrt" $SG_URL"/clay/clay_0-5cm_mean.vrt" $SG_URL"/phh2o/phh2o_0-5cm_mean.vrt" $SG_URL"/soc/soc_0-5cm_mean.vrt"

gdalbuildvrt -separate soil-grid_5-15cm_mean.vrt $SG_URL"/bdod/bdod_5-15cm_mean.vrt" $SG_URL"/clay/clay_5-15cm_mean.vrt" $SG_URL"/phh2o/phh2o_5-15cm_mean.vrt" $SG_URL"/soc/soc_5-15cm_mean.vrt"

gdalbuildvrt -separate soil-grid_15-30cm_mean.vrt $SG_URL"/bdod/bdod_15-30cm_mean.vrt" $SG_URL"/clay/clay_15-30cm_mean.vrt" $SG_URL"/phh2o/phh2o_15-30cm_mean.vrt" $SG_URL"/soc/soc_15-30cm_mean.vrt"


# Download the overview that is closest in size to LUH2 resolution.
gdal_translate -outsize 2489 907 -co "SPARSE_OK=YES" -co "TILED=YES" -co "COMPRESS=DEFLATE" -co "PREDICTOR=2" -co "BIGTIFF=YES" soil-grid_0-5cm_mean.vrt soil-grid_0-5cm_mean.tif

gdal_translate -outsize 2489 907 -co "SPARSE_OK=YES" -co "TILED=YES" -co "COMPRESS=DEFLATE" -co "PREDICTOR=2" -co "BIGTIFF=YES" soil-grid_5-15cm_mean.vrt soil-grid_5-15cm_mean.tif

gdal_translate -outsize 2489 907 -co "SPARSE_OK=YES" -co "TILED=YES" -co "COMPRESS=DEFLATE" -co "PREDICTOR=2" -co "BIGTIFF=YES" soil-grid_15-30cm_mean.vrt soil-grid_15-30cm_mean.tif


# Re-project and re-size the rasters (to 0.25°).
mkdir luh2
gdalwarp -t_srs EPSG:4326 -tr 0.25 0.25 -r average -dstnodata -32768 soil-grid_0-5cm_mean.tif luh2/soil-grid_0-5cm_mean.tif

gdalwarp -t_srs EPSG:4326 -tr 0.25 0.25 -r average -dstnodata -32768 soil-grid_5-15cm_mean.tif luh2/soil-grid_5-15cm_mean.tif

gdalwarp -t_srs EPSG:4326 -tr 0.25 0.25 -r average -dstnodata -32768 soil-grid_15-30cm_mean.tif luh2/soil-grid_15-30cm_mean.tif

