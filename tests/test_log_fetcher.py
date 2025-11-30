
import pytest
from unittest.mock import Mock, patch
from kubernetes import client, config
from sibyl.log_fetcher import LogFetcher
from sibyl.models.events.k8_event import K8Event
from sibyl.models.events.k8_event_involved_object import K8EventInvolvedObject

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
    logs = log_fetcher_fixture.fetch_current_pod_logs_from_event(mock_k8_event)
    assert logs == "current logs"
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.assert_called_with(
        name="test-pod", namespace="default", tail_lines=100, previous=False
    )

def test_fetch_current_pod_logs_404(log_fetcher_fixture, mock_k8_event):
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.side_effect = client.ApiException(status=404)
    logs = log_fetcher_fixture.fetch_current_pod_logs_from_event(mock_k8_event)
    assert logs is None

def test_fetch_previous_pod_logs_from_event_success(log_fetcher_fixture, mock_k8_event):
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.return_value = "previous logs"
    logs = log_fetcher_fixture.fetch_previous_pod_logs_from_event(mock_k8_event)
    assert logs == "previous logs"
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.assert_called_with(
        name="test-pod", namespace="default", tail_lines=100, previous=True
    )

def test_fetch_previous_pod_logs_404(log_fetcher_fixture, mock_k8_event):
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.side_effect = client.ApiException(status=404)
    logs = log_fetcher_fixture.fetch_previous_pod_logs_from_event(mock_k8_event)
    assert logs is None

@pytest.mark.parametrize("reason", LogFetcher.PREVIOUS_LOG_REASONS)
def test_fetch_pod_logs_from_event_previous(reason, log_fetcher_fixture, mock_k8_event):
    mock_k8_event.reason = reason
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.return_value = "previous logs"
    
    with patch.object(log_fetcher_fixture, 'fetch_previous_pod_logs_from_event', wraps=log_fetcher_fixture.fetch_previous_pod_logs_from_event) as wrapped_previous:
        logs = log_fetcher_fixture.fetch_pod_logs_from_event(mock_k8_event)
        wrapped_previous.assert_called_once()

def test_fetch_pod_logs_from_event_unhealthy_liveness(log_fetcher_fixture, mock_k8_event):
    mock_k8_event.reason = "Unhealthy"
    mock_k8_event.message = "Liveness probe failed"
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.return_value = "previous logs"
    
    with patch.object(log_fetcher_fixture, 'fetch_previous_pod_logs_from_event', wraps=log_fetcher_fixture.fetch_previous_pod_logs_from_event) as wrapped_previous:
        logs = log_fetcher_fixture.fetch_pod_logs_from_event(mock_k8_event)
        wrapped_previous.assert_called_once()

def test_fetch_pod_logs_from_event_fallback(log_fetcher_fixture, mock_k8_event):
    mock_k8_event.reason = "BackOff"
    
    # First call for previous logs returns None, second for current logs returns logs
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.side_effect = [
        None, 
        "current logs"
    ]
    
    logs = log_fetcher_fixture.fetch_pod_logs_from_event(mock_k8_event)
    assert logs == "current logs"
    assert log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.call_count == 2
    
def test_fetch_pod_logs_from_event_current(log_fetcher_fixture, mock_k8_event):
    mock_k8_event.reason = "Started"
    log_fetcher_fixture.core_v1_client.read_namespaced_pod_log.return_value = "current logs"
    
    with patch.object(log_fetcher_fixture, 'fetch_current_pod_logs_from_event', wraps=log_fetcher_fixture.fetch_current_pod_logs_from_event) as wrapped_current:
        logs = log_fetcher_fixture.fetch_pod_logs_from_event(mock_k8_event)
        wrapped_current.assert_called_once()
        assert logs == "current logs"
