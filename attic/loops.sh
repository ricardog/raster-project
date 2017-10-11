#!/bin/bash

for year in $(seq 1950 60 2010); do
    for lu in cropland pasture plantation_pri primary secondary urban; do
	echo ./luh5-test.py -m ./tmp ab ${lu} historical ${year}
	./luh5-test.py -m ./tmp ab ${lu} historical ${year}
	for intensity in minimal light intense; do
	    echo ./luh5-test.py ab ${lu}_${intensity} historical ${year}
	    ./luh5-test.py -m ./tmp ab ${lu}_${intensity} historical ${year}
	done
    done
done
