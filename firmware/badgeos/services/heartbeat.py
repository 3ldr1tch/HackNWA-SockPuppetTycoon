"""
BadgeOS

Heartbeat Service

Provides a visible heartbeat using the onboard NeoPixel.
"""

from badgeos.core import Service
from badgeos.drivers import LED


class HeartbeatService(Service):
    """
    Simple heartbeat that blinks the onboard LED.
    """

    def __init__(self, interval=1.0):

        super().__init__(interval)

        self.led = LED()
        self._state = False

    def start(self):

        self.led.off()

    def update(self):

        self._state = not self._state

        if self._state:
            self.led.green()
        else:
            self.led.off()

    def stop(self):

        self.led.off()
