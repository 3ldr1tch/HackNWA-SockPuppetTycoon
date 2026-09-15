"""
BadgeOS Mode Manager Service.

Owns registered interactive modes and controls the lifecycle of the
currently active mode.
"""

from badgeos.core import Mode
from badgeos.core import Service


class ModeManagerService(Service):
    """Manage registered BadgeOS modes."""

    def __init__(self):
        super().__init__("ModeManager")

        self.current_mode = None

        self._pending_mode = None

        self._modes = []
        self._mode_lookup = {}

    def register_mode(self, mode):
        """
        Register a mode with the manager.
        """

        if not isinstance(mode, Mode):
            raise TypeError(
                "Mode must inherit from Mode."
            )

        key = mode.name.lower()

        if key in self._mode_lookup:
            raise ValueError(
                "Mode already registered: {}".format(
                    mode.name
                )
            )

        self._modes.append(
            mode
        )

        self._mode_lookup[key] = mode

        self.log.info(
            "Registered mode: {}".format(
                mode.name
            )
        )

    def modes(self):
        """
        Return the registered modes.
        """

        return tuple(
            self._modes
        )

    def mode_names(self):
        """
        Return registered mode names.
        """

        names = []

        for mode in self._modes:
            names.append(
                mode.name
            )

        return tuple(
            names
        )

    def get_mode(self, name):
        """
        Look up a mode by name.

        Matching is case-insensitive.
        """

        if name is None:
            return None

        return self._mode_lookup.get(
            name.lower()
        )

    def initialize(self):
        super().initialize()

        self.log.info(
            "Mode manager initialized"
        )

        if self._pending_mode is not None:
            mode = self._pending_mode

            self._pending_mode = None

            self.set_mode(
                mode
            )

    def set_mode(self, mode):
        """
        Switch to a mode.

        mode may be either:

            Mode instance
            mode name string
        """

        if isinstance(mode, str):
            resolved = self.get_mode(
                mode
            )

            if resolved is None:
                raise ValueError(
                    "Unknown mode: {}".format(
                        mode
                    )
                )

            mode = resolved

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
