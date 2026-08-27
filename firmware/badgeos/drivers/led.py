"""
BadgeOS NeoPixel ring driver.

HackNWA SockPuppetTycoon badge:
    12 NeoPixels
    GPIO GP11
"""

import neopixel

from badgeos.config import (
    NEOPIXEL_BRIGHTNESS,
    NEOPIXEL_COUNT,
    NEOPIXEL_PIN,
)


class LEDDriver:
    """Driver for the badge's 12-pixel NeoPixel ring."""

    def __init__(
        self,
        brightness=NEOPIXEL_BRIGHTNESS,
    ):
        self.pixel_count = NEOPIXEL_COUNT

        self.pixels = neopixel.NeoPixel(
            NEOPIXEL_PIN,
            NEOPIXEL_COUNT,
            brightness=brightness,
            auto_write=False,
        )

        self.off()

    def fill(self, color):
        self.pixels.fill(color)
        self.pixels.show()

    def set_pixel(self, index, color):
        if index < 0 or index >= self.pixel_count:
            raise ValueError("NeoPixel index out of range")

        self.pixels[index] = color
        self.pixels.show()

    def off(self):
        self.fill((0, 0, 0))

    def red(self):
        self.fill((255, 0, 0))

    def green(self):
        self.fill((0, 255, 0))

    def blue(self):
        self.fill((0, 0, 255))

    def yellow(self):
        self.fill((255, 255, 0))

    def cyan(self):
        self.fill((0, 255, 255))

    def magenta(self):
        self.fill((255, 0, 255))

    def white(self):
        self.fill((255, 255, 255))

    def deinit(self):
        self.off()
        self.pixels.deinit()
