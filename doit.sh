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
    echo ${scenario}
    ## Generate the four base layers.
    for what in sr cs-sr ab cs-ab hpd; do
	printf "  %-6s :: %s:%s\n" ${what} ${year0} ${year1}
	if ${for_real}; then
	    echo > /dev/null
	    ./ipbes-project.py -p ${num_jobs} \
			       -m /vagrant/models/sam/2018-01-05/ \
			       ${what} ${scenario} ${year0}:${year1} > /dev/null
	fi
    done

    ## Combine base layers into BII layer.
    for what in sr ab; do
	if [ "${what}" == "ab" ]; then
	    v1="Abundance"
	    v2="Ab"
	else
	    v1="Richness"
	    v2="SR"
	fi
	for (( year=$year0; year<$year1; year++ )); do
	    ## Run num_jobs in parallel.
	    echo "-o /out/luh2/${scenario}-BII${v2}-${year}.tif /out/luh2/${scenario}-${v1}-${year}.tif /out/luh2/${scenario}-CompSim${v2}-${year}.tif"
	done
    done | xargs -P ${num_jobs} -n 1 -l1 rio calc \
		 --co "COMPRESS=lzw" --co "PREDICTOR=3" --masked \
		 -t float32 \
		 "(* (read 1 1) (read 2 1))"
done
