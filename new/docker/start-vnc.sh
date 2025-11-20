#!/bin/bash

export DISPLAY=:99

echo "Waiting for Chromium to be copied..."
while [ ! -f /opt/chromium/chrome ]; do
    echo "Waiting for chrome binary..."
    sleep 2
done

echo "Chrome binary found, waiting for display..."
sleep 5

echo "Launching Chrome..."
/opt/chromium/chrome \
    --no-sandbox \
    --disable-dev-shm-usage \
    --disable-gpu \
    --disable-software-rasterizer \
    --start-maximized \
    --no-first-run \
    --user-data-dir=/root/.config/chromium \
    "https://www.google.com" \
    2>&1 | tee /var/log/chrome.log

# Keep running
tail -f /dev/null
