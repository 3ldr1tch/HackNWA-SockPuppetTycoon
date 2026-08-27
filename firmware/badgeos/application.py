"""
BadgeOS main Application object.
"""

import gc

from badgeos.config import SCHEDULER_TICK_INTERVAL
from badgeos.core import Scheduler
from badgeos.drivers import LEDDriver
from badgeos.logger import get_logger
from badgeos.plugins import PluginManager
from badgeos.services import HeartbeatService


log = get_logger("APP")


class Application:
    """Own and coordinate the major BadgeOS subsystems."""

    def __init__(self):
        self.scheduler = Scheduler(
            tick_interval=SCHEDULER_TICK_INTERVAL
        )

        self.led = LEDDriver()

        self.plugin_manager = PluginManager(self)

    def initialize(self):
        log.info("Initializing services")

        self.scheduler.register(
            HeartbeatService(
                self.led,
                interval=1.0,
            )
        )

        log.info("Initializing plugins")
        self.plugin_manager.start()

        log.info("Initialization complete")
        log.info(
            "Free RAM: {} bytes".format(gc.mem_free())
        )

    def run(self):
        self.initialize()

        log.info("Starting scheduler")

        self.scheduler.run()
