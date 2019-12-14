FROM py-geospatial:latest

MAINTAINER Ricardo E. Gonzalez <ricardog@ricardog.com>

SHELL ["/bin/bash", "--login", "-c"]

USER rstudio
RUN mkdir -p ~/work
COPY --chown=rstudio:rstudio reqs.txt /home/rstudio/work/
COPY --chown=root:root jupyter-runner /usr/local/bin/jupyter
RUN cd /home/rstudio/work && \
	whoami && \
	. ~/.bashrc && \
	which pip && \
	pip install -r reqs.txt && \
	R -e "IRkernel::installspec()" && \
	sed -i.orig -e 's/from pysal.esda.mapclassify import/from pysal.viz.mapclassify import/' /home/rstudio/.pyenv/versions/3.6.3/lib/python3.6/site-packages/geopandas/plotting.py

COPY --chown=rstudio:rstudio Abundance.ipynb \
     do-hist-one.sh \
     do-hist2.sh \
     doit2.sh \
     do-hist.sh \
     doit.sh \
     environment.yml \
     gen_luh2.py \
     natgeo-project.py \
     ipbes-project.py \
     ipbes-summarize.py \
     ipbes-visualize.py \
     luh2-test.py \
     luh5-test.py \
     requirements.txt \
     secd-dist.py \
     setup.py \
     wid_data.py \
     /home/rstudio/work/
COPY --chown=rstudio:rstudio projections /home/rstudio/work/projections
COPY --chown=rstudio:rstudio user-scripts /home/rstudio/work/user-scripts
RUN source ~/.bashrc && \
	cd /home/rstudio/work && \
	pip install -e .

USER root
WORKDIR /home/rstudio/work
ENV LD_LIBRARY_PATH /usr/local/lib/R/lib/:${LD_LIBRARY_PATH}
