"""
BadgeOS
boot.py

Boot-time configuration for the HackNWA SockPuppetTycoon Badge.

This file executes before code.py on every reset.

Version:
    0.1.0-dev

License:
    MIT

Author:
    BadgeOS Project
"""

import supervisor
import storage
import usb_cdc

# ==========================================================
# BadgeOS Version
# ==========================================================

BOOT_VERSION = "0.1.0-dev"

# ==========================================================
# Configuration
# ==========================================================

# Enable the USB serial console.
ENABLE_USB_CONSOLE = True

# Keep the CIRCUITPY drive writable from the host computer.
# During development this should remain True.
ENABLE_USB_DRIVE = True

# Future option:
# Set to False for kiosk/deployment mode.
READ_ONLY_FILESYSTEM = False

# ==========================================================
# USB Console
# ==========================================================

if ENABLE_USB_CONSOLE:
    try:
        usb_cdc.enable(console=True, data=True)
    except Exception as exc:
        print(f"[BOOT] USB CDC enable failed: {exc}")

# ==========================================================
# Filesystem
# ==========================================================

try:
    storage.remount(
        "/",
        readonly=READ_ONLY_FILESYSTEM
    )
except Exception as exc:
    print(f"[BOOT] Filesystem remount failed: {exc}")

# ==========================================================
# Auto Reload
# ==========================================================

# Enable automatic reload whenever files are modified.
# This is ideal while developing BadgeOS.
supervisor.runtime.autoreload = True

# ==========================================================
# Boot Banner
# ==========================================================

print("=" * 60)
print("BadgeOS Bootloader")
print(f"Version : {BOOT_VERSION}")
print("Target  : RP2350A")
print("Mode    : Development")
print("=" * 60)

# ==========================================================
# Future Boot Features
# ==========================================================
#
# Planned additions:
#
# - Safe Mode
# - Hold Left Button -> Hardware Probe
# - Hold Right Button -> Recovery Mode
# - Hold Both Buttons -> Factory Reset
# - Plugin Safe Boot
# - USB Mode Selection
# - Configuration Validation
# - Boot Profiling
#
# ==========================================================
