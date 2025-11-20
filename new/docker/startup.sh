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
rm -rf ${TARGET_PATH}/*  # Clean target directory first
cp -r ${SOURCE_PATH}/* ${TARGET_PATH}/

# Make chrome executable
chmod +x ${TARGET_PATH}/chrome 2>/dev/null || chmod +x ${TARGET_PATH}/chrome-linux/chrome 2>/dev/null || true

# Find and display chrome binary location
CHROME_BINARY=$(find ${TARGET_PATH} -name "chrome" -type f 2>/dev/null | head -1)
if [ -n "$CHROME_BINARY" ]; then
    echo "✓ Chrome binary ready at: ${CHROME_BINARY}"
    chmod +x ${CHROME_BINARY}
    
    # Create a symlink for easy access
    ln -sf ${CHROME_BINARY} /usr/local/bin/chrome
    
    # Test chrome version
    echo "Testing Chrome binary..."
    ${CHROME_BINARY} --version 2>/dev/null || echo "Note: Chrome version check may fail without display"
else
    echo "WARNING: Chrome binary not found in ${TARGET_PATH}"
    ls -la ${TARGET_PATH}
fi

echo "========================================="
echo "✓ Setup complete. Only version ${CHROMIUM_VERSION} is available at ${TARGET_PATH}"
echo "========================================="

# Execute passed command or keep running
exec "$@"
