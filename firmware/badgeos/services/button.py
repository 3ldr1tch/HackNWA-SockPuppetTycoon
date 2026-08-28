"""
BadgeOS Button Service.

Monitors a debounced button and publishes input events.

Events:
    button.pressed
    button.released
    button.short_press
    button.long_press
"""

import time

from badgeos.core import Service
from badgeos.drivers import ButtonDriver


class ButtonService(Service):
    """Publish debounced button events to the BadgeOS event bus."""

    def __init__(
        self,
        pin,
        events,
        name="UserButton",
        debounce_ms=30,
        long_press_seconds=0.75,
    ):
        super().__init__("Button")

        self.pin = pin
        self.events = events
        self.button_name = name
        self.debounce_ms = debounce_ms
        self.long_press_seconds = long_press_seconds

        self.button = None

        self._press_count = 0
        self._release_count = 0

        self._press_started = None
        self._long_press_sent = False

    def initialize(self):
        super().initialize()

        self.button = ButtonDriver(
            self.pin,
            name=self.button_name,
            debounce_ms=self.debounce_ms,
        )

        self._press_count = 0
        self._release_count = 0

        self._press_started = None
        self._long_press_sent = False

        self.log.info(
            "{} initialized ({}ms debounce, {}s long press)".format(
                self.button_name,
                self.debounce_ms,
                self.long_press_seconds,
            )
        )

    def update(self):
        self.button.update()

        now = time.monotonic()

        if self.button.was_pressed():
            self._press_count += 1
            self._press_started = now
            self._long_press_sent = False

            self.log.info(
                "{} pressed #{}".format(
                    self.button_name,
                    self._press_count,
                )
            )

            self.events.publish(
                "button.pressed",
                {
                    "button": self.button_name,
                    "count": self._press_count,
                },
            )

        if (
            self.button.pressed
            and self._press_started is not None
            and not self._long_press_sent
        ):
            duration = now - self._press_started

            if duration >= self.long_press_seconds:
                self._long_press_sent = True

                self.log.info(
                    "{} long press ({:.2f}s)".format(
                        self.button_name,
                        duration,
                    )
                )

                self.events.publish(
                    "button.long_press",
                    {
                        "button": self.button_name,
                        "count": self._press_count,
                        "duration": duration,
                    },
                )

        if self.button.was_released():
            self._release_count += 1

            duration = 0.0

            if self._press_started is not None:
                duration = now - self._press_started

            self.log.info(
                "{} released #{} ({:.2f}s)".format(
                    self.button_name,
                    self._release_count,
                    duration,
                )
            )

            self.events.publish(
                "button.released",
                {
                    "button": self.button_name,
                    "count": self._release_count,
                    "duration": duration,
                },
            )

            if not self._long_press_sent:
                self.log.info(
                    "{} short press ({:.2f}s)".format(
                        self.button_name,
                        duration,
                    )
                )

                self.events.publish(
                    "button.short_press",
                    {
                        "button": self.button_name,
                        "count": self._press_count,
                        "duration": duration,
                    },
                )

            self._press_started = None
            self._long_press_sent = False

    def shutdown(self):
        if self.button is not None:
            self.button.deinit()
            self.button = None

        self.log.info(
            "{} stopped after {} presses".format(
                self.button_name,
                self._press_count,
            )
        )

        super().shutdown()
