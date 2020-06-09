#!/bin/bash -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
YEARS=2020:2061:5
for model in base ageclass nohpd nohpd-ageclass; do
    echo ${model}
    model_dir=$HOME/src/eec/predicts/models/dasgupta/2020-05-26/${model}
    for scene in base early late_23 late_26 late_29 ; do
	echo ${scene}
	${DIR}/dasgupta.py project -m ${model_dir} -f ab ${scene} ${YEARS}
	${DIR}/dasgupta.py project -m ${model_dir} ab ${scene} ${YEARS}

	${DIR}/dasgupta.py project -m ${model_dir} -f cs-ab ${scene} ${YEARS}
	${DIR}/dasgupta.py project -m ${model_dir} cs-ab ${scene} ${YEARS}

	${DIR}/dasgupta.py combine ab ${scene} ${YEARS}
	${DIR}/dasgupta.py combine cs-ab ${scene} ${YEARS}
	${DIR}/dasgupta.py combine bii ${scene} ${YEARS}
    done
    ${DIR}/summarize.py --npp ${OUTDIR}/rcp/npp.tif

    mkdir -p ${model}-model
    mv Figure-1.png vivid-summary.csv ${model}-model

    mkdir -p ${OUTDIR}/rcp/${model}-model
    mv ${OUTDIR}/rcp/dasgupta-*-BIIAb-20*.tif ${OUTDIR}/rcp/${model}-model
    mv ${OUTDIR}/rcp/dasgupta-*-Abundance-20*.tif ${OUTDIR}/rcp/${model}-model
    mv ${OUTDIR}/rcp/dasgupta-*-CompSimAb-20*.tif ${OUTDIR}/rcp/${model}-model
done
