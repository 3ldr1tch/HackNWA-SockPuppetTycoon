"""
BadgeOS configuration.

Only permanent board configuration belongs here.

Automatically detected values will later
be written to hardware_profile.py.
"""

import board

VERSION = "0.1.0-dev"

# Confirmed from your badge
NEOPIXEL_PIN = board.GP11

# Update after hardware probe
NUM_PIXELS = 12

BUTTON_LEFT = None

BUTTON_RIGHT = None

I2C_BUSES = []

SPI_BUSES = []

UART_BUSES = []
