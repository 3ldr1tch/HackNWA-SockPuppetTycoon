"""
BadgeOS

drivers/led.py

NeoPixel LED driver.
"""

import board
import neopixel


class LED:

    def __init__(self, brightness=0.2):

        self.pixel = neopixel.NeoPixel(
            board.NEOPIXEL,
            1,
            brightness=brightness,
            auto_write=True,
        )

        self.off()

    def set(self, r, g, b):

        self.pixel[0] = (r, g, b)

    def off(self):

        self.set(0, 0, 0)

    def red(self):

        self.set(255, 0, 0)

    def green(self):

        self.set(0, 255, 0)

    def blue(self):

        self.set(0, 0, 255)

    def yellow(self):

        self.set(255, 255, 0)

    def cyan(self):

        self.set(0, 255, 255)

    def magenta(self):

        self.set(255, 0, 255)

    def white(self):

        self.set(255, 255, 255)
