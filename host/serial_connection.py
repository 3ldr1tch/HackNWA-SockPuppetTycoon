"""
BadgeOS Deployment Tools

serial_connection.py

Low-level serial transport for communicating with the Badge over
CircuitPython's USB CDC interface.

This module is intentionally unaware of the REPL protocol. Its only
responsibility is opening the port, sending bytes, and receiving bytes.
"""

from __future__ import annotations

import glob
import time
from pathlib import Path

import serial

DEFAULT_BAUDRATE = 115200

DEVICE_PATTERNS = (
    "/dev/serial/by-id/*Pico*",
    "/dev/ttyACM*",
)


class SerialConnection:
    """Low-level serial connection to the badge."""

    def __init__(
        self,
        port: str | None = None,
        baudrate: int = DEFAULT_BAUDRATE,
        timeout: float = 1.0,
    ):

        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self._serial: serial.Serial | None = None

    @staticmethod
    def discover() -> str:
        """
        Locate the badge's serial port.

        Returns:
            Path to the serial device.
        """

        for pattern in DEVICE_PATTERNS:
            matches = sorted(glob.glob(pattern))

            if matches:
                return matches[0]

        raise RuntimeError(
            "No CircuitPython serial device found."
        )

    def connect(self):

        if self.port is None:
            self.port = self.discover()

        self._serial = serial.Serial(
            self.port,
            self.baudrate,
            timeout=self.timeout,
        )

        # Allow the port to settle.
        time.sleep(0.25)

        self._serial.reset_input_buffer()
        self._serial.reset_output_buffer()

    def disconnect(self):

        if self._serial is not None:
            self._serial.close()
            self._serial = None

    @property
    def connected(self) -> bool:

        return (
            self._serial is not None
            and self._serial.is_open
        )

    def write(self, data: bytes | str):

        if not self.connected:
            raise RuntimeError("Serial port is not connected.")

        if isinstance(data, str):
            data = data.encode("utf-8")

        self._serial.write(data)

    def read(self, size: int = 1) -> bytes:

        if not self.connected:
            raise RuntimeError("Serial port is not connected.")

        return self._serial.read(size)

    def readline(self) -> bytes:

        if not self.connected:
            raise RuntimeError("Serial port is not connected.")

        return self._serial.readline()

    def read_until(
        self,
        marker: bytes,
        timeout: float = 5.0,
    ) -> bytes:

        if not self.connected:
            raise RuntimeError("Serial port is not connected.")

        deadline = time.time() + timeout

        buffer = bytearray()

        while time.time() < deadline:

            chunk = self._serial.read(1)

            if chunk:
                buffer.extend(chunk)

                if marker in buffer:
                    return bytes(buffer)

        raise TimeoutError(
            f"Timed out waiting for {marker!r}"
        )

    def flush(self):

        if self.connected:
            self._serial.flush()

    def __enter__(self):

        self.connect()
        return self

    def __exit__(self, exc_type, exc, tb):

        self.disconnect()
