FROM jupyter/datascience-notebook:latest

MAINTAINER Ricardo E. Gonzalez <ricardog@ricardog.com>

## Installing lme4 may not be required (it should be available
## already in the container).
RUN R BATCH -e 'install.packages(c("Matrix", "lme4"), repos="https://cran.ma.imperial.ac.uk/")'

COPY environment.yml requirements.txt setup.py luh2-test.py luh5-test.py /home/jovyan/work/
COPY projections /home/jovyan/work/projections
COPY _condarc /opt/conda/.condarc
RUN conda env update -n root -f /home/jovyan/work/environment.yml && \
    conda clean -tipsy
RUN cd /home/jovyan/work && pip install -e .


