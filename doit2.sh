#!/bin/bash 

set -e
num_jobs=10
year0=2015
year1=2101
for_real=/bin/true

for dname in /data/luh2_v2/LUH2_v2f_SSP[0-9]_*; do
    dd=$(basename $dname)
    full=${dd,,}
    scenario=${full#luh2_v2f_}
    for what in sr cs-sr ab cs-ab bii-ab bii-sr; do
	if [[ ("$what" = "sr") || ("$what" = "cs-sr") || ( "$what" = "bii-sr") ]]; then
	    printf "%s /out/luh2/vertebrate-richness.tif %s %s %d:%d\n" "--vsr" "${what}" "${scenario}" "${year0}" "${year1}"
	else
	    printf "%s /out/luh2/npp.tif %s %s %d:%d\n" "--npp" "${what}" "${scenario}" "${year0}" "${year1}"
	fi
    done
done | xargs -P 10 -n 1 -l1 ./ipbes-summarize.py summary

