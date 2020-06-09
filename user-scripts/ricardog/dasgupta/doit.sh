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
MODELS="base ageclass nohpd nohpd-ageclass"
SCENARIOS="base early late_125 late_15 late_175 late_20 late_23 late_26 late_29"
YEARS=2020:2061:5
ODIR=${OUTDIR:-/out}

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
    if [[ -d /out ]]; then
	model_dir=/out/models/dasgupta/2020-05-26/${model}
    else
	model_dir=$HOME/src/eec/predicts/models/dasgupta/2020-05-26/${model}
    fi
    for scene in ${SCENARIOS} ; do
	printf "%s %s\n" "${scene}" "${YEARS} ${model}"
    done | xargs -P ${JOBS} -n 1 -L 1 ${DIR}/run.sh
    ${DIR}/summarize.py --npp ${ODIR}/rcp/npp.tif --indicator BIIAb

    mkdir -p ${model}-model
    mv Figure-1.png vivid-summary.csv ${model}-model
    mv mean-bii-*.png ${model}-model

    mkdir -p ${ODIR}/rcp/${model}-model
    mv ${ODIR}/rcp/dasgupta-*-BIIAb-20*.tif ${ODIR}/rcp/${model}-model
    mv ${ODIR}/rcp/dasgupta-*-Abundance-20*.tif ${ODIR}/rcp/${model}-model
    mv ${ODIR}/rcp/dasgupta-*-CompSimAb-20*.tif ${ODIR}/rcp/${model}-model
done
