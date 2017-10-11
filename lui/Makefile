
ifndef DATA_ROOT
  ifeq ($(shell hostname),vagrant)
    $(warn Setting DATA_ROOT to /data)
    DATA_ROOT := /data
  else
    $(error Please set DATA_ROOT)
  endif
endif

ifndef SRCDIR
export ARCHIVE := $(abspath ${DATA_ROOT}/LUIdata.zip)
export UN_SUB := $(abspath ${DATA_ROOT}/un_subregions)
export ICEWR := $(abspath ${DATA_ROOT}/rcp1.1/gicew.1700.txt)
include target.mk
else

VPATH = ${SRCDIR}
define name
$(strip $(word 2, $(subst -, ,$(basename ${1}))))
endef

define rasterize
	@echo gdal_rasterize ${2} ${3}
	@gdal_rasterize -q -a_nodata -9999 -init -9999 -a ${1} -ot Float32 -tr 0.5 0.5 -te -180 -90 180 90 -co "COMPRESS=lzw" -co "PREDICTOR=2" ${2} ${3}
endef

#LU_TYPES := $(notdir $(basename $(wildcard ${SRCDIR}/*.vrt)))
LU_TYPES := cropland pasture primary secondary urban
LUI_TYPES := minimal light intense
PATTERNS := $(addsuffix .tiff, $(addprefix %-, ${LUI_TYPES}))
ALL := $(foreach type, ${LUI_TYPES}, $(addsuffix -${type}.tif, ${LU_TYPES}))

all: $(addsuffix .tif, ${LU_TYPES}) $(addsuffix -recal.tif, ${LU_TYPES})
	@echo Need to make $(addsuffix .tif, ${LU_TYPES})
	@echo LU types: ${LU_TYPES}

%.vrt: template.vrt.in
	@sed -e 's@%archive%@${ARCHIVE}@; s@%type%@$(notdir $(basename $@))@' \
		$< > $@

%-minimal.tif: %.vrt
	@echo $(call name,$@)
	$(call rasterize, $(call name, $@), $<, $@)

%-light.tif: %.vrt
	@echo $(call name,$@)
	$(call rasterize, $(call name, $@), $<, $@)

%-intense.tif: %.vrt
	@echo $(call name,$@)
	$(call rasterize, $(call name, $@), $<, $@)

%.tif: %-minimal.tif %-light.tif %-intense.tif
	@echo gdal_merge.py -o $@ $^
	@gdal_merge.py -q -o $@ -of GTiff -co "COMPRESS=lzw" -co "PREDICTOR=2"\
		-separate -a_nodata -9999 -init -9999 -n -9999 $^

%-recal.tif: %.tif
	${SRCDIR}/../lu-recalibrate.R \
		-m ${SRCDIR}/../out/_d5ed9724c6cb2c78b59707f69b3044e6/ \
		-t $(basename $^) --hpd ${SRCDIR}/../gluds00aghd.vrt \
		-l ../lu/rcp/hyde/$(basename $^)_1999.tif --lui $^ \
		-u ${UN_SUB} --mask ${ICEWR} \
		-o $@

endif
