FROM continuumio/miniconda3:latest

MAINTAINER Ricardo E. Gonzalez <ricardog@ricardog.com>

run pip install -U pip
RUN conda install --quiet --yes r-base r-essentials r-lme4 gdal netcdf4 rpy2

COPY Abundance.ipynb \
     gen_luh2.py \
     environment.yml \
     luh2-test.py \
     luh5-test.py \
     requirements.txt \
     secd-dist.py \
     setup.py \
     /home/jovyan/work/
COPY projections /home/jovyan/work/projections
#RUN cd /home/jovyan/work && /opt/conda/bin/pip install -e .


