"""
BadgeOS board configuration.

Hardware values confirmed for the HackNWA SockPuppetTycoon badge.
"""

import board


NEOPIXEL_PIN = board.GP11
NEOPIXEL_COUNT = 12
NEOPIXEL_BRIGHTNESS = 0.20

SCHEDULER_TICK_INTERVAL = 0.01
