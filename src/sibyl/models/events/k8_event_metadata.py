
from dataclasses import dataclass
from typing import Optional

@dataclass
class K8EventMetadata:
    """
    Data class representing the metadata of a Kubernetes event.
    """
    name: str
    namespace: str
    creation_timestamp: Optional[str]
    deletion_timestamp: Optional[str]