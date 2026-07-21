"""
BadgeOS Service Base Class

Defines the common lifecycle for all BadgeOS services.

Every long-running subsystem should inherit from Service and
override the methods it needs.

Version:
    0.1.0-dev
"""

from badgeos.logger import get_logger


class Service:
    """
    Base class for BadgeOS services.

    Lifecycle:

        initialize()
            Called once when the scheduler starts.

        update()
            Called every scheduler tick while enabled.

        shutdown()
            Called once when the scheduler stops.
    """

    def __init__(self, name=None):
        """
        Initialize the service.

        Parameters
        ----------
        name : str, optional
            Human-readable service name.
        """

        self.name = name or self.__class__.__name__
        self.enabled = True
        self.initialized = False

        self.log = get_logger(self.name)

    # ---------------------------------------------------------
    # Lifecycle
    # ---------------------------------------------------------

    def initialize(self):
        """
        Initialize the service.

        Override in subclasses.
        """

        self.initialized = True

    def update(self):
        """
        Execute one scheduler tick.

        Override in subclasses.
        """

        pass

    def shutdown(self):
        """
        Shutdown the service.

        Override in subclasses.
        """

        self.initialized = False

    # ---------------------------------------------------------
    # State
    # ---------------------------------------------------------

    def enable(self):
        """
        Enable scheduler updates.
        """

        self.enabled = True
        self.log.info("Enabled")

    def disable(self):
        """
        Disable scheduler updates.
        """

        self.enabled = False
        self.log.info("Disabled")

    def toggle(self):
        """
        Toggle enabled state.
        """

        if self.enabled:
            self.disable()
        else:
            self.enable()

    # ---------------------------------------------------------
    # Information
    # ---------------------------------------------------------

    @property
    def status(self):
        """
        Return service status information.
        """

        return {
            "name": self.name,
            "enabled": self.enabled,
            "initialized": self.initialized,
        }

    def __repr__(self):
        """
        Developer-friendly representation.
        """

        return (
            f"<Service "
            f"name='{self.name}' "
            f"enabled={self.enabled} "
            f"initialized={self.initialized}>"
        )
