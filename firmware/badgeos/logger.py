"""
BadgeOS logging.

A lightweight logger suitable for CircuitPython.
"""

import time

DEBUG = 10
INFO = 20
WARNING = 30
ERROR = 40

_LEVEL_NAMES = {
    DEBUG: "DEBUG",
    INFO: "INFO",
    WARNING: "WARN",
    ERROR: "ERROR",
}


class Logger:

    def __init__(self, name):

        self.name = name

        self.level = INFO

    def log(self, level, message):

        if level < self.level:
            return

        timestamp = int(time.monotonic())

        print(
            f"[{timestamp:6}] "
            f"{_LEVEL_NAMES[level]:5} "
            f"{self.name}: "
            f"{message}"
        )

    def debug(self, message):
        self.log(DEBUG, message)

    def info(self, message):
        self.log(INFO, message)

    def warning(self, message):
        self.log(WARNING, message)

    def error(self, message):
        self.log(ERROR, message)


_loggers = {}


def get_logger(name):

    if name not in _loggers:
        _loggers[name] = Logger(name)

    return _loggers[name]
