FROM jupyter/datascience-notebook:latest

MAINTAINER Ricardo E. Gonzalez <ricardog@ricardog.com>

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
COPY _condarc /opt/conda/.condarc
RUN conda env update -n root -f /home/jovyan/work/environment.yml && \
    conda clean -tipsy
RUN cd /home/jovyan/work && pip install -e .


