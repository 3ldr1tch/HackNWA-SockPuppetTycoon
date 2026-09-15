"""
BadgeOS Pulse Demo Mode.

Displays a pulsing RGB LED effect across the NeoPixel ring.

Controls:
    short press -> cycle pulse speed

Mode switching is handled globally by ModeSwitchService.
"""

import time

from badgeos.core import Mode
from badgeos.logger import get_logger


class PulseDemoMode(Mode):
    """Pulse the full LED ring with adjustable animation speed."""

    SPEEDS = (
        0.035,
        0.020,
        0.010,
    )

    BASE_COLOR = (
        0,
        180,
        255,
    )

    def __init__(
        self,
        events,
        led,
    ):
        super().__init__("PulseDemo")

        self.events = events
        self.led = led

        self.log = get_logger(
            self.name
        )

        self.speed_index = 0

        self._level = 0
        self._direction = 1
        self._last_update = 0.0

    def start(self):
        super().start()

        self.speed_index = 0

        self._level = 0
        self._direction = 1
        self._last_update = time.monotonic()

        self.events.subscribe(
            "button.short_press",
            self._on_short_press,
        )

        self.led.off()

        self.log.info(
            "Pulse demo started"
        )

        self.log.info(
            "Short press changes pulse speed"
        )

    def _on_short_press(
        self,
        event_name,
        data,
    ):
        if not self.active:
            return

        self.speed_index += 1

        if self.speed_index >= len(self.SPEEDS):
            self.speed_index = 0

        self.log.info(
            "Pulse speed {}".format(
                self.speed_index
            )
        )

    def update(self):
        if not self.active:
            return

        now = time.monotonic()

        interval = self.SPEEDS[
            self.speed_index
        ]

        if (now - self._last_update) < interval:
            return

        self._last_update = now

        self._level += self._direction * 8

        if self._level >= 255:
            self._level = 255
            self._direction = -1

        elif self._level <= 0:
            self._level = 0
            self._direction = 1

        red = (
            self.BASE_COLOR[0]
            * self._level
            // 255
        )

        green = (
            self.BASE_COLOR[1]
            * self._level
            // 255
        )

        blue = (
            self.BASE_COLOR[2]
            * self._level
            // 255
        )

        self.led.fill(
            (
                red,
                green,
                blue,
            )
        )

    def stop(self):
        self.events.unsubscribe(
            "button.short_press",
            self._on_short_press,
        )

        self.led.off()

        self.log.info(
            "Pulse demo stopped"
        )

        super().stop()
