"""
BadgeOS Event Bus.

Provides lightweight synchronous event delivery between BadgeOS
subsystems without requiring services to know about one another.
"""


class EventBus:
    """Simple publish/subscribe event bus."""

    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_name, callback):
        if event_name not in self._subscribers:
            self._subscribers[event_name] = []

        if callback not in self._subscribers[event_name]:
            self._subscribers[event_name].append(callback)

    def unsubscribe(self, event_name, callback):
        if event_name not in self._subscribers:
            return

        callbacks = self._subscribers[event_name]

        if callback in callbacks:
            callbacks.remove(callback)

        if not callbacks:
            del self._subscribers[event_name]

    def publish(self, event_name, data=None):
        if event_name not in self._subscribers:
            return

        if data is None:
            data = {}

        callbacks = list(
            self._subscribers[event_name]
        )

        for callback in callbacks:
            callback(
                event_name,
                data,
            )
