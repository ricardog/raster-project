#!/bin/bash -e

CS_PRE_F=magpie_baseline_pas_contrast_primary_minimal_age
AB_PRE_F=magpie_baseline_pas_age

CS_PRE_NF=magpie_baseline_pas_contrast_primary_minimal_
AB_PRE_NF=magpie_baseline_pas_

MODEL_DIR=${HOME}/src/eec/predicts/models/dasgupta/2020-06-02
MODEL=base

./attic/cs-plot.py -p "${CS_PRE_F}" ${MODEL_DIR}/${MODEL}/full_cs_f.rds \
		   -t --title "Tropical ${MODEL} model response curves" \
		   --clip -s ${MODEL}-model/cs-resp-tr.png

./attic/cs-plot.py -p "${CS_PRE_F}" ${MODEL_DIR}/${MODEL}/full_cs_f.rds \
		   --title "Temperate ${MODEL} model response curves" \
		   --clip -s ${MODEL}-model/cs-resp-te.png

./attic/cs-plot.py -p "${AB_PRE_F}" ${MODEL_DIR}/${MODEL}/full_ab_f.rds \
		   -t --title "Tropical ${MODEL} model response curves" \
		   --clip -s ${MODEL}-model/ab-resp-tr.png

./attic/cs-plot.py -p "${AB_PRE_F}" ${MODEL_DIR}/${MODEL}/full_ab_f.rds \
		   --title "Temperate ${MODEL} model response curves" \
		   --clip -s ${MODEL}-model/ab-resp-te.png

./attic/cs-plot.py -p "${AB_PRE_NF}" ${MODEL_DIR}/${MODEL}/ab_nf.rds \
		   --title "Non-forest ${MODEL} model response curve" \
		   --clip -s ${MODEL}-model/ab-resp-nf.png

./attic/cs-plot.py -p "${CS_PRE_NF}" ${MODEL_DIR}/${MODEL}/cs_nf.rds \
		   --title "Non-forest ${MODEL} model response curve" \
		   --clip -s ${MODEL}-model/cs-resp-nf.png
