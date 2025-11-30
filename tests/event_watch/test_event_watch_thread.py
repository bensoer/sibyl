
import pytest

from unittest.mock import Mock, patch, MagicMock

from queue import Queue

from kubernetes import client, config

from sibyl.event_watch.event_watch_thread import EventWatchThread, EventWatch

from sibyl.models.events.k8_event import K8Event



@pytest.fixture

def mock_queue():

    return Mock(spec=Queue)



@pytest.fixture

@patch('sibyl.event_watch.event_watch_thread.config.load_incluster_config')

@patch('sibyl.event_watch.event_watch_thread.client.CoreV1Api')

def event_watch_thread(mock_core_v1_api, mock_load_config, mock_queue):

    return EventWatchThread(event_queue=mock_queue)



def test_init_success(event_watch_thread):

    assert event_watch_thread.core_v1_client is not None

    assert not event_watch_thread._stop_event.is_set()



@patch('sibyl.event_watch.event_watch_thread.config.load_incluster_config', side_effect=Exception("Test error"))

def test_init_fails(mock_load_config, mock_queue):

    with pytest.raises(Exception, match="Test error"):

        EventWatchThread(event_queue=mock_queue)



@patch('sibyl.event_watch.event_watch_thread.EventWatch')

def test_run_loop(mock_event_watch, event_watch_thread, mock_queue):

    mock_poll = mock_event_watch.return_value.poll_for_event

    

    mock_event = Mock(spec=client.CoreV1Event)

    mock_event.type = "Warning"

    mock_event.reason = "Some Reason"

    mock_event.message = "Some Message"

    mock_event.source.component = "comp"

    mock_event.source.host = "host"

    mock_event.metadata.name = "name"

    mock_event.metadata.namespace = "ns"

    mock_event.metadata.creation_timestamp = None

    mock_event.metadata.deletion_timestamp = None

    mock_event.involved_object.kind = "Pod"

    mock_event.involved_object.name = "pod-name"

    mock_event.involved_object.namespace = "pod-ns"

    mock_event.last_timestamp = None





    def side_effect(callback):

        callback(mock_event)

        event_watch_thread.stop()



    mock_poll.side_effect = side_effect



    event_watch_thread.run()



    mock_queue.put.assert_called_once()

    assert isinstance(mock_queue.put.call_args[0][0], K8Event)



@patch('sibyl.event_watch.event_watch_thread.EventWatch')

def test_run_ignores_normal_event(mock_event_watch, event_watch_thread, mock_queue):

    mock_poll = mock_event_watch.return_value.poll_for_event

    mock_event = Mock(spec=client.CoreV1Event)

    mock_event.type = "Normal"



    def side_effect(callback):

        callback(mock_event)

        event_watch_thread.stop()



    mock_poll.side_effect = side_effect



    event_watch_thread.run()



    mock_queue.put.assert_not_called()



@patch('time.sleep')

@patch('sibyl.event_watch.event_watch_thread.EventWatch')

def test_run_handles_api_exception(mock_event_watch, mock_sleep, event_watch_thread, mock_queue):

    mock_poll = mock_event_watch.return_value.poll_for_event

    

    side_effects = [

        client.ApiException(),

    ]



    def side_effect_func(callback):

        if side_effects:

            effect = side_effects.pop(0)

            if isinstance(effect, Exception):

                raise effect

        else:

            event_watch_thread.stop()

    

    mock_poll.side_effect = side_effect_func



    event_watch_thread.run()



    mock_sleep.assert_called_once_with(10)

    assert mock_poll.call_count == 2





def test_format_event(event_watch_thread):

    mock_event = MagicMock(spec=client.CoreV1Event)

    mock_event.kind = "Event"

    mock_event.type = "Warning"

    mock_event.reason = "Some Reason"

    mock_event.message = "Some Message"

    mock_event.action = "Action"

    mock_event.source.component = "comp"

    mock_event.source.host = "host"

    mock_event.metadata.name = "name"

    mock_event.metadata.namespace = "ns"

    mock_event.metadata.creation_timestamp = None

    mock_event.metadata.deletion_timestamp = None

    mock_event.involved_object.kind = "Pod"

    mock_event.involved_object.name = "pod-name"

    mock_event.involved_object.namespace = "pod-ns"

    mock_event.last_timestamp = None

    

    formatted_event = event_watch_thread._format_event(mock_event)

    assert isinstance(formatted_event, K8Event)

    assert formatted_event.reason == "Some Reason"





