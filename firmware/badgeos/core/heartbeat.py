"""
BadgeOS Heartbeat Service

A simple service used to verify that the scheduler is
running correctly.

The heartbeat emits a log message once per second,
regardless of the scheduler tick rate.
"""

import time

from badgeos.core.service import Service


class HeartbeatService(Service):
    """
    Periodic heartbeat service.
    """

    def __init__(self, interval=1.0):
        super().__init__("Heartbeat")

        self.interval = interval
        self.counter = 0
        self.last_tick = 0.0

    def initialize(self):
        """
        Initialize the heartbeat timer.
        """

        super().initialize()

        self.last_tick = time.monotonic()

        self.log.info("Heartbeat initialized")

    def update(self):
        """
        Called every scheduler cycle.
        """

        now = time.monotonic()

        if (now - self.last_tick) >= self.interval:

            self.counter += 1
            self.last_tick = now

            self.log.info(
                f"Heartbeat #{self.counter}"
            )

    def shutdown(self):
        """
        Shutdown the heartbeat service.
        """

        self.log.info(
            f"Heartbeat stopped after {self.counter} beats"
        )

        super().shutdown()
