"""
Lightweight BadgeOS logger for CircuitPython.
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
    """Minimal serial-console logger."""

    def __init__(self, name, level=INFO):
        self.name = name
        self.level = level

    def log(self, level, message):
        if level < self.level:
            return

        timestamp = int(time.monotonic())

        print(
            "[{:6}] {:5} {}: {}".format(
                timestamp,
                _LEVEL_NAMES.get(level, "LOG"),
                self.name,
                message,
            )
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
    """Return a shared logger for *name*."""

    if name not in _loggers:
        _loggers[name] = Logger(name)

    return _loggers[name]
