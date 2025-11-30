
from dataclasses import dataclass

@dataclass
class K8EventSource:
    """
    Data class representing the source of a Kubernetes event.
    """
    component: str
    host: str