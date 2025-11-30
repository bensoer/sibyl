

from dataclasses import dataclass

from sibyl.models.events.k8_event_involved_object import K8EventInvolvedObject
from sibyl.models.events.k8_event_metadata import K8EventMetadata
from sibyl.models.events.k8_event_source import K8EventSource


'''
        return {
            "kind": k8s_event.kind,
            "source": {
                "component": k8s_event.source.component,
                "host": k8s_event.source.host,
            },
            "action": k8s_event.action,
            "type": k8s_event.type,
            "namespace": k8s_event.metadata.namespace,
            "name" : k8s_event.metadata.name,
            "reason": k8s_event.reason,
            "message": k8s_event.message,
            "metadata": {
                "name": k8s_event.metadata.name,
                "namespace": k8s_event.metadata.namespace,
                "creation_timestamp": k8s_event.metadata.creation_timestamp.isoformat() if k8s_event.metadata.creation_timestamp else "N/A",
                "deletion_timestamp": k8s_event.metadata.deletion_timestamp.isoformat() if k8s_event.metadata.deletion_timestamp else "N/A",
            },
            "involved_object": {
                "kind": k8s_event.involved_object.kind,
                "name": k8s_event.involved_object.name,
                "namespace": k8s_event.involved_object.namespace,
            },
            "timestamp": k8s_event.last_timestamp.isoformat() if k8s_event.last_timestamp else "N/A"
        }

'''

@dataclass
class K8Event:
    """
    Data class representing a Kubernetes event.
    """
    kind: str
    source: K8EventSource
    action: str
    type: str
    namespace: str
    name: str
    reason: str
    message: str
    metadata: K8EventMetadata
    involved_object: K8EventInvolvedObject
    timestamp: str


