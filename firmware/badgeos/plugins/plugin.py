"""
Base class for BadgeOS plugins.
"""


class Plugin:

    name = "Plugin"

    description = ""

    version = "0.1"

    def initialize(self):
        pass

    def update(self):
        pass

    def shutdown(self):
        pass
