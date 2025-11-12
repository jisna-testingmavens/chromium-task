#!/bin/bash
set -e

CHROMIUM_VERSION=${CHROMIUM_VERSION:-v1}
echo "Requested Chromium version: $CHROMIUM_VERSION"

if [ -d "/opt/chromium-versions/$CHROMIUM_VERSION" ]; then
  mkdir -p /usr/local/chromium
  cp -r /opt/chromium-versions/$CHROMIUM_VERSION/* /usr/local/chromium/
  echo "Copied Chromium version $CHROMIUM_VERSION to runtime path"
else
  echo "Chromium version $CHROMIUM_VERSION not found!"
  exit 1
fi

echo "Contents of /usr/local/chromium:"
ls -R /usr/local/chromium

echo "Chromium version info:"
cat /usr/local/chromium/version.txt

