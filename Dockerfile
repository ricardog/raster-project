FROM py-geospatial:latest

MAINTAINER Ricardo E. Gonzalez <ricardog@ricardog.com>

COPY reqs.txt /work/
RUN cd /work && \
	/root/.pyenv/shims/pip install numpy && \
	/root/.pyenv/shims/pip install cython && \
	/root/.pyenv/shims/pip install gdal==2.1.3 --global-option "build_ext" --global-option="--include-dirs=/usr/include/gdal" && \
	/root/.pyenv/shims/pip install -r reqs.txt

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
COPY user-scripts /work/user-scripts
RUN cd /work && /root/.pyenv/shims/pip install -e .
WORKDIR /work
ENV LD_LIBRARY_PATH /usr/local/lib/R/lib/:${LD_LIBRARY_PATH}


