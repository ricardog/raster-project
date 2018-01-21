#!/bin/bash

set -e
year=$1
oyear=$(printf "%04d" ${year})
scenario='historical'
export DATA_ROOT=${DATA_ROOT:=/data}
export OUTDIR=${OUTDIR:=/out}
model_dir=/vagrant/models/sam/2018-01-05/

## Generate the four base layers.
for what in sr cs-sr ab cs-ab hpd; do
    printf "  %-6s :: %s\n" ${what} ${year}
    ./ipbes-project.py -m ${model_dir} ${what} ${scenario} ${year} > /dev/null
done

## Combine base layers into BII layer.
for what in sr ab; do
    if [ "${what}" == "ab" ]; then
	v1="Abundance"
	v2="Ab"
    else
	v1="Richness"
	v2="SR"
    fi

    rio clip ${OUTDIR}/luh2/${scenario}-CompSim${v2}-${oyear}.tif \
	--like ${OUTDIR}/luh2/${scenario}-${v1}-${oyear}.tif \
	--output ${OUTDIR}/luh2/${scenario}-CompSim${v2}-${oyear}.tif

    rio calc --co "COMPRESS=lzw" --co "PREDICTOR=2" --masked \
	-t float32 "(* (read 1 1) (read 2 1))" \
	-o ${OUTDIR}/luh2/${scenario}-BII${v2}-${oyear}.tif \
	${OUTDIR}/luh2/${scenario}-${v1}-${oyear}.tif \
	${OUTDIR}/luh2/${scenario}-CompSim${v2}-${oyear}.tif
done
