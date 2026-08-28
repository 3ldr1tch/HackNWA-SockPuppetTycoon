"""
BadgeOS Heartbeat Controller.

Demonstrates event-driven interaction between input and services.
"""

from badgeos.core import Service


class HeartbeatControllerService(Service):
    """Toggle the heartbeat when the user performs a short press."""

    def __init__(
        self,
        events,
        heartbeat,
    ):
        super().__init__("HeartbeatController")

        self.events = events
        self.heartbeat = heartbeat

    def initialize(self):
        super().initialize()

        self.events.subscribe(
            "button.short_press",
            self._on_short_press,
        )

        self.events.subscribe(
            "button.long_press",
            self._on_long_press,
        )

        self.log.info(
            "Listening for short and long button presses"
        )

    def _on_short_press(
        self,
        event_name,
        data,
    ):
        button_name = data.get(
            "button",
            "unknown",
        )

        if self.heartbeat.enabled:
            self.heartbeat.disable()

            self.log.info(
                "{} short press disabled heartbeat".format(
                    button_name
                )
            )

        else:
            self.heartbeat.enable()

            self.log.info(
                "{} short press enabled heartbeat".format(
                    button_name
                )
            )

    def _on_long_press(
        self,
        event_name,
        data,
    ):
        button_name = data.get(
            "button",
            "unknown",
        )

        duration = data.get(
            "duration",
            0.0,
        )

        self.log.info(
            "{} long press received ({:.2f}s)".format(
                button_name,
                duration,
            )
        )

    def update(self):
        pass

    def shutdown(self):
        self.events.unsubscribe(
            "button.short_press",
            self._on_short_press,
        )

        self.events.unsubscribe(
            "button.long_press",
            self._on_long_press,
        )

        self.log.info(
            "Stopped listening for button events"
        )

        super().shutdown()
