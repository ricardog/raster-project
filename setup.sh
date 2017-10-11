#!/usr/bin/bash

# Build R tools
pushd ../tools
./build.sh yarg
./build.sh roquefort
./build.sh dovedale
popd

# Create data directory 
mkdir -p ds
for subdir in rcp luh2 1km vector lu/rcp lui; do
    mkdir -p ds/${res}
done

# Extract a couple of years from the RCP HYDE scenario tarball
project land_use rcp extract ${DATA_ROOT}/rcp1.1/LUHa_u2.v1.tgz  --years 1999:2001 
project land_use rcp project hyde 1999:2001

## Fit land use intensity models
make lui-models

## Generate road, population density rasters
make -C ds -f Makefile.ds

## Generate and recalibrate land use intensity rasters
make -C lui

## Generate secondary age distribution
./secd-dist.py --start-index 1050 --outdir ds/luh2

## Generate LUH2 generated land use types
./gen_luh2.py

## Generate SPS rasters
gen_sps

