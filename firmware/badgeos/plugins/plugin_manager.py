"""
BadgeOS

plugin_manager.py

Plugin manager for BadgeOS.
"""

from badgeos.logger import get_logger


log = get_logger("PLUGIN")


class PluginManager:
    """
    Manage registered BadgeOS plugins.
    """

    def __init__(self, app):
        self.app = app
        self.plugins = []

    def register(self, plugin):
        plugin.initialize(self.app)
        self.plugins.append(plugin)

        log.info(
            "Registered plugin: {}".format(plugin.name)
        )

    def start(self):
        for plugin in self.plugins:
            plugin.start()

        log.info(
            "Started {} plugins".format(
                len(self.plugins)
            )
        )

    def stop(self):
        for plugin in reversed(self.plugins):
            plugin.stop()

        log.info("Plugins stopped")
