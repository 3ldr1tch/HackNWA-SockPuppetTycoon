"""
BadgeOS

Main application entry point.
"""

import gc
import sys

from badgeos.core import Scheduler
from badgeos.logger import get_logger
from badgeos.services import HeartbeatService
from badgeos.version import VERSION, CODENAME

log = get_logger("APP")


def startup():
    """
    Display startup information.
    """

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


def build_scheduler():
    """
    Create and configure the BadgeOS scheduler.
    """

    scheduler = Scheduler()

    scheduler.register(
        HeartbeatService(interval=1.0)
    )

    return scheduler


def main():
    """
    BadgeOS entry point.
    """

    startup()

    scheduler = build_scheduler()

    scheduler.run()
