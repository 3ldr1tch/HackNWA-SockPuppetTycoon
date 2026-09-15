"""
BadgeOS Input Demo Mode.

Demonstrates event-driven positional control using the NeoPixel ring.

Controls:
    short press -> advance active pixel

Mode switching is handled globally by ModeSwitchService.
"""

from badgeos.core import Mode
from badgeos.logger import get_logger


class InputDemoMode(Mode):
    """Move a single illuminated pixel around the LED ring."""

    COLOR = (0, 255, 0)

    def __init__(
        self,
        events,
        led,
    ):
        super().__init__("InputDemo")

        self.events = events
        self.led = led

        self.log = get_logger(
            self.name
        )

        self.position = 0

    def start(self):
        super().start()

        self.position = 0

        self.events.subscribe(
            "button.short_press",
            self._on_short_press,
        )

        self._render()

        self.log.info(
            "Input demo started"
        )

        self.log.info(
            "Short press moves pixel"
        )

    def _on_short_press(
        self,
        event_name,
        data,
    ):
        if not self.active:
            return

        self.position += 1

        if self.position >= self.led.pixel_count:
            self.position = 0

        self._render()

        self.log.info(
            "Pixel position {}".format(
                self.position
            )
        )

    def _render(self):
        self.led.off()

        self.led.set_pixel(
            self.position,
            self.COLOR,
        )

    def update(self):
        pass

    def stop(self):
        self.events.unsubscribe(
            "button.short_press",
            self._on_short_press,
        )

        self.led.off()

        self.log.info(
            "Input demo stopped"
        )

        super().stop()
