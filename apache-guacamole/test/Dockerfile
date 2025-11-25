FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y \
    xfce4 xfce4-terminal x11-xserver-utils \
    xvfb x11vnc python3 python3-tk python3-pip supervisor \
    wget net-tools curl xterm && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /opt/gui
COPY hello_gui.py /opt/gui/hello_gui.py
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

EXPOSE 5900

CMD ["/usr/bin/supervisord", "-n", "-c", "/etc/supervisor/supervisord.conf"]

