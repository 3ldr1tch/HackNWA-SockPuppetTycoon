"""
Main BadgeOS application.
"""

import gc
import sys

from badgeos.core import Scheduler, HeartbeatService
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


def main():

    startup()

    scheduler = Scheduler()

    scheduler.register(
        HeartbeatService(interval=1.0)
    )

    scheduler.run()
