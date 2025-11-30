
import pytest
from sibyl.models.events.k8_event_involved_object import K8EventInvolvedObject

def test_k8_event_involved_object_creation():
    """
    Test the creation of a K8EventInvolvedObject.
    """
    involved_object = K8EventInvolvedObject(
        kind="Pod",
        name="test-pod",
        namespace="default"
    )
    assert involved_object.kind == "Pod"
    assert involved_object.name == "test-pod"
    assert involved_object.namespace == "default"
