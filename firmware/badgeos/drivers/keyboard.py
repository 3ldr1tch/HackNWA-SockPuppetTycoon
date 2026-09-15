"""
BadgeOS USB Keyboard Driver.

Minimal USB HID keyboard implementation using CircuitPython's
built-in usb_hid module.

Supports:
    - printable US keyboard characters
    - modifier keys
    - hotkeys
    - Enter / Tab / Escape
    - Windows / Command / GUI key
"""

import time
import usb_hid


class KeyboardDriver:
    """Minimal USB HID keyboard driver."""

    MOD_LEFT_CTRL = 0x01
    MOD_LEFT_SHIFT = 0x02
    MOD_LEFT_ALT = 0x04
    MOD_LEFT_GUI = 0x08

    KEY_ENTER = 0x28
    KEY_ESCAPE = 0x29
    KEY_BACKSPACE = 0x2A
    KEY_TAB = 0x2B
    KEY_SPACE = 0x2C

    KEYCODES = {
        "a": 0x04,
        "b": 0x05,
        "c": 0x06,
        "d": 0x07,
        "e": 0x08,
        "f": 0x09,
        "g": 0x0A,
        "h": 0x0B,
        "i": 0x0C,
        "j": 0x0D,
        "k": 0x0E,
        "l": 0x0F,
        "m": 0x10,
        "n": 0x11,
        "o": 0x12,
        "p": 0x13,
        "q": 0x14,
        "r": 0x15,
        "s": 0x16,
        "t": 0x17,
        "u": 0x18,
        "v": 0x19,
        "w": 0x1A,
        "x": 0x1B,
        "y": 0x1C,
        "z": 0x1D,

        "1": 0x1E,
        "2": 0x1F,
        "3": 0x20,
        "4": 0x21,
        "5": 0x22,
        "6": 0x23,
        "7": 0x24,
        "8": 0x25,
        "9": 0x26,
        "0": 0x27,

        "\n": 0x28,
        "\t": 0x2B,
        " ": 0x2C,
        "-": 0x2D,
        "=": 0x2E,
        "[": 0x2F,
        "]": 0x30,
        "\\": 0x31,
        ";": 0x33,
        "'": 0x34,
        "`": 0x35,
        ",": 0x36,
        ".": 0x37,
        "/": 0x38,
    }

    SHIFTED = {
        "!": "1",
        "@": "2",
        "#": "3",
        "$": "4",
        "%": "5",
        "^": "6",
        "&": "7",
        "*": "8",
        "(": "9",
        ")": "0",
        "_": "-",
        "+": "=",
        "{": "[",
        "}": "]",
        "|": "\\",
        ":": ";",
        '"': "'",
        "~": "`",
        "<": ",",
        ">": ".",
        "?": "/",
    }

    def __init__(
        self,
        key_delay=0.02,
    ):
        self.key_delay = key_delay

        self.device = self._find_keyboard()

        if self.device is None:
            raise RuntimeError(
                "USB HID keyboard device not available."
            )

        self.release_all()

    def _find_keyboard(self):
        for device in usb_hid.devices:
            if (
                device.usage_page == 0x01
                and device.usage == 0x06
            ):
                return device

        return None

    def _send_report(
        self,
        modifier=0,
        keycodes=None,
    ):
        if keycodes is None:
            keycodes = ()

        report = bytearray(8)

        report[0] = modifier
        report[1] = 0

        index = 2

        for keycode in keycodes:
            if index >= 8:
                break

            report[index] = keycode
            index += 1

        self.device.send_report(
            report
        )

    def release_all(self):
        self.device.send_report(
            bytearray(8)
        )

    def tap_key(
        self,
        keycode,
        modifier=0,
    ):
        self._send_report(
            modifier,
            (
                keycode,
            ),
        )

        time.sleep(
            self.key_delay
        )

        self.release_all()

        time.sleep(
            self.key_delay
        )

    def hotkey(
        self,
        modifier,
        keycode,
    ):
        """
        Send a modifier + key combination.
        """

        self.tap_key(
            keycode,
            modifier=modifier,
        )

    def press_character(
        self,
        character,
    ):
        modifier = 0
        lookup = character

        if (
            character >= "A"
            and character <= "Z"
        ):
            modifier = (
                self.MOD_LEFT_SHIFT
            )

            lookup = character.lower()

        elif character in self.SHIFTED:
            modifier = (
                self.MOD_LEFT_SHIFT
            )

            lookup = self.SHIFTED[
                character
            ]

        if lookup not in self.KEYCODES:
            raise ValueError(
                "Unsupported keyboard character: {!r}".format(
                    character
                )
            )

        self.tap_key(
            self.KEYCODES[
                lookup
            ],
            modifier=modifier,
        )

    def write(
        self,
        text,
    ):
        """
        Type a string as USB keyboard input.
        """

        for character in text:
            self.press_character(
                character
            )

    def enter(self):
        self.tap_key(
            self.KEY_ENTER
        )

    def escape(self):
        self.tap_key(
            self.KEY_ESCAPE
        )

    def deinit(self):
        self.release_all()
