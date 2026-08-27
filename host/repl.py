"""
BadgeOS Deployment Tools

repl.py

High-level interface to the CircuitPython REPL.

This module builds on SerialConnection and provides methods for:

    - Interrupting running code
    - Entering the REPL
    - Entering Raw REPL
    - Executing Python remotely
    - Soft rebooting
    - Uploading files
"""

from __future__ import annotations

import base64
from pathlib import Path
import time

from serial_connection import SerialConnection


CTRL_A = b"\x01"
CTRL_B = b"\x02"
CTRL_C = b"\x03"
CTRL_D = b"\x04"


class REPL:
    """High-level CircuitPython REPL interface."""

    def __init__(self, connection: SerialConnection):
        self.connection = connection

    def interrupt(self):
        """
        Stop any currently running CircuitPython program.
        """

        self.connection.write(CTRL_C)
        time.sleep(0.1)

        self.connection.write(CTRL_C)
        time.sleep(0.1)

    def enter_raw(self):
        """
        Enter CircuitPython Raw REPL mode.
        """

        self.connection.write(CTRL_A)

        self.connection.read_until(
            b"raw REPL",
            timeout=5.0,
        )

    def exit_raw(self):
        """
        Return from Raw REPL to the normal REPL.
        """

        self.connection.write(CTRL_B)

    def soft_reset(self):
        """
        Request a CircuitPython soft reset.
        """

        self.connection.write(CTRL_D)

    def execute(
        self,
        code: str,
        timeout: float = 5.0,
    ) -> bytes:
        """
        Execute Python code in Raw REPL.

        Parameters
        ----------
        code:
            Python source code to execute.

        timeout:
            Maximum number of seconds to wait for execution
            to complete.

        Returns
        -------
        bytes
            Raw REPL response bytes.
        """

        if not code.endswith("\n"):
            code += "\n"

        self.connection.write(
            code.encode("utf-8")
        )

        self.connection.write(CTRL_D)

        return self.connection.read_until(
            b"\x04>",
            timeout=timeout,
        )

    def run(
        self,
        code: str,
        timeout: float = 5.0,
    ) -> str:
        """
        Execute Python and return decoded output.
        """

        output = self.execute(
            code,
            timeout=timeout,
        )

        return output.decode(
            "utf-8",
            errors="replace",
        )

    def run_lines(self, *lines: str) -> str:
        """
        Execute multiple Python statements in one Raw REPL execution.
        """

        code = "\n".join(lines)

        return self.run(code)

    def mkdir(self, path: str):
        """
        Create a directory on the badge if it does not already exist.
        """

        self.run_lines(
            "import os",
            "path = {!r}".format(path),
            "try:",
            "    os.mkdir(path)",
            "except OSError:",
            "    pass",
        )

    def write_file(
        self,
        remote_path: str,
        data: bytes,
        chunk_size: int = 256,
    ):
        """
        Upload binary data to a file on the badge.

        Data is Base64-encoded on the host and decoded on the badge.
        """

        encoded = base64.b64encode(data).decode("ascii")

        # Each command is self-contained so no remote file handle needs
        # to survive between separate Raw REPL executions.
        self.run(
            "open({!r}, 'wb').close()".format(
                remote_path
            )
        )

        for offset in range(
            0,
            len(encoded),
            chunk_size,
        ):
            chunk = encoded[
                offset:offset + chunk_size
            ]

            code = (
                "import binascii\n"
                "f = open({!r}, 'ab')\n"
                "f.write(binascii.a2b_base64({!r}))\n"
                "f.close()"
            ).format(
                remote_path,
                chunk,
            )

            self.run(
                code,
                timeout=10.0,
            )

    def write_text_file(
        self,
        remote_path: str,
        text: str,
    ):
        """
        Upload UTF-8 text to a file on the badge.
        """

        self.write_file(
            remote_path,
            text.encode("utf-8"),
        )

    def upload(
        self,
        local_file: str | Path,
        remote_file: str,
    ):
        """
        Upload a local file to the badge.
        """

        local_file = Path(local_file)

        if not local_file.is_file():
            raise FileNotFoundError(
                "Local file not found: {}".format(
                    local_file
                )
            )

        self.write_file(
            remote_file,
            local_file.read_bytes(),
        )
