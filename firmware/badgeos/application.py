"""
BadgeOS main Application object.
"""

import gc

import board

from badgeos.boot_status import (
    show_boot_error,
    show_boot_success,
)
from badgeos.config import SCHEDULER_TICK_INTERVAL
from badgeos.core import Scheduler
from badgeos.drivers import LEDDriver
from badgeos.events import EventBus
from badgeos.logger import get_logger
from badgeos.modes import (
    DiagMode,
    HIDDemoMode,
    InputDemoMode,
    PulseDemoMode,
    ReactionGameMode,
    ScannerMode,
    ShowcaseMode,
)
from badgeos.plugins import PluginManager
from badgeos.services import (
    ButtonService,
    ModeManagerService,
    ModeSwitchService,
    SerialShellService,
)
from badgeos.startup import run_startup_animation


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
        self.mode_switch = None

        self.serial_shell = None

        self.input_demo = None
        self.pulse_demo = None
        self.hid_demo = None
        self.diag_mode = None
        self.reaction_game = None
        self.scanner_mode = None
        self.showcase_mode = None

    def initialize(self):
        try:
            log.info(
                "Running startup animation"
            )

            run_startup_animation(
                self.led
            )

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

            self.pulse_demo = PulseDemoMode(
                self.events,
                self.led,
            )

            self.hid_demo = HIDDemoMode(
                self.events,
                self.led,
            )

            self.diag_mode = DiagMode(
                self.events,
                self.led,
            )

            self.reaction_game = (
                ReactionGameMode(
                    self.events,
                    self.led,
                )
            )

            self.scanner_mode = (
                ScannerMode(
                    self.events,
                    self.led,
                )
            )

            self.showcase_mode = (
                ShowcaseMode(
                    self.events,
                    self.led,
                )
            )

            self.mode_manager.register_mode(
                self.input_demo
            )

            self.mode_manager.register_mode(
                self.pulse_demo
            )

            self.mode_manager.register_mode(
                self.hid_demo
            )

            self.mode_manager.register_mode(
                self.diag_mode
            )

            self.mode_manager.register_mode(
                self.reaction_game
            )

            self.mode_manager.register_mode(
                self.scanner_mode
            )

            self.mode_manager.register_mode(
                self.showcase_mode
            )

            modes = (
                self.input_demo,
                self.pulse_demo,
                self.hid_demo,
                self.diag_mode,
                self.reaction_game,
                self.scanner_mode,
                self.showcase_mode,
            )

            self.mode_manager.set_mode(
                self.showcase_mode
            )

            self.mode_switch = (
                ModeSwitchService(
                    self.events,
                    self.mode_manager,
                    modes,
                )
            )

            self.serial_shell = (
                SerialShellService(
                    self.led,
                    self.mode_manager,
                )
            )

            self.scheduler.register(
                self.mode_manager
            )

            self.scheduler.register(
                self.mode_switch
            )

            self.scheduler.register(
                self.serial_shell
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

            show_boot_success(
                self.led
            )

        except Exception as exc:
            log.error(
                "Initialization failed: {}".format(
                    exc
                )
            )

            try:
                import sys

                sys.print_exception(
                    exc
                )

            except Exception:
                pass

            try:
                show_boot_error(
                    self.led
                )

            except Exception:
                pass

            raise

    def run(self):
        self.initialize()

        log.info(
            "Starting scheduler"
        )

        self.scheduler.run()
