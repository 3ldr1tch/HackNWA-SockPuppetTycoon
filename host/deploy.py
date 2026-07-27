#!/usr/bin/env python3

"""
BadgeOS Deployment Tool
"""

from pathlib import Path

from serial_connection import SerialConnection
from repl import REPL
from uploader import Uploader


ROOT = Path(__file__).parent.parent
FIRMWARE = ROOT / "firmware"


def main():

    print("Connecting to Badge...")

    with SerialConnection() as conn:

        repl = REPL(conn)

        repl.interrupt()
        repl.enter_raw()

        uploader = Uploader(repl)

        print("Uploading boot.py")

        uploader.upload_text_file(
            FIRMWARE / "boot.py",
            "/boot.py",
        )

        print("Uploading code.py")

        uploader.upload_text_file(
            FIRMWARE / "code.py",
            "/code.py",
        )

        repl.exit_raw()

        repl.soft_reset()

        print("Done.")


if __name__ == "__main__":
    main()
