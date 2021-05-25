
ifndef DATA_ROOT
  ifeq ($(shell hostname),vagrant)
    $(warn Setting DATA_ROOT to /data)
    DATA_ROOT := /data
  else
    $(error Please set DATA_ROOT)
  endif
endif 
##
## Boilerplate
##
ifeq (,$(filter _%,$(notdir $(CURDIR))))
#DIVERSITY_DB := ../tools/yarg/data/diversity.rds
export DIVERSITY_DB := ${DATA_ROOT}/predicts/diversity-2017-02-06-03-36-23.rds
export HPD_DB := ${DATA_ROOT}/grump1.0/gluds00ag
export ROADS_DB := ${DATA_ROOT}/groads1.0/groads-v1-global-gdb/gROADS_v1.gdb
export LUI_DATA := $(abspath ${DATA_ROOT}/LUIdata.zip)

include target.mk
else
VPATH = ${SRCDIR}

##
## Rules
##
OS := $(shell uname -s)
ifeq (${OS},Darwin)
  TRUE := /usr/bin/true
  NOSLEEP := caffeinate -i 
else
  TRUE := /bin/true
  NOSLEEP := 
endif

all: sr-model.rds ab-model.rds lui-models

outdir:
	+@pwd

merged.rds: ${DIVERSITY_DB} ${SRCDIR}/preprocess-diversity.R
	@echo "Merging diversity data"
	@${SRCDIR}/preprocess-diversity.R --input $< --output $@

sites.csv: merged.rds ${SRCDIR}/get-sites.R
	@echo "Extracting geographic about sites"
	@${SRCDIR}/get-sites.R $< $@

sites.vrt: sites.vrt.in
	@cp $^ $@

hpd/sites.shp: sites.vrt sites.csv \
		${SRCDIR}/projections/scripts/extract_values.py
	@echo "Extracting human population density at sites"
	@ogr2ogr -f "ESRI Shapefile" -overwrite hpd $<
	@extract_values -nodata -9999 -f $@ ${HPD_DB}

roads/sites.shp: sites.vrt sites.csv ${SRCDIR}/projections/roads/groads.py
	@echo "Computing distance to a road"
	@ogr2ogr -f "ESRI Shapefile" -overwrite roads $<
	@project roads compute ${ROADS_DB} $@ 

# There are a couple of odd bits when running ogr2ogr:
#
# - It doesn't like it if the output file exists--even with the
#   -override flag.
#
# - It deletes sites.csv
#
# So, remove the output and move sites.csv out of the way.  Moveit back
# after ogr2ogr finishes.
%_sites.csv: %/sites.shp
	rm -f $@
	mv sites.csv foo.csv
	ogr2ogr -f CSV -overwrite $@ $<
	mv foo.csv sites.csv

site-div.rds: merged.rds hpd_sites.csv roads_sites.csv \
		${SRCDIR}/gen-site-data.R
	@echo "Generating site data file"
	${SRCDIR}/gen-site-data.R --diversity merged.rds --hpd hpd_sites.csv \
		--roads roads_sites.csv --out $@

sr-model.rds: site-div.rds ${SRCDIR}/fit-species-richness-model.R
	@echo "Generating species richness model"
	${NOSLEEP} ${SRCDIR}/fit-species-richness-model.R --site-data $< \
		--out $(basename $@)

ab-model.rds: site-div.rds ${SRCDIR}/fit-abundance-model.R
	@echo "Generating species abundance model"
	${NOSLEEP} ${SRCDIR}/fit-abundance-model.R --site-data $< \
		--out $(basename $@)

LU_TYPES = primary secondary cropland pasture urban
LUI_MODELS = $(addsuffix .rds, ${LU_TYPES})
${LUI_MODELS}: ${LUI_DATA} ${SRCDIR}/fit-landuse-intensity-model.R
	@echo "Fitting $(basename $(notdir $@)) land use intensity model"
	@${NOSLEEP} ${SRCDIR}/fit-landuse-intensity-model.R \
		-t $(basename $(notdir $@)) --zip ${LUI_DATA} \
		> $(addsuffix .log, $(basename $(notdir $@))) 2>&1

%.py: %.rds
	@echo "compiling $(basename $(notdir $@)) land use intensity module"
	@${NOSLEEP} r2py $(abspath $^)
	@python $@

lui-models: ${LUI_MODELS} ${LUI_MODELS:.rds=.py}

.PRECIOUS: sites.csv

.PHONY: all lui-models outdir

endif
