"""
BadgeOS Button Service.

Monitors a debounced button input and uses button presses to control
another BadgeOS service.
"""

from badgeos.core import Service
from badgeos.drivers import ButtonDriver


class ButtonService(Service):
    """Toggle the heartbeat service from a physical button."""

    def __init__(
        self,
        pin,
        heartbeat,
        debounce_ms=30,
    ):
        super().__init__("Button")

        self.pin = pin
        self.heartbeat = heartbeat
        self.debounce_ms = debounce_ms

        self.button = None
        self._press_count = 0

    def initialize(self):
        super().initialize()

        self.button = ButtonDriver(
            self.pin,
            name="UserButton",
            debounce_ms=self.debounce_ms,
        )

        self._press_count = 0

        self.log.info(
            "Button initialized ({}ms debounce)".format(
                self.debounce_ms
            )
        )

    def update(self):
        self.button.update()

        if not self.button.was_pressed():
            return

        self._press_count += 1

        if self.heartbeat.enabled:
            self.heartbeat.disable()

            self.log.info(
                "Press #{}: heartbeat disabled".format(
                    self._press_count
                )
            )
        else:
            self.heartbeat.enable()

            self.log.info(
                "Press #{}: heartbeat enabled".format(
                    self._press_count
                )
            )

    def shutdown(self):
        if self.button is not None:
            self.button.deinit()
            self.button = None

        self.log.info(
            "Button stopped after {} presses".format(
                self._press_count
            )
        )

        super().shutdown()
