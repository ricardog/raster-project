#!/bin/bash

set -e

#function join_by { local IFS="$1"; shift; echo "$*"; }
function join_by { local d=$1; shift; echo -n "$1"; shift; printf "%s" "${@/#/$d}"; }

COMMONS=(Banana Cacao Coffee Eucalyptus Pine Rubber)
SIMPLE=("Oil Palm " "Oil Palm Mix" "Fruit Mix" "Rubber Mix" "Unknown"
	"Wood fiber / timber")

#REFERENCE=/Users/ricardog/src/eec/predicts/playground/ds/1km/un_codes-full.tif
#ICEWTR='zip:///Users/ricardog/src/eec/data/1km/ICE.zip!/ICE_1km_2005.bil'
#outdir=sdpt_1km

REFERENCE=/Users/ricardog/src/eec/predicts/playground/ds/luh2/un_codes-full.tif
ICEWTR='netcdf:/Users/ricardog/src/eec/data/luh2_v2/staticData_quarterdeg.nc:icwtr'
outdir=sdpt-qd

JOINED=$(join_by "', '" "${COMMONS[@]}")
NOT_IN=$(printf "common_name NOT IN ('%s')" "${JOINED}")
outdir=sdpt_qd

for common in "${COMMONS[@]}"; do
    echo "${common}"
    fname=$(echo ${common} | tr '[:upper:]' '[:lower:]')
    where_clause=$(printf "WHERE common_name='%s'" ${common})
    caffeinate ./plant_db.py -n 4 trees "${where_clause}" ${REFERENCE} \
	       ${outdir}/${fname}.tif
    ./partial-to-full.py ${outdir}/${fname}-full.tif \
			 ${outdir}/${fname}.tif "${ICEWTR}"
done

echo ""; echo ""; echo "";

for name in "${SIMPLE[@]}"; do
    echo ${name}
    if [ "${name}" = "Wood fiber / timber" ]; then
	fname=timber
    else
	fname=$(echo ${name} | tr '[:upper:]' '[:lower:]' | tr ' ' '_')
    fi
    where_clause=$(printf "WHERE species_simp='%s' AND %s" "${name}" "${NOT_IN}")
    caffeinate ./plant_db.py -n 4 trees "${where_clause}" ${REFERENCE} \
	       ${outdir}/${fname}.tif
    ./partial-to-full.py ${outdir}/${fname}-full.tif \
			 ${outdir}/${fname}.tif "${ICEWTR}"
done

