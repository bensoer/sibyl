
import pytest
from sibyl.models.events.k8_event_source import K8EventSource

def test_k8_event_source_creation():
    """
    Test the creation of a K8EventSource.
    """
    source = K8EventSource(
        component="kubelet",
        host="minikube"
    )
    assert source.component == "kubelet"
    assert source.host == "minikube"
