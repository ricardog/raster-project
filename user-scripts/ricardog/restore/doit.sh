#!/bin/bash -e

die() {
    printf '\033[1;31mERROR:\033[0m %s\n' "$@" >&2  # bold red
    exit 1
}

einfo() {
    printf '\n\033[1;36m> %s\033[0m\n' "$@" >&2  # bold cyan
}

usage() {
      echo "Usage: $0 [ -j JOBS ] [ -y YEARS ] [-m MODELS]" 1>&2 
}

JOBS=4
MODELS="base"
SCENARIOS="fc fc_no_cra fc_no_sfa idc_amz idc_imp_f3 no_fc"
YEARS=2015:2051:5
ODIR=${OUTDIR:-/mnt/predicts}

while getopts "p:m:y:h" options; do
    case "${options}" in
	p)
	    JOBS=${OPTARG}
	    re_isanum='^[0-9]+$'
	    if ! [[ $JOBS =~ $re_isanum ]] ; then
		die "JOBS must be a positive, whole number."
	    elif [ $JOBS -eq "0" ]; then
		die "JOBS must be greater than zero."
	    fi
	    ;;
	y)
	    YEARS=${OPTARG}
	    ;;
	m)
	    MODELS=${OPTARG}
	    ;;
	h)
	    usage
	    exit 1
	    ;;
	:)
	    die "-${OPTARG} requires an argument."
	    ;;
	*)
	    die "Unexpected argument"
	    ;;
    esac
done

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
for model in ${MODELS}; do
    einfo ${model}
    for scene in ${SCENARIOS} ; do
	printf "%s %s\n" "${scene}" "${YEARS} ${model}"
    done | xargs -P ${JOBS} -n 1 -L 1 ${DIR}/run.sh
    ${DIR}/summarize.py --npp ${ODIR}/rcp/npp.tif --indicator BIIAb

    mkdir -p ${model}-model
    mv Figure-1.png brazil-summary.csv ${model}-model

    for scene in ${SCENARIOS} ; do
	rio calc -t float32 -f GTiff --masked --overwrite \
	    --co COMPRESS=lzw --co PREDICTOR=3 \
	    "(- (read 1) (read 2))" \
	    ${ODIR}/rcp/restore/brazil/${scene}-BIIAb-2050.tif \
	    ${ODIR}/rcp/restore/brazil/${scene}-BIIAb-2015.tif \
	    -o ${model}-model/restore-${scene}-BIIAb-diff.tif
	rview -s ${model}-model/restore-${scene}-BIIAb-diff.png \
	      ${model}-model/restore-${scene}-BIIAb-diff.tif
    done
done
