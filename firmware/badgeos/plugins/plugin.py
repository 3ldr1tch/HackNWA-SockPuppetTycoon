"""
BadgeOS

plugin.py

Base class for all BadgeOS plugins.
"""


class Plugin:
    """
    Base plugin class.

    Plugins may override any lifecycle method.
    """

    name = "Plugin"
    version = "0.0.1"

    def initialize(self, app):
        """
        Called once when the plugin is registered.
        """
        pass

    def start(self):
        """
        Called when plugins are started.
        """
        pass

    def stop(self):
        """
        Called before shutdown.
        """
        pass
