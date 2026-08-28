"""
BadgeOS Heartbeat Service.

Provides a periodic visual indication that the scheduler is alive.
"""

import time

from badgeos.core import Service


class HeartbeatService(Service):
    """Blink the NeoPixel ring at a configurable interval."""

    def __init__(self, led, interval=1.0):
        super().__init__("Heartbeat")

        self.led = led
        self.interval = interval

        self._last_toggle = 0.0
        self._state = False
        self._counter = 0

    def initialize(self):
        super().initialize()

        self._state = False
        self._counter = 0
        self._last_toggle = time.monotonic()

        self.led.off()

        self.log.info(
            "Heartbeat initialized ({}s interval)".format(
                self.interval
            )
        )

    def update(self):
        now = time.monotonic()

        if (now - self._last_toggle) < self.interval:
            return

        self._last_toggle = now
        self._state = not self._state
        self._counter += 1

        if self._state:
            self.led.green()
        else:
            self.led.off()

        self.log.info(
            "Heartbeat #{}".format(self._counter)
        )

    def enable(self):
        if self.enabled:
            return

        self.enabled = True

        self._state = False
        self._last_toggle = time.monotonic()

        self.led.off()

        self.log.info("Enabled")

    def disable(self):
        if not self.enabled:
            return

        self.enabled = False
        self._state = False

        self.led.off()

        self.log.info("Disabled")

    def shutdown(self):
        self.led.off()

        self.log.info(
            "Heartbeat stopped after {} toggles".format(
                self._counter
            )
        )

        super().shutdown()
