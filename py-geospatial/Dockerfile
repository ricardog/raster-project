FROM geospatial:latest

MAINTAINER Ricardo E. Gonzalez <ricardog@ricardog.com>
RUN apt-get -y install python-pip \
	make \
	build-essential \
	libssl-dev \
	zlib1g-dev \
	libbz2-dev \
	libreadline-dev \
	libsqlite3-dev \
	wget \
	llvm \
	libncurses5-dev \
	xz-utils \
	tk-dev \
	libxml2-dev \
	libxmlsec1-dev \
	libffi-dev && \
	pip install -U pip

ADD --chown=rstudio:rstudio \
	https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer \
	/tmp/
RUN usermod --shell /bin/bash rstudio
USER rstudio
RUN cat /tmp/pyenv-installer | /bin/bash && \
	echo 'export PATH="${HOME}/.pyenv/bin:$PATH"' >> ~/.bashrc && \
	echo 'eval "$(pyenv init -)"' >> ~/.bashrc && \
	echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc && \
	export PATH="${HOME}/.pyenv/bin:$PATH" && \
	eval "$(pyenv init -)" && \
	eval "$(pyenv virtualenv-init -)" && \
	pyenv install 3.6.3 && \
	pyenv global 3.6.3

RUN . /home/rstudio/.bashrc && \
	pip install -U pip && \
	pip install numpy cython && \
	pip install gdal==2.1.3 --global-option "build_ext" --global-option="--include-dirs=/usr/include/gdal"

USER root
