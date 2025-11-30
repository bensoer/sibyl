
import pytest
from sibyl.models.events.k8_event import K8Event
from sibyl.models.events.k8_event_involved_object import K8EventInvolvedObject
from sibyl.models.events.k8_event_metadata import K8EventMetadata
from sibyl.models.events.k8_event_source import K8EventSource

def test_k8_event_creation():
    """
    Test the creation of a K8Event.
    """
    source = K8EventSource(component="kubelet", host="minikube")
    metadata = K8EventMetadata(
        name="test-event",
        namespace="default",
        creation_timestamp="2025-11-30T12:00:00Z",
        deletion_timestamp=None
    )
    involved_object = K8EventInvolvedObject(
        kind="Pod",
        name="test-pod",
        namespace="default"
    )
    event = K8Event(
        kind="Event",
        source=source,
        action="Created",
        type="Normal",
        namespace="default",
        name="test-event",
        reason="PodCreated",
        message="Pod test-pod created",
        metadata=metadata,
        involved_object=involved_object,
        timestamp="2025-11-30T12:00:00Z"
    )
    assert event.kind == "Event"
    assert event.source == source
    assert event.action == "Created"
    assert event.type == "Normal"
    assert event.namespace == "default"
    assert event.name == "test-event"
    assert event.reason == "PodCreated"
    assert event.message == "Pod test-pod created"
    assert event.metadata == metadata
    assert event.involved_object == involved_object
    assert event.timestamp == "2025-11-30T12:00:00Z"
