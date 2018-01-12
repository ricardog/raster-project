#!/bin/bash

set -e
year=$1
scenario='historical'
export DATA_ROOT=${DATA_ROOT:=/Users/ricardog/src/eec/data}
export OUTDIR=${OUTDIR:=/Users/ricardog/src/eec/predicts/playground/ds}

## Generate the four base layers.
for what in sr cs-sr ab cs-ab; do
    printf "  %-6s :: %s\n" ${what} ${year}
    ./ipbes-project.py -m ~/src/eec/predicts/models/sam/2018-01-05/ \
		       ${what} ${scenario} ${year} > /dev/null
done

## Combine base layers into BII layer.
for what in sr ab; do
    if [ "${what}" == "ab" ]; then
	v1="Abundance"
	v2="Ab"
	v3="npp"
    else
	v1="Richness"
	v2="SR"
	v3="vertebrate-richness"
    fi

    tempweight=$(basename $0)
    TMPFILE=$(mktemp -t ${tempweight})
    if [ $? -ne 0 ]; then
	echo "$0: Can't create temp file, exiting..."
        exit 1
    fi

    rio clip ${OUTDIR}/luh2/${scenario}-CompSim${v2}-${year}.tif \
	--like ${OUTDIR}/luh2/${scenario}-${v1}-${year}.tif \
	--output ${OUTDIR}/luh2/${scenario}-CompSim${v2}-${year}.tif

    rio clip ${OUTDIR}/luh2/${v3}.tif \
	--like ${OUTDIR}/luh2/${scenario}-${v1}-${year}.tif \
	--output ${TMPFILE}
    
    rio calc --co "COMPRESS=lzw" --co "PREDICTOR=2" --masked \
	-t float32 "(* (read 1 1) (read 2 1) (read 3 1))" \
	-o ${OUTDIR}/luh2/${scenario}-BII${v2}-${year}.tif \
	${OUTDIR}/luh2/${scenario}-${v1}-${year}.tif \
	${OUTDIR}/luh2/${scenario}-CompSim${v2}-${year}.tif \
	${TMPFILE}
done
