FROM ubuntu:latest

MAINTAINER Ricardo E. Gonzalez <ricardog@ricardog.com>

RUN useradd -ms /bin/bash vncuser
RUN apt-get update && \
	apt-get install -y twm tightvncserver
RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*
COPY --chown=vncuser:vncuser run.sh /home/vncuser/run.sh
COPY --chown=vncuser:vncuser _twmrc /home/vncuser/.twmrc
COPY --chown=vncuser:vncuser _Xsession /home/vncuser/.Xsession
COPY --chown=vncuser:vncuser _vnc_passwd /home/vncuser/.vnc/passwd
EXPOSE 5900/tcp
USER vncuser
ENV DISPLAY=:0
ENV USER=vncuser
CMD /bin/sh /home/vncuser/run.sh

