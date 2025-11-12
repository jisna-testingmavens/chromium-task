#!/bin/bash
set -e

CHROMIUM_VERSION=${CHROMIUM_VERSION:-"120.0.6099.109"}
SOURCE_PATH="/opt/chromium-versions/${CHROMIUM_VERSION}"
TARGET_PATH="/usr/local/chromium"

echo "========================================="
echo "Chromium Pod Startup"
echo "========================================="
echo "Requested version: ${CHROMIUM_VERSION}"
echo "Source path: ${SOURCE_PATH}"
echo "Target path: ${TARGET_PATH}"

# Check if version exists
if [ ! -d "${SOURCE_PATH}" ]; then
    echo "ERROR: Chromium version ${CHROMIUM_VERSION} not found in ${SOURCE_PATH}"
    echo "Available versions:"
    ls -la /opt/chromium-versions/ || echo "No versions found"
    exit 1
fi

echo "Copying Chromium ${CHROMIUM_VERSION} to runtime path..."
cp -r ${SOURCE_PATH}/* ${TARGET_PATH}/

# Make chrome executable
chmod +x ${TARGET_PATH}/chrome 2>/dev/null || chmod +x ${TARGET_PATH}/chrome-linux/chrome 2>/dev/null || true

echo "✓ Chromium ${CHROMIUM_VERSION} ready at ${TARGET_PATH}"
echo "Chrome binary location:"
find ${TARGET_PATH} -name "chrome" -type f 2>/dev/null || echo "Chrome binary not found"

echo "========================================="

# Execute passed command or keep running
exec "$@"
