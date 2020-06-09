#!/bin/bash -e

scenario="$1"
indir=$DATA_ROOT/vivid/${scenario}/spatial_files

for land in crop past forestry primforest secdforest urban other; do
    gdal_translate -of GTiff -a_nodata -9999.0 -co COMPRESS=lzw -co \
		   PREDICTOR=3 -ot Float32 \
		   netcdf:${indir}/cell.land_0.5.nc:${land} \
		   ${indir}/${land}.tif
done
