
import pytest
from sibyl.models.events.k8_event_metadata import K8EventMetadata

def test_k8_event_metadata_creation():
    """
    Test the creation of a K8EventMetadata.
    """
    metadata = K8EventMetadata(
        name="test-event",
        namespace="default",
        creation_timestamp="2025-11-30T12:00:00Z",
        deletion_timestamp=None
    )
    assert metadata.name == "test-event"
    assert metadata.namespace == "default"
    assert metadata.creation_timestamp == "2025-11-30T12:00:00Z"
    assert metadata.deletion_timestamp is None
