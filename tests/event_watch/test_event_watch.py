
import pytest
from unittest.mock import Mock, patch
from kubernetes import client, watch
from sibyl.event_watch.event_watch import EventWatch

@pytest.fixture
def mock_core_v1_client():
    return Mock(spec=client.CoreV1Api)

@pytest.fixture
def event_watch(mock_core_v1_client):
    return EventWatch(core_v1_client=mock_core_v1_client, timeout_seconds=10)

def test_event_watch_init(event_watch, mock_core_v1_client):
    assert event_watch.core_v1_client == mock_core_v1_client
    assert event_watch.timeout_seconds == 10

@patch('kubernetes.watch.Watch')
def test_poll_for_event_calls_stream_and_callback(mock_watch, event_watch, mock_core_v1_client):
    mock_stream = [
        {'object': 'event1'},
        {'object': 'event2'}
    ]
    mock_watch_instance = mock_watch.return_value
    mock_watch_instance.stream.return_value = mock_stream
    
    callback = Mock()
    
    event_watch.poll_for_event(callback)
    
    mock_watch_instance.stream.assert_called_once_with(
        func=mock_core_v1_client.list_event_for_all_namespaces,
        timeout_seconds=10
    )
    assert callback.call_count == 2
    callback.assert_any_call('event1')
    callback.assert_any_call('event2')

@patch('kubernetes.watch.Watch')
def test_poll_for_event_api_exception(mock_watch, event_watch):
    mock_watch_instance = mock_watch.return_value
    mock_watch_instance.stream.side_effect = client.ApiException()
    
    callback = Mock()
    
    with pytest.raises(client.ApiException):
        event_watch.poll_for_event(callback)
    
    callback.assert_not_called()

@patch('kubernetes.watch.Watch')
def test_poll_for_event_generic_exception(mock_watch, event_watch):
    mock_watch_instance = mock_watch.return_value
    mock_watch_instance.stream.side_effect = Exception("test error")
    
    callback = Mock()
    
    with pytest.raises(Exception, match="test error"):
        event_watch.poll_for_event(callback)
    
    callback.assert_not_called()
