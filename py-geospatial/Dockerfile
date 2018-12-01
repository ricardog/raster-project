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

RUN wget -qO- https://github.com/pyenv/pyenv-installer/raw/master/bin/pyenv-installer | \
	/bin/bash && \
	echo 'export PATH="/root/.pyenv/bin:$PATH"' >> ~/.bashrc && \
	echo 'eval "$(pyenv init -)"' >> ~/.bashrc && \
	echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc && \
	export PATH="/root/.pyenv/bin:$PATH" && \
	eval "$(pyenv init -)" && \
	eval "$(pyenv virtualenv-init -)" && \
	pyenv install 3.6.3 && \
	pyenv global 3.6.3 && \
	pip install -U pip
CMD /bin/bash



