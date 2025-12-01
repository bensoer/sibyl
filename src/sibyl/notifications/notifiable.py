

from abc import ABC, abstractmethod
from typing import List, Optional

from sibyl.models.events.k8_event import K8Event


class Notifiable(ABC):

    @abstractmethod
    def notify(self, event_data: K8Event, logs: List[tuple[str,str]] = []) -> None:
        """Send a notification based on the event data."""
        pass