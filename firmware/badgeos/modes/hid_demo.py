"""
BadgeOS USB HID Demo Mode.

Demonstrates the badge acting as a USB keyboard.

A short press launches a harmless website using an OS-specific
keyboard sequence.

Long-press mode switching is handled globally by ModeSwitchService.

USB HID does not provide a reliable cross-platform mechanism for
detecting the host operating system, so the demo currently uses a
configurable host profile.
"""

import time

from badgeos.core import Mode
from badgeos.drivers import KeyboardDriver
from badgeos.logger import get_logger


class HIDDemoMode(Mode):
    """USB HID browser-launch demonstration."""

    # ---------------------------------------------------------
    # Demo configuration
    # ---------------------------------------------------------

    HOST_PROFILE = "linux"

    TARGET_URL = "https://seccon.com"

    COLOR_READY = (
        255,
        0,
        255,
    )

    COLOR_SENDING = (
        255,
        180,
        0,
    )

    COLOR_SUCCESS = (
        0,
        255,
        0,
    )

    COLOR_ERROR = (
        255,
        0,
        0,
    )

    def __init__(
        self,
        events,
        led,
    ):
        super().__init__(
            "HIDDemo"
        )

        self.events = events
        self.led = led

        self.log = get_logger(
            self.name
        )

        self.keyboard = None

        self._send_count = 0

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def start(self):
        super().start()

        self._send_count = 0

        try:
            self.keyboard = (
                KeyboardDriver()
            )

        except Exception as exc:
            self.keyboard = None

            self.log.error(
                "Keyboard initialization failed: {}".format(
                    exc
                )
            )

            self.led.fill(
                self.COLOR_ERROR
            )

            return

        self.events.subscribe(
            "button.short_press",
            self._on_short_press,
        )

        self._show_ready()

        self.log.info(
            "HID demo started"
        )

        self.log.info(
            "Host profile: {}".format(
                self.HOST_PROFILE
            )
        )

        self.log.info(
            "Target URL: {}".format(
                self.TARGET_URL
            )
        )

        self.log.info(
            "Short press launches browser"
        )

    def stop(self):
        self.events.unsubscribe(
            "button.short_press",
            self._on_short_press,
        )

        if self.keyboard is not None:
            self.keyboard.deinit()
            self.keyboard = None

        self.led.off()

        self.log.info(
            "HID demo stopped"
        )

        super().stop()

    # ---------------------------------------------------------
    # Input
    # ---------------------------------------------------------

    def _on_short_press(
        self,
        event_name,
        data,
    ):
        if not self.active:
            return

        if self.keyboard is None:
            self.log.error(
                "Keyboard unavailable"
            )

            return

        self._send_count += 1

        self.log.info(
            "Launching browser #{}".format(
                self._send_count
            )
        )

        self.led.fill(
            self.COLOR_SENDING
        )

        try:
            self._launch_browser()

            self.led.fill(
                self.COLOR_SUCCESS
            )

            time.sleep(
                0.20
            )

            self._show_ready()

            self.log.info(
                "Browser launch sequence complete"
            )

        except Exception as exc:
            self.led.fill(
                self.COLOR_ERROR
            )

            self.log.error(
                "HID sequence failed: {}".format(
                    exc
                )
            )

    # ---------------------------------------------------------
    # Browser launch
    # ---------------------------------------------------------

    def _launch_browser(self):
        profile = (
            self.HOST_PROFILE.lower()
        )

        if profile == "linux":
            self._launch_linux()

        elif profile == "windows":
            self._launch_windows()

        elif profile in (
            "mac",
            "macos",
        ):
            self._launch_macos()

        else:
            raise ValueError(
                "Unknown HID host profile: {}".format(
                    self.HOST_PROFILE
                )
            )

    def _launch_linux(self):
        """
        Linux demo:

            Ctrl+Alt+T
            xdg-open <URL>
            Enter
        """

        self.keyboard._send_report(
            (
                self.keyboard.MOD_LEFT_CTRL
                | self.keyboard.MOD_LEFT_ALT
            ),
            (
                self.keyboard.KEYCODES[
                    "t"
                ],
            ),
        )

        time.sleep(
            0.10
        )

        self.keyboard.release_all()

        time.sleep(
            0.75
        )

        self.keyboard.write(
            "xdg-open "
        )

        self.keyboard.write(
            self.TARGET_URL
        )

        self.keyboard.enter()

    def _launch_windows(self):
        """
        Windows demo:

            Win+R
            <URL>
            Enter
        """

        self.keyboard.hotkey(
            self.keyboard.MOD_LEFT_GUI,
            self.keyboard.KEYCODES[
                "r"
            ],
        )

        time.sleep(
            0.50
        )

        self.keyboard.write(
            self.TARGET_URL
        )

        self.keyboard.enter()

    def _launch_macos(self):
        """
        macOS demo:

            Command+Space
            <URL>
            Enter
        """

        self.keyboard.hotkey(
            self.keyboard.MOD_LEFT_GUI,
            self.keyboard.KEY_SPACE,
        )

        time.sleep(
            0.50
        )

        self.keyboard.write(
            self.TARGET_URL
        )

        self.keyboard.enter()

    # ---------------------------------------------------------
    # Display
    # ---------------------------------------------------------

    def _show_ready(self):
        self.led.off()

        self.led.set_pixel(
            0,
            self.COLOR_READY,
        )

    def update(self):
        pass
