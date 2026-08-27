"""
BadgeOS entry point.
"""

import sys

from badgeos.application import Application
from badgeos.logger import get_logger
from badgeos.version import CODENAME, VERSION

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


def main():

    startup()

    app = Application()

    app.run()
