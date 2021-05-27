FROM py-geospatial:4.0.0

MAINTAINER Ricardo E. Gonzalez <ricardog@ricardog.com>

SHELL ["/bin/bash", "--login", "-c"]

USER rstudio
RUN mkdir -p ~/work
COPY --chown=rstudio:rstudio requirements.txt /home/rstudio/work/
COPY --chown=root:root jupyter-runner /usr/local/bin/jupyter
RUN cd /home/rstudio/work && \
	whoami && \
	. ~/.bashrc && \
	which pip && \
	pip install -r requirements.txt && \
	R -e "IRkernel::installspec()"

COPY --chown=rstudio:rstudio setup.py pyproject.toml user-scripts \
    /home/rstudio/work/
COPY --chown=rstudio:rstudio projections /home/rstudio/work/projections
RUN source ~/.bashrc && \
	cd /home/rstudio/work && \
	pip install -e .

USER root
WORKDIR /home/rstudio/work
ENV LD_LIBRARY_PATH /usr/local/lib/R/lib/:${LD_LIBRARY_PATH}
