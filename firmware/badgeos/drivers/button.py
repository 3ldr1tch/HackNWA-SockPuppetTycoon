"""
BadgeOS Button Driver

Debounced digital input driver for momentary buttons.

A typical button is wired between a GPIO pin and ground. The driver
enables the internal pull-up resistor, making the electrical states:

    released -> HIGH
    pressed  -> LOW

The active_low option can be disabled for alternate wiring.
"""

import time

import digitalio


class ButtonDriver:
    def __init__(
        self,
        pin,
        name="Button",
        debounce_ms=30,
        active_low=True,
    ):
        self.name = name
        self.debounce_ms = debounce_ms
        self.active_low = active_low

        self._io = digitalio.DigitalInOut(pin)
        self._io.direction = digitalio.Direction.INPUT

        if active_low:
            self._io.pull = digitalio.Pull.UP
        else:
            self._io.pull = digitalio.Pull.DOWN

        self._raw_state = self._read_pressed()
        self._stable_state = self._raw_state

        self._last_change = time.monotonic()

        self._pressed_event = False
        self._released_event = False

    def _read_pressed(self):
        value = self._io.value

        if self.active_low:
            return not value

        return value

    def update(self):
        now = time.monotonic()
        raw_state = self._read_pressed()

        if raw_state != self._raw_state:
            self._raw_state = raw_state
            self._last_change = now

        elapsed_ms = (now - self._last_change) * 1000

        if (
            raw_state != self._stable_state
            and elapsed_ms >= self.debounce_ms
        ):
            self._stable_state = raw_state

            if self._stable_state:
                self._pressed_event = True
            else:
                self._released_event = True

    @property
    def pressed(self):
        return self._stable_state

    def was_pressed(self):
        if not self._pressed_event:
            return False

        self._pressed_event = False
        return True

    def was_released(self):
        if not self._released_event:
            return False

        self._released_event = False
        return True

    def deinit(self):
        if self._io is not None:
            self._io.deinit()
            self._io = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.deinit()
