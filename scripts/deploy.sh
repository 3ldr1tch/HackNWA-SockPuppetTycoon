#!/usr/bin/env bash

###############################################################################
#
# BadgeOS Deployment Tool
#
# Deploys the firmware directory to a connected CircuitPython device.
#
# Version: 0.1.0-dev
#
###############################################################################

set -euo pipefail

###############################################################################
# Configuration
###############################################################################

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

FIRMWARE_DIR="${PROJECT_ROOT}/firmware"

###############################################################################
# Locate CIRCUITPY
###############################################################################

SEARCH_PATHS=(
    "/run/media/${USER}/CIRCUITPY"
    "/media/${USER}/CIRCUITPY"
    "/Volumes/CIRCUITPY"
)

TARGET=""

for path in "${SEARCH_PATHS[@]}"; do
    if [[ -d "$path" ]]; then
        TARGET="$path"
        break
    fi
done

if [[ -z "$TARGET" ]]; then
    echo
    echo "ERROR: CIRCUITPY drive not found."
    echo
    exit 1
fi

echo
echo "BadgeOS Deployment"
echo "=================="
echo

echo "Source : $FIRMWARE_DIR"
echo "Target : $TARGET"

###############################################################################
# Verify firmware
###############################################################################

if [[ ! -f "${FIRMWARE_DIR}/boot.py" ]]; then
    echo
    echo "boot.py not found."
    exit 1
fi

if [[ ! -f "${FIRMWARE_DIR}/code.py" ]]; then
    echo
    echo "code.py not found."
    exit 1
fi

###############################################################################
# Remove previous BadgeOS installation
###############################################################################

echo
echo "Removing previous BadgeOS files..."

rm -rf "${TARGET}/badgeos"

###############################################################################
# Copy firmware
###############################################################################

echo
echo "Copying firmware..."

cp "${FIRMWARE_DIR}/boot.py" "${TARGET}/"

cp "${FIRMWARE_DIR}/code.py" "${TARGET}/"

cp -r "${FIRMWARE_DIR}/badgeos" "${TARGET}/"

###############################################################################
# Copy libraries (optional)
###############################################################################

if [[ -d "${FIRMWARE_DIR}/lib" ]]; then

    echo
    echo "Synchronizing lib/"

    mkdir -p "${TARGET}/lib"

    cp -r "${FIRMWARE_DIR}/lib/"* "${TARGET}/lib/" 2>/dev/null || true

fi

sync

###############################################################################
# Finished
###############################################################################

echo
echo "Deployment Complete."
echo

echo "CircuitPython should automatically reload."

echo
