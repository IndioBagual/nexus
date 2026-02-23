from collections.abc import Callable

from nexus.domain.events import Event


class EventBus:
    def __init__(self):
        self._listeners: dict[str, list[Callable[[Event], None]]] = {}

    def subscribe(self, event_name: str, callback: Callable[[Event], None]):
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(callback)

    def publish(self, event: Event):
        print(f"[BUS] Event published: {event.name}")
        if event.name in self._listeners:
            for callback in self._listeners[event.name]:
                callback(event)
