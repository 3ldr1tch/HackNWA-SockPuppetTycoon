"""
BadgeOS Scanner Mode.

Cyberpunk-style rotating scanner effect using the NeoPixel ring.

Controls:
    short press -> cycle scanner speed

Long-press mode switching is handled globally by ModeSwitchService.
"""

import time

from badgeos.core import Mode
from badgeos.logger import get_logger


class ScannerMode(Mode):
    """Rotating scanner effect with fading tail."""

    SPEEDS = (
        0.10,
        0.06,
        0.03,
    )

    HEAD_COLOR = (
        0,
        255,
        255,
    )

    TAIL_1 = (
        0,
        120,
        255,
    )

    TAIL_2 = (
        0,
        45,
        120,
    )

    TAIL_3 = (
        0,
        12,
        35,
    )

    def __init__(
        self,
        events,
        led,
    ):
        super().__init__(
            "ScannerMode"
        )

        self.events = events
        self.led = led

        self.log = get_logger(
            self.name
        )

        self.position = 0
        self.speed_index = 1
        self._last_update = 0.0

    def start(self):
        super().start()

        self.position = 0
        self.speed_index = 1
        self._last_update = time.monotonic()

        self.events.subscribe(
            "button.short_press",
            self._on_short_press,
        )

        self._render()

        self.log.info(
            "Scanner mode started"
        )

        self.log.info(
            "Short press changes scanner speed"
        )

    def _on_short_press(
        self,
        event_name,
        data,
    ):
        if not self.active:
            return

        self.speed_index += 1

        if self.speed_index >= len(
            self.SPEEDS
        ):
            self.speed_index = 0

        self.log.info(
            "Scanner speed {}".format(
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

        if (
            now - self._last_update
        ) < interval:
            return

        self._last_update = now

        self.position += 1

        if self.position >= self.led.pixel_count:
            self.position = 0

        self._render()

    def _render(self):
        self.led.off()

        count = self.led.pixel_count

        head = self.position
        tail_1 = (
            self.position - 1
        ) % count
        tail_2 = (
            self.position - 2
        ) % count
        tail_3 = (
            self.position - 3
        ) % count

        self.led.set_pixel(
            tail_3,
            self.TAIL_3,
        )

        self.led.set_pixel(
            tail_2,
            self.TAIL_2,
        )

        self.led.set_pixel(
            tail_1,
            self.TAIL_1,
        )

        self.led.set_pixel(
            head,
            self.HEAD_COLOR,
        )

    def stop(self):
        self.events.unsubscribe(
            "button.short_press",
            self._on_short_press,
        )

        self.led.off()

        self.log.info(
            "Scanner mode stopped"
        )

        super().stop()
