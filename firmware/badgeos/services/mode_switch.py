"""
BadgeOS Mode Switch Service.

Provides global mode switching through long button presses.
"""

from badgeos.core import Service


class ModeSwitchService(Service):
    """Cycle through registered BadgeOS modes."""

    def __init__(
        self,
        events,
        mode_manager,
        modes,
    ):
        super().__init__("ModeSwitch")

        self.events = events
        self.mode_manager = mode_manager
        self.modes = modes

    def initialize(self):
        super().initialize()

        self.events.subscribe(
            "button.long_press",
            self._on_long_press,
        )

        self.log.info(
            "Mode switch initialized"
        )

        self.log.info(
            "{} modes available".format(
                len(self.modes)
            )
        )

    def _on_long_press(
        self,
        event_name,
        data,
    ):
        if not self.modes:
            return

        current = self.mode_manager.current_mode

        try:
            current_index = self.modes.index(
                current
            )
        except ValueError:
            current_index = -1

        next_index = (
            current_index + 1
        ) % len(self.modes)

        next_mode = self.modes[
            next_index
        ]

        self.log.info(
            "Switching to mode: {}".format(
                next_mode.name
            )
        )

        self.mode_manager.set_mode(
            next_mode
        )

    def update(self):
        pass

    def shutdown(self):
        self.events.unsubscribe(
            "button.long_press",
            self._on_long_press,
        )

        self.log.info(
            "Mode switch stopped"
        )

        super().shutdown()
