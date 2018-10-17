#!/bin/bash

set -e
dir="/Volumes/Macintosh HD/Users/ricardog/tmp/katia"
islands=KS_layers/Islands_fromIgor_edited.shp
mainland=KS_layers/Mainland_fromIgor_edited.shp


gdal_rasterize -tap -init 0 -burn 1 -a FID_1 \
	       -ot Byte -tr 0.008333333333333 0.008333333333333 \
	       -co "COMPRESS=lzw" -co "PREDICTOR=2" \
	       "${dir}/${islands}" islands_fromIgor_edited.tif


gdal_rasterize -tap -init 0 -burn 1 -a FID_1 \
	       -ot Byte -tr 0.008333333333333 0.008333333333333 \
	       -co "COMPRESS=lzw" -co "PREDICTOR=2" \
	       "${dir}/${mainland}" mainland_fromIgor_edited.tif

