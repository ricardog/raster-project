FROM continuumio/miniconda3:latest

MAINTAINER Ricardo E. Gonzalez <ricardog@ricardog.com>

run pip install -U pip
RUN conda install --quiet --yes r-base r-essentials r-lme4 gdal netcdf4 rpy2
COPY reqs.txt /work/
RUN cd /work && /opt/conda/bin/pip install -r reqs.txt

COPY Abundance.ipynb \
     do-hist-one.sh \
     do-hist2.sh \
     doit2.sh \
     do-hist.sh \
     doit.sh \
     environment.yml \
     gen_luh2.py \
     ipbes-project.py \
     ipbes-summarize.py \
     ipbes-visualize.py \
     luh2-test.py \
     luh5-test.py \
     requirements.txt \
     secd-dist.py \
     setup.py \
     /work/
COPY projections /work/projections
RUN cd /work && /opt/conda/bin/pip install -e .
WORKDIR /work


