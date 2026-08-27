#!/usr/bin/env python3
"""
BadgeOS Deployment Tools

upload_file.py

Upload a single file to a BadgeOS device over the CircuitPython
USB CDC Raw REPL.

Example:

    python upload_file.py firmware/code.py /code.py

"""

from __future__ import annotations

import argparse
from pathlib import Path
import posixpath

from serial_connection import SerialConnection
from repl import REPL


def ensure_remote_directories(repl: REPL, remote_path: str):
    """
    Create every directory needed for a remote file.

    Example:

        /badgeos/services/heartbeat.py

    becomes

        /badgeos
        /badgeos/services
    """

    directory = posixpath.dirname(remote_path)

    if directory in ("", "/"):
        return

    parts = directory.strip("/").split("/")

    current = ""

    for part in parts:
        current += "/" + part
        repl.mkdir(current)


def main():

    parser = argparse.ArgumentParser(
        description="Upload one file to a BadgeOS device."
    )

    parser.add_argument(
        "local_file",
        help="Local source file",
    )

    parser.add_argument(
        "remote_file",
        help="Destination path on CIRCUITPY",
    )

    args = parser.parse_args()

    local = Path(args.local_file)

    if not local.exists():
        raise SystemExit(
            f"File not found: {local}"
        )

    print(f"Connecting to badge...")

    with SerialConnection() as connection:

        repl = REPL(connection)

        print("Interrupting running program...")
        repl.interrupt()

        print("Entering Raw REPL...")
        repl.enter_raw()

        print("Creating directories...")
        ensure_remote_directories(
            repl,
            args.remote_file,
        )

        print(
            f"Uploading {local.name}..."
        )

        repl.upload(
            local,
            args.remote_file,
        )

        print("Upload complete.")

        print("Leaving Raw REPL...")
        repl.exit_raw()

        print("Soft rebooting badge...")
        repl.soft_reset()

    print("Done.")


if __name__ == "__main__":
    main()
