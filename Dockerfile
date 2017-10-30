FROM jupyter/datascience-notebook:latest

MAINTAINER Ricardo E. Gonzalez <ricardog@ricardog.com>

RUN R BATCH -e 'install.packages(c("matrix", "lme4"), repos="https://cran.ma.imperial.ac.uk/")'
COPY environment.yml requirements.txt setup.py luh2-test.py luh5-test.py /home/jovyan/work/
COPY projections /home/jovyan/work/projections
#RUN conda env update -n root -f /work/environment.yml && \
#    conda clean -tipsy
#RUN pip install -e .

