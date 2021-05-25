.SUFFIXES:

ifndef MD5
ifeq (${OS},Darwin)
  MD5 := $(shell md5 -q ${DIVERSITY_DB})
else
  MD5 := $(word 1, $(shell md5sum ${DIVERSITY_DB}))
endif
export MD5
endif

OUTDIR := out/_$(MD5)

MAKETARGET = ${MAKE} --no-print-directory -C $@ -f ${CURDIR}/Makefile \
		SRCDIR=${CURDIR} ${MAKECMDGOALS}

.PHONY: ${OUTDIR}
$(OUTDIR):
	+@[ -d $@ ] || mkdir -p $@
	+@$(MAKETARGET)

Makefile : ;
%.mk :: ;

% :: $(OUTDIR) ;

.PHONY: clean
clean:
	rm -rf $(OUTDIR)
