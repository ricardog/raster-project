#!/bin/bash -e

DATA_ROOT=${DATA_ROOT:=/mnt/data}
DATA_DIR=${DATA_ROOT}//ccafs-climate

OUTDIR=${OUTDIR:=/mnt/predicts}
OUTPATH=${OUTDIR}/luh2/helen
for rcp in 2_6 4_5 6_0 8_5; do
    for decade in 2030 2050 2070 2080; do
	echo ${rcp} ${decade}
	./user-scripts/ricardog/helen/ccafs_process.py \
	 ${DATA_DIR}/giss_e2_r_rcp${rcp}_${decade}s_tmean_10min_r1i1p1_no_tile_asc.tif \
	 ${OUTPATH}/rcp${rcp}-${decade}s-tmean.tif
    done
done
