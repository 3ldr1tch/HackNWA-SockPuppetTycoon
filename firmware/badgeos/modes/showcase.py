"""
BadgeOS Showcase Mode.

Automatically rotates through several LED effects for unattended
demo/display use.

Controls:
    short press -> skip to next effect

Long-press mode switching is handled globally by ModeSwitchService.
"""

import time

from badgeos.core import Mode
from badgeos.logger import get_logger


class ShowcaseMode(Mode):
    """Automatic multi-effect LED showcase."""

    EFFECT_SECONDS = 5.0

    EFFECT_SCANNER = 0
    EFFECT_PULSE = 1
    EFFECT_CHASE = 2
    EFFECT_BREATHE = 3
    EFFECT_SPARKLE = 4

    EFFECT_NAMES = (
        "Scanner",
        "Pulse",
        "Chase",
        "Breathe",
        "Sparkle",
    )

    def __init__(
        self,
        events,
        led,
    ):
        super().__init__(
            "ShowcaseMode"
        )

        self.events = events
        self.led = led

        self.log = get_logger(
            self.name
        )

        self.effect = 0

        self._effect_started = 0.0
        self._last_update = 0.0

        self._position = 0
        self._level = 0
        self._direction = 1

        self._sparkle_index = 0
        self._sparkle_phase = 0

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def start(self):
        super().start()

        self.events.subscribe(
            "button.short_press",
            self._on_short_press,
        )

        self.effect = 0

        self._start_effect()

        self.log.info(
            "Showcase mode started"
        )

        self.log.info(
            "Short press skips effect"
        )

    def stop(self):
        self.events.unsubscribe(
            "button.short_press",
            self._on_short_press,
        )

        self.led.off()

        self.log.info(
            "Showcase mode stopped"
        )

        super().stop()

    # ---------------------------------------------------------
    # Input
    # ---------------------------------------------------------

    def _on_short_press(
        self,
        event_name,
        data,
    ):
        if not self.active:
            return

        self._next_effect()

    # ---------------------------------------------------------
    # Effect switching
    # ---------------------------------------------------------

    def _next_effect(self):
        self.effect += 1

        if self.effect >= len(
            self.EFFECT_NAMES
        ):
            self.effect = 0

        self._start_effect()

    def _start_effect(self):
        now = time.monotonic()

        self._effect_started = now
        self._last_update = now

        self._position = 0
        self._level = 0
        self._direction = 1

        self._sparkle_index = 0
        self._sparkle_phase = 0

        self.led.off()

        self.log.info(
            "Showcase effect: {}".format(
                self.EFFECT_NAMES[
                    self.effect
                ]
            )
        )

    # ---------------------------------------------------------
    # Main update
    # ---------------------------------------------------------

    def update(self):
        if not self.active:
            return

        now = time.monotonic()

        if (
            now - self._effect_started
        ) >= self.EFFECT_SECONDS:
            self._next_effect()
            return

        if self.effect == self.EFFECT_SCANNER:
            self._update_scanner(
                now
            )

        elif self.effect == self.EFFECT_PULSE:
            self._update_pulse(
                now
            )

        elif self.effect == self.EFFECT_CHASE:
            self._update_chase(
                now
            )

        elif self.effect == self.EFFECT_BREATHE:
            self._update_breathe(
                now
            )

        elif self.effect == self.EFFECT_SPARKLE:
            self._update_sparkle(
                now
            )

    # ---------------------------------------------------------
    # Scanner
    # ---------------------------------------------------------

    def _update_scanner(
        self,
        now,
    ):
        if (
            now - self._last_update
        ) < 0.055:
            return

        self._last_update = now

        self._position += 1

        if self._position >= self.led.pixel_count:
            self._position = 0

        count = self.led.pixel_count

        head = self._position
        tail_1 = (
            self._position - 1
        ) % count
        tail_2 = (
            self._position - 2
        ) % count
        tail_3 = (
            self._position - 3
        ) % count

        self.led.off()

        self.led.set_pixel(
            tail_3,
            (
                0,
                10,
                25,
            ),
        )

        self.led.set_pixel(
            tail_2,
            (
                0,
                40,
                100,
            ),
        )

        self.led.set_pixel(
            tail_1,
            (
                0,
                120,
                255,
            ),
        )

        self.led.set_pixel(
            head,
            (
                0,
                255,
                255,
            ),
        )

    # ---------------------------------------------------------
    # Pulse
    # ---------------------------------------------------------

    def _update_pulse(
        self,
        now,
    ):
        if (
            now - self._last_update
        ) < 0.025:
            return

        self._last_update = now

        self._level += (
            self._direction
            * 7
        )

        if self._level >= 255:
            self._level = 255
            self._direction = -1

        elif self._level <= 0:
            self._level = 0
            self._direction = 1

        red = (
            80
            * self._level
            // 255
        )

        green = (
            0
            * self._level
            // 255
        )

        blue = (
            255
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

    # ---------------------------------------------------------
    # Chase
    # ---------------------------------------------------------

    def _update_chase(
        self,
        now,
    ):
        if (
            now - self._last_update
        ) < 0.070:
            return

        self._last_update = now

        self._position += 1

        if self._position >= self.led.pixel_count:
            self._position = 0

        self.led.off()

        colors = (
            (
                255,
                0,
                80,
            ),
            (
                255,
                100,
                0,
            ),
            (
                255,
                255,
                0,
            ),
            (
                0,
                255,
                100,
            ),
            (
                0,
                180,
                255,
            ),
            (
                140,
                0,
                255,
            ),
        )

        for offset in range(
            6
        ):
            position = (
                self._position
                + offset * 2
            ) % self.led.pixel_count

            self.led.set_pixel(
                position,
                colors[
                    offset
                ],
            )

    # ---------------------------------------------------------
    # Breathe
    # ---------------------------------------------------------

    def _update_breathe(
        self,
        now,
    ):
        if (
            now - self._last_update
        ) < 0.030:
            return

        self._last_update = now

        self._level += (
            self._direction
            * 5
        )

        if self._level >= 255:
            self._level = 255
            self._direction = -1

        elif self._level <= 0:
            self._level = 0
            self._direction = 1

        red = (
            255
            * self._level
            // 255
        )

        blue = (
            180
            * self._level
            // 255
        )

        self.led.fill(
            (
                red,
                0,
                blue,
            )
        )

    # ---------------------------------------------------------
    # Sparkle
    # ---------------------------------------------------------

    def _update_sparkle(
        self,
        now,
    ):
        if (
            now - self._last_update
        ) < 0.080:
            return

        self._last_update = now

        self._sparkle_phase += 1

        self._sparkle_index = (
            (
                self._sparkle_index
                + 5
                + self._sparkle_phase
            )
            % self.led.pixel_count
        )

        self.led.off()

        self.led.set_pixel(
            self._sparkle_index,
            (
                255,
                255,
                255,
            ),
        )

        second = (
            self._sparkle_index
            + 4
        ) % self.led.pixel_count

        self.led.set_pixel(
            second,
            (
                60,
                0,
                120,
            ),
        )
