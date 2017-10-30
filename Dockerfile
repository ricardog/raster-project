FROM jupyter/datascience-notebook:latest

MAINTAINER Ricardo E. Gonzalez <ricardog@ricardog.com>

RUN R BATCH -e 'install.packages(c("matrix", "lme4"), repos="https://cran.ma.imperial.ac.uk/")'
ADD environment.yml requirements.txt setup.py projections luh2-test.py luh5-test.py /work/
RUN conda update -f=/work/environment.yml
RUN pip install -e .

