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
	printf "%s %s %d:%d\n" "${what}" "${scenario}" "${year0}" "${year1}"
    done
done | xargs -P 10 -n 1 -l1 ./ipbes-summarize.py summary

