import logging
from typing import Callable, Dict, List

from nexus.domain.events import Event

logger = logging.getLogger(__name__)


class EventBus:
    def __init__(self):
        self._listeners: Dict[str, List[Callable[[Event], None]]] = {}

    def subscribe(self, event_name: str, callback: Callable[[Event], None]):
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        self._listeners[event_name].append(callback)

    def publish(self, event: Event):
        logger.info(f"[BUS] Event published: {event.name}")
        if event.name in self._listeners:
            for callback in self._listeners[event.name]:
                callback(event)
