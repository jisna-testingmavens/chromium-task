#!/bin/bash

DISPLAYS=(10 11 12 13 14)
PORT_BASE=5910

for i in ${!DISPLAYS[@]}; do
    D=${DISPLAYS[$i]}
    P=$((PORT_BASE+i))
    echo "Starting display :$D on port $P"
    Xvfb :$D -screen 0 1920x1080x24 &
    sleep 1
    x11vnc -display :$D -rfbport $P -forever -shared -nopw -bg &
done

sudo systemctl restart guacd
sudo systemctl restart tomcat10

