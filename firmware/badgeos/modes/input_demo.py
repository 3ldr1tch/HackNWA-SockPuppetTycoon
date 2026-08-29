"""
BadgeOS Input Demo Mode.

Demonstrates event-driven gameplay-style input using the NeoPixel ring.

Controls:
    short press -> advance active pixel
    long press  -> cycle active color
"""

from badgeos.core import Mode
from badgeos.logger import get_logger


class InputDemoMode(Mode):
    """Simple interactive LED demo."""

    COLORS = (
        (0, 255, 0),
        (0, 0, 255),
        (255, 0, 0),
        (255, 255, 0),
        (0, 255, 255),
        (255, 0, 255),
        (255, 255, 255),
    )

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
        self.color_index = 0

    def start(self):
        super().start()

        self.position = 0
        self.color_index = 0

        self.events.subscribe(
            "button.short_press",
            self._on_short_press,
        )

        self.events.subscribe(
            "button.long_press",
            self._on_long_press,
        )

        self._render()

        self.log.info(
            "Input demo started"
        )

        self.log.info(
            "Short press moves pixel; long press changes color"
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

    def _on_long_press(
        self,
        event_name,
        data,
    ):
        if not self.active:
            return

        self.color_index += 1

        if self.color_index >= len(self.COLORS):
            self.color_index = 0

        self._render()

        self.log.info(
            "Color index {}".format(
                self.color_index
            )
        )

    def _render(self):
        color = self.COLORS[
            self.color_index
        ]

        self.led.off()

        self.led.set_pixel(
            self.position,
            color,
        )

    def update(self):
        pass

    def stop(self):
        self.events.unsubscribe(
            "button.short_press",
            self._on_short_press,
        )

        self.events.unsubscribe(
            "button.long_press",
            self._on_long_press,
        )

        self.led.off()

        self.log.info(
            "Input demo stopped"
        )

        super().stop()
