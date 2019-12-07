#!/bin/bash

for layer in aus_plant arg_plant bra_plant chl_plant civ_plant usa_plant cmr_plant cod_plant col_plant cri_plant eu_plant gab_plant gha_plant gtm_plant hnd_plant idn_plant jpn_plant ken_plant khm_plant kor_plant lbr_plant lka_plant mex_plant mmr_plant mwi_plant mys_plant nga_plant ecu_plant nic_plant npl_plant nzl_plant pak_plant pan_plant per_plant phl_plant rwa_plant slb_plant tha_plant ury_plant ven_plant vnm_plant zaf_plant ind_plant; do
    echo ${layer}
    ogr2ogr -f "PostgreSQL" PG:"host=bonobo.local port=5432 dbname=trees user=postgis password=postgis" ./plantations_v1_3_dl.gdb ${layer}
done

