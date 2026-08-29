"""
BadgeOS Mode Manager Service.

Owns the currently active interactive mode and provides a controlled
lifecycle for switching between BadgeOS modes.
"""

from badgeos.core import Mode
from badgeos.core import Service


class ModeManagerService(Service):
    """Manage the currently active BadgeOS mode."""

    def __init__(self):
        super().__init__("ModeManager")

        self.current_mode = None
        self._pending_mode = None

    def initialize(self):
        super().initialize()

        self.log.info(
            "Mode manager initialized"
        )

        if self._pending_mode is not None:
            mode = self._pending_mode
            self._pending_mode = None
            self.set_mode(mode)

    def set_mode(self, mode):
        if not isinstance(mode, Mode):
            raise TypeError(
                "Mode must inherit from Mode."
            )

        if not self.initialized:
            self._pending_mode = mode

            self.log.info(
                "Queued initial mode: {}".format(
                    mode.name
                )
            )

            return

        if self.current_mode is mode:
            return

        if self.current_mode is not None:
            self.log.info(
                "Stopping mode: {}".format(
                    self.current_mode.name
                )
            )

            self.current_mode.stop()

        self.current_mode = mode

        self.log.info(
            "Starting mode: {}".format(
                self.current_mode.name
            )
        )

        self.current_mode.start()

    def clear_mode(self):
        if self.current_mode is None:
            return

        self.log.info(
            "Stopping mode: {}".format(
                self.current_mode.name
            )
        )

        self.current_mode.stop()
        self.current_mode = None

    def update(self):
        if self.current_mode is None:
            return

        if not self.current_mode.active:
            return

        self.current_mode.update()

    def shutdown(self):
        self.clear_mode()

        self.log.info(
            "Mode manager stopped"
        )

        super().shutdown()
