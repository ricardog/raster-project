FROM geospatial:4.0.0
MAINTAINER Ricardo E. Gonzalez <ricardog@ricardog.com>

RUN apt-get -y install python3-pip \
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
	libffi-dev \
	gdal-bin && \
	pip3 install -U pip

ADD --chown=rstudio:rstudio \
	https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer \
	/tmp/
RUN usermod --shell /bin/bash rstudio
USER rstudio
RUN export CONFIGURE_OPTS=--enable-shared && \
	cat /tmp/pyenv-installer | /bin/bash && \
	echo 'export PYENV_ROOT="${HOME}/.pyenv"' >> ~/.bash_profile && \
	echo 'export PATH="${HOME}/.pyenv/bin:$PATH"' >> ~/.bash_profile && \
	echo 'eval "$(pyenv init --path)"' >> ~/.bash_profile && \
	echo '. "${HOME}/.bashrc"' >> ~/.bash_profile && \
	export PATH="${HOME}/.pyenv/bin:$PATH" && \
	echo 'eval "$(pyenv init -)"' >> ~/.bashrc && \
	echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc && \
	eval "$(pyenv init -)" && \
	eval "$(pyenv virtualenv-init -)" && \
	pyenv install 3.8.6 && \
	pyenv global 3.8.6

RUN . /home/rstudio/.bash_profile && \
	pip install -U pip && \
	pip install numpy cython && \
	pip install gdal==3.0.4 --global-option "build_ext" --global-option="--include-dirs=/usr/include/gdal"

USER root
