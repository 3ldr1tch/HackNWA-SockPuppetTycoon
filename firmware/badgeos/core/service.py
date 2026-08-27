"""
BadgeOS Service Base Class

Common lifecycle interface for BadgeOS services.
"""

from badgeos.logger import get_logger


class Service:
    """
    Base class for scheduler-managed BadgeOS services.
    """

    def __init__(self, name=None):
        self.name = name or self.__class__.__name__

        self.enabled = True
        self.initialized = False

        self.log = get_logger(self.name)

    def initialize(self):
        """
        Initialize the service.

        Subclasses may override this method.
        """

        self.initialized = True

    def update(self):
        """
        Execute one scheduler update.

        Subclasses override this method.
        """

        pass

    def shutdown(self):
        """
        Shut down the service.

        Subclasses may override this method.
        """

        self.initialized = False

    def enable(self):
        self.enabled = True
        self.log.info("Enabled")

    def disable(self):
        self.enabled = False
        self.log.info("Disabled")

    def toggle(self):
        if self.enabled:
            self.disable()
        else:
            self.enable()

    @property
    def status(self):
        return {
            "name": self.name,
            "enabled": self.enabled,
            "initialized": self.initialized,
        }

    def __repr__(self):
        return (
            "<Service name='{}' enabled={} initialized={}>".format(
                self.name,
                self.enabled,
                self.initialized,
            )
        )
