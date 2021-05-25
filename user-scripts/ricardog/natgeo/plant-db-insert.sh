#!/bin/bash

PG_HOST=192.168.178.63
PG_PORT=5432
DB=trees
PG_USER=postgis
PG_PASSWD=postgis
SRCDIR="/Volumes/Macintosh HD/Users/ricardog/datasets/planted-trees"

layer=aus_plant
ogr2ogr --config PG_USE_COPY YES -f "PostgreSQL" \
	PG:"host=${PG_HOST} port=${PG_PORT} dbname=${DB} user=${PG_USER} password=${PG_PASSWD}" \
	"${SRCDIR}"/plantations_v1_3_dl.gdb -nln trees ${layer}

for layer in arg_plant bra_plant chl_plant civ_plant usa_plant cmr_plant cod_plant col_plant cri_plant eu_plant gab_plant gha_plant gtm_plant hnd_plant idn_plant jpn_plant ken_plant khm_plant kor_plant lbr_plant lka_plant mex_plant mmr_plant mwi_plant mys_plant nga_plant ecu_plant nic_plant npl_plant nzl_plant pak_plant pan_plant per_plant phl_plant rwa_plant slb_plant tha_plant ury_plant ven_plant vnm_plant zaf_plant ind_plant; do
    echo ${layer}
    ogr2ogr --config PG_USE_COPY YES -f "PostgreSQL" \
	    PG:"host=${PG_HOST} port=${PG_PORT} dbname=${DB} user=${PG_USER} password=${PG_PASSWD}" \
	    "${SRCDIR}"/plantations_v1_3_dl.gdb -nln trees -append ${layer}
done
