
import pytest
from unittest.mock import Mock, patch, call
from kubernetes import client, config
from sibyl.log_fetcher import LogFetcher
from sibyl.models.events.k8_event import K8Event
from sibyl.models.events.k8_event_involved_object import K8EventInvolvedObject

class MockV1Container:
    def __init__(self, name):
        self.name = name

class MockV1PodSpec:
    def __init__(self, containers):
        self.containers = containers

class MockV1Pod:
    def __init__(self, containers):
        self.spec = MockV1PodSpec(containers)


@pytest.fixture
def mock_k8_event():
    involved_object = K8EventInvolvedObject(namespace="default", name="test-pod", kind="Pod")
    return K8Event(
        namespace="default",
        involved_object=involved_object,
        reason="SomeReason",
        message="",
        # Fill in other required fields for K8Event if necessary
        kind="", source=Mock(), action="", type="", name="", metadata=Mock(), timestamp=""
    )

@pytest.fixture
def log_fetcher_fixture():
    with patch('sibyl.log_fetcher.config.load_incluster_config'), \
         patch('sibyl.log_fetcher.client.CoreV1Api') as mock_api:
        fetcher = LogFetcher()
        fetcher.core_v1_client = mock_api.return_value
        yield fetcher


def test_fetch_current_pod_logs_from_event_success(log_fetcher_fixture, mock_k8_event):
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.return_value = "current logs"
    logs = log_fetcher_fixture.fetch_current_pod_logs_from_event(mock_k8_event, "test-container")
    assert logs == "current logs"
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.assert_called_with(
        name="test-pod", namespace="default", container="test-container", tail_lines=100, previous=False
    )

def test_fetch_current_pod_logs_404(log_fetcher_fixture, mock_k8_event):
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.side_effect = client.ApiException(status=404)
    logs = log_fetcher_fixture.fetch_current_pod_logs_from_event(mock_k8_event, "test-container")
    assert logs is None

def test_fetch_previous_pod_logs_from_event_success(log_fetcher_fixture, mock_k8_event):
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.return_value = "previous logs"
    logs = log_fetcher_fixture.fetch_previous_pod_logs_from_event(mock_k8_event, "test-container")
    assert logs == "previous logs"
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.assert_called_with(
        name="test-pod", namespace="default", container="test-container", tail_lines=100, previous=True
    )

def test_fetch_previous_pod_logs_404(log_fetcher_fixture, mock_k8_event):
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.side_effect = client.ApiException(status=404)
    logs = log_fetcher_fixture.fetch_previous_pod_logs_from_event(mock_k8_event, "test-container")
    assert logs is None

@pytest.mark.parametrize("reason", LogFetcher.PREVIOUS_LOG_REASONS)
def test_fetch_pod_logs_from_event_previous(reason, log_fetcher_fixture, mock_k8_event):
    mock_k8_event.reason = reason
    
    mock_pod = MockV1Pod(containers=[MockV1Container(name="test-container")])
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_status.return_value = mock_pod
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.return_value = "previous logs"
    
    logs = log_fetcher_fixture.fetch_pod_logs_from_event(mock_k8_event)
    
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_status.assert_called_once_with(
        name="test-pod", namespace="default"
    )
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.assert_called_once_with(
        name="test-pod", namespace="default", container="test-container", tail_lines=100, previous=True
    )
    assert logs == [("test-container", "previous logs")]


def test_fetch_pod_logs_from_event_unhealthy_liveness(log_fetcher_fixture, mock_k8_event):
    mock_k8_event.reason = "Unhealthy"
    mock_k8_event.message = "Liveness probe failed"
    
    mock_pod = MockV1Pod(containers=[MockV1Container(name="test-container")])
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_status.return_value = mock_pod
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.return_value = "previous logs"
    
    logs = log_fetcher_fixture.fetch_pod_logs_from_event(mock_k8_event)
    
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_status.assert_called_once_with(
        name="test-pod", namespace="default"
    )
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.assert_called_once_with(
        name="test-pod", namespace="default", container="test-container", tail_lines=100, previous=True
    )
    assert logs == [("test-container", "previous logs")]

def test_fetch_pod_logs_from_event_fallback(log_fetcher_fixture, mock_k8_event):
    mock_k8_event.reason = "BackOff"
    
    mock_pod = MockV1Pod(containers=[MockV1Container(name="test-container")])
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_status.return_value = mock_pod
    
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.side_effect = [
        client.ApiException(status=404), # for previous logs
        "current logs" # for current logs
    ]
    
    logs = log_fetcher_fixture.fetch_pod_logs_from_event(mock_k8_event)
    assert logs == [("test-container", "current logs")]
    assert log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.call_count == 2
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.assert_has_calls([
        call(name='test-pod', namespace='default', container='test-container', tail_lines=100, previous=True),
        call(name='test-pod', namespace='default', container='test-container', tail_lines=100, previous=False)
    ])
    
def test_fetch_pod_logs_from_event_current(log_fetcher_fixture, mock_k8_event):
    mock_k8_event.reason = "Started"
    
    mock_pod = MockV1Pod(containers=[MockV1Container(name="test-container")])
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_status.return_value = mock_pod
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.return_value = "current logs"
    
    logs = log_fetcher_fixture.fetch_pod_logs_from_event(mock_k8_event)
    
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_status.assert_called_once_with(
        name="test-pod", namespace="default"
    )
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.assert_called_once_with(
        name="test-pod", namespace="default", container="test-container", tail_lines=100, previous=False
    )
    assert logs == [("test-container", "current logs")]


def test_fetch_pod_logs_from_event_multiple_containers(log_fetcher_fixture, mock_k8_event):
    mock_k8_event.reason = "Started" # Fetch current logs
    
    container1_name = "container-alpha"
    container2_name = "container-beta"
    
    mock_pod = MockV1Pod(containers=[MockV1Container(name=container1_name), MockV1Container(name=container2_name)])
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_status.return_value = mock_pod
    
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.side_effect = [
        f"logs for {container1_name}",
        f"logs for {container2_name}"
    ]
    
    logs = log_fetcher_fixture.fetch_pod_logs_from_event(mock_k8_event)
    
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_status.assert_called_once_with(
        name="test-pod", namespace="default"
    )
    
    assert log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.call_count == 2
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.assert_has_calls([
        call(name='test-pod', namespace='default', container=container1_name, tail_lines=100, previous=False),
        call(name='test-pod', namespace='default', container=container2_name, tail_lines=100, previous=False)
    ])
    
    assert logs == [
        (container1_name, f"logs for {container1_name}"),
        (container2_name, f"logs for {container2_name}")
    ]
