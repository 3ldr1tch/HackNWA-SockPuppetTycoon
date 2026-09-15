"""
BadgeOS Diagnostics Mode.

Provides a simple visual diagnostics interface using the NeoPixel ring.

Controls:
    short press -> cycle diagnostic page

Pages:
    RAM
    Uptime
    USB
    Version
"""

import gc
import time

import supervisor

from badgeos.core import Mode
from badgeos.logger import get_logger
from badgeos.version import CODENAME, VERSION


class DiagMode(Mode):
    """Visual and serial diagnostics mode."""

    PAGE_RAM = 0
    PAGE_UPTIME = 1
    PAGE_USB = 2
    PAGE_VERSION = 3

    PAGE_NAMES = (
        "RAM",
        "Uptime",
        "USB",
        "Version",
    )

    def __init__(
        self,
        events,
        led,
    ):
        super().__init__("DiagMode")

        self.events = events
        self.led = led

        self.log = get_logger(
            self.name
        )

        self.page = self.PAGE_RAM
        self._last_render = 0.0
        self._refresh_interval = 1.0

    def start(self):
        super().start()

        self.page = self.PAGE_RAM
        self._last_render = 0.0

        self.events.subscribe(
            "button.short_press",
            self._on_short_press,
        )

        self.log.info(
            "Diagnostics mode started"
        )

        self.log.info(
            "Short press cycles diagnostic page"
        )

        self._render(
            force=True
        )

    def _on_short_press(
        self,
        event_name,
        data,
    ):
        if not self.active:
            return

        self.page += 1

        if self.page >= len(
            self.PAGE_NAMES
        ):
            self.page = 0

        self.log.info(
            "Diagnostic page: {}".format(
                self.PAGE_NAMES[
                    self.page
                ]
            )
        )

        self._render(
            force=True
        )

    def update(self):
        if not self.active:
            return

        self._render()

    def _render(
        self,
        force=False,
    ):
        now = time.monotonic()

        if not force:
            if (
                now - self._last_render
            ) < self._refresh_interval:
                return

        self._last_render = now

        if self.page == self.PAGE_RAM:
            self._render_ram()

        elif self.page == self.PAGE_UPTIME:
            self._render_uptime()

        elif self.page == self.PAGE_USB:
            self._render_usb()

        elif self.page == self.PAGE_VERSION:
            self._render_version()

    def _render_ram(self):
        free_ram = gc.mem_free()

        # Approximate scale for the current RP2350/CircuitPython
        # environment. Clamp between 0 and the LED count.
        estimated_total = 520000

        lit = (
            free_ram
            * self.led.pixel_count
            // estimated_total
        )

        if lit < 1:
            lit = 1

        if lit > self.led.pixel_count:
            lit = self.led.pixel_count

        self.led.off()

        for index in range(
            lit
        ):
            self.led.set_pixel(
                index,
                (
                    0,
                    255,
                    0,
                ),
            )

        self.log.info(
            "RAM free: {} bytes".format(
                free_ram
            )
        )

    def _render_uptime(self):
        uptime = int(
            time.monotonic()
        )

        position = (
            uptime
            % self.led.pixel_count
        )

        self.led.off()

        self.led.set_pixel(
            position,
            (
                0,
                0,
                255,
            ),
        )

        self.log.info(
            "Uptime: {} seconds".format(
                uptime
            )
        )

    def _render_usb(self):
        connected = (
            supervisor.runtime.usb_connected
        )

        if connected:
            self.led.green()
        else:
            self.led.red()

        self.log.info(
            "USB connected: {}".format(
                connected
            )
        )

    def _render_version(self):
        self.led.magenta()

        self.log.info(
            "BadgeOS {} ({})".format(
                VERSION,
                CODENAME,
            )
        )

    def stop(self):
        self.events.unsubscribe(
            "button.short_press",
            self._on_short_press,
        )

        self.led.off()

        self.log.info(
            "Diagnostics mode stopped"
        )

        super().stop()
