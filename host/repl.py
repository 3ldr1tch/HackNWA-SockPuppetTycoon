"""
BadgeOS Deployment Tools

repl.py

High-level interface to the CircuitPython REPL.

This module builds on SerialConnection and provides methods for:

    • Interrupting running code
    • Entering the REPL
    • Entering Raw REPL
    • Executing Python remotely
    • Soft rebooting
    • Reading output

This module intentionally does NOT know anything about BadgeOS or
deployment.
"""

from __future__ import annotations

import time

from serial_connection import SerialConnection


CTRL_A = b"\x01"      # Raw REPL
CTRL_B = b"\x02"      # Normal REPL
CTRL_C = b"\x03"      # KeyboardInterrupt
CTRL_D = b"\x04"      # Soft reset / Execute raw REPL


class REPL:

    def __init__(self, connection: SerialConnection):

        self.connection = connection

    # ---------------------------------------------------------

    def interrupt(self):

        """
        Stop any currently running program.
        """

        self.connection.write(CTRL_C)
        time.sleep(0.1)

        self.connection.write(CTRL_C)
        time.sleep(0.1)

    # ---------------------------------------------------------

    def enter_raw(self):

        """
        Switch into Raw REPL.
        """

        self.connection.write(CTRL_A)

        self.connection.read_until(
            b"raw REPL"
        )

    # ---------------------------------------------------------

    def exit_raw(self):

        self.connection.write(CTRL_B)

    # ---------------------------------------------------------

    def soft_reset(self):

        self.connection.write(CTRL_D)

    # ---------------------------------------------------------

    def execute(self, code: str) -> bytes:

        """
        Execute Python code in Raw REPL.

        Returns stdout/stderr bytes.
        """

        if not code.endswith("\n"):
            code += "\n"

        self.connection.write(code.encode())

        self.connection.write(CTRL_D)

        return self.connection.read_until(
            b"\x04>"
        )

    # ---------------------------------------------------------

    def run(self, code: str) -> str:

        """
        Execute Python and return decoded text.
        """

        output = self.execute(code)

        return output.decode(
            "utf-8",
            errors="replace"
        )
