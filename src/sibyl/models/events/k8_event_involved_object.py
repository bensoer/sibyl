
from dataclasses import dataclass

@dataclass
class K8EventInvolvedObject:
    """
    Data class representing the involved object of a Kubernetes event.
    """
    kind: str
    name: str
    namespace: str