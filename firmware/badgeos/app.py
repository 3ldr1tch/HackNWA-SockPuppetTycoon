"""
Main BadgeOS application.
"""

import gc
import sys
import time

from badgeos.logger import get_logger
from badgeos.version import VERSION, CODENAME

log = get_logger("APP")


def startup():

    print()

    print("=" * 60)
    print("BadgeOS")
    print(VERSION)
    print(CODENAME)
    print("=" * 60)

    print()

    print(sys.version)

    print()

    log.info("Startup complete")

    log.info(f"Free RAM: {gc.mem_free()} bytes")

    print()


def scheduler():

    while True:

        time.sleep(0.05)


def main():

    startup()

    scheduler()
