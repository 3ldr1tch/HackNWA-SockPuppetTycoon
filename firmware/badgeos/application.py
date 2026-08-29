"""
BadgeOS main Application object.
"""

import gc

import board

from badgeos.config import SCHEDULER_TICK_INTERVAL
from badgeos.core import Scheduler
from badgeos.drivers import LEDDriver
from badgeos.events import EventBus
from badgeos.logger import get_logger
from badgeos.modes import InputDemoMode
from badgeos.plugins import PluginManager
from badgeos.services import (
    ButtonService,
    ModeManagerService,
)


log = get_logger("APP")


class Application:
    """Own and coordinate the major BadgeOS subsystems."""

    def __init__(self):
        self.scheduler = Scheduler(
            tick_interval=SCHEDULER_TICK_INTERVAL
        )

        self.events = EventBus()

        self.led = LEDDriver()

        self.plugin_manager = PluginManager(
            self
        )

        self.button = None
        self.mode_manager = None
        self.input_demo = None

    def initialize(self):
        log.info(
            "Initializing services"
        )

        self.button = ButtonService(
            board.GP20,
            self.events,
            name="UserButton",
            debounce_ms=30,
            long_press_seconds=0.75,
        )

        self.mode_manager = (
            ModeManagerService()
        )

        self.input_demo = InputDemoMode(
            self.events,
            self.led,
        )

        self.mode_manager.set_mode(
            self.input_demo
        )

        self.scheduler.register(
            self.mode_manager
        )

        self.scheduler.register(
            self.button
        )

        log.info(
            "Initializing plugins"
        )

        self.plugin_manager.start()

        log.info(
            "Initialization complete"
        )

        log.info(
            "Free RAM: {} bytes".format(
                gc.mem_free()
            )
        )

    def run(self):
        self.initialize()

        log.info(
            "Starting scheduler"
        )

        self.scheduler.run()
