.SUFFIXES:

OUTDIR := ../ds/lui

MAKETARGET = ${MAKE} --no-print-directory -C $@ -f ${CURDIR}/Makefile \
		SRCDIR=${CURDIR} ${MAKECMDGOALS}

.PHONY: ${OUTDIR}
$(OUTDIR):
	+@[ -d $@ ] || mkdir -p $@
	+@$(MAKETARGET)

Makefile : ;
%.mk :: ;

% :: $(OUTDIR) ; :

.PHONY: clean
clean:
	rm -rf $(OUTDIR)
