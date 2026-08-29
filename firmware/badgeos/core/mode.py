"""
BadgeOS Mode Base Class.

Modes represent interactive BadgeOS states such as menus, games,
demos, and utilities.

A mode has a simple lifecycle:

    start()
    update()
    stop()
"""


class Mode:
    """Base class for BadgeOS interactive modes."""

    def __init__(self, name=None):
        self.name = name or self.__class__.__name__
        self.active = False

    def start(self):
        """Activate the mode."""

        self.active = True

    def update(self):
        """Perform periodic mode work."""

        pass

    def stop(self):
        """Deactivate the mode."""

        self.active = False

    @property
    def status(self):
        return {
            "name": self.name,
            "active": self.active,
        }

    def __repr__(self):
        return (
            "<Mode name='{}' active={}>".format(
                self.name,
                self.active,
            )
        )
