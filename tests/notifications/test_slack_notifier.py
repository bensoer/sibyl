
import pytest
from unittest.mock import Mock, patch
from slack_sdk.web import WebClient
import requests

from sibyl.notifications.slack_notifier import SlackNotifier
from sibyl.models.events.k8_event import K8Event
from sibyl.models.events.k8_event_involved_object import K8EventInvolvedObject
from sibyl.models.events.k8_event_metadata import K8EventMetadata
from sibyl.models.events.k8_event_source import K8EventSource

@pytest.fixture
def k8_event_data():
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
    return K8Event(
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

@pytest.fixture
def slack_notifier(mocker):
    mocker.patch("sibyl.notifications.slack_notifier.WebClient")
    return SlackNotifier(bot_token="test_token", channel="test_channel", cluster_name="test_cluster")

def test_slack_notifier_init(slack_notifier):
    from sibyl.notifications.slack_notifier import WebClient
    WebClient.assert_called_once_with(token="test_token")
    assert slack_notifier.channel == "test_channel"
    assert slack_notifier.cluster_name == "test_cluster"

def test_notify_without_logs(slack_notifier, k8_event_data):
    slack_notifier.client.chat_postMessage.return_value = {"ok": True, "ts": "12345"}
    slack_notifier.notify(k8_event_data)
    slack_notifier.client.chat_postMessage.assert_called_once()
    slack_notifier.client.files_getUploadURLExternal.assert_not_called()

def test_notify_with_logs(slack_notifier, k8_event_data, mocker):
    slack_notifier.client.chat_postMessage.return_value = {"ok": True, "ts": "12345", "channel": "C123"}
    slack_notifier.client.files_getUploadURLExternal.return_value = {"ok": True, "upload_url": "http://upload.url", "file_id": "F123"}
    mocker.patch("requests.post")
    requests.post.return_value.raise_for_status.return_value = None
    slack_notifier.client.files_completeUploadExternal.return_value = {"ok": True}

    logs_data = [("container1", "logs for container1"), ("container2", "logs for container2")]
    slack_notifier.notify(k8_event_data, logs=logs_data)

    # Assert initial message
    slack_notifier.client.chat_postMessage.assert_any_call(
        channel="test_channel",
        text=mocker.ANY,
        blocks=mocker.ANY
    )
    # Assert log uploads for each container
    assert slack_notifier.client.files_getUploadURLExternal.call_count == 2
    assert requests.post.call_count == 2
    assert slack_notifier.client.files_completeUploadExternal.call_count == 2

    # Assert specific calls for container1
    slack_notifier.client.files_getUploadURLExternal.assert_any_call(
        filename=f"logs_pod_default_test_pod_container1.txt",
        length=len("logs for container1"),
        snippet_type="text"
    )
    requests.post.assert_any_call(
        "http://upload.url",
        headers={'Content-Type': 'application/octet-stream'},
        data="logs for container1".encode('utf-8')
    )
    slack_notifier.client.files_completeUploadExternal.assert_any_call(
        upload_url=mocker.ANY,
        channels=[mocker.ANY],
        thread_ts="12345",
        initial_comment=mocker.ANY,
        files=mocker.ANY
    )
    slack_notifier.client.files_getUploadURLExternal.assert_any_call(
        filename=f"logs_pod_default_test_pod_container2.txt",
        length=len("logs for container2"),
        snippet_type="text"
    )
    requests.post.assert_any_call(
        "http://upload.url",
        headers={'Content-Type': 'application/octet-stream'},
        data="logs for container2".encode('utf-8')
    )
    slack_notifier.client.files_completeUploadExternal.assert_any_call(
        upload_url=mocker.ANY,
        channels=[mocker.ANY],
        thread_ts="12345",
        initial_comment=mocker.ANY,
        files=mocker.ANY
    )
    # The threaded messages are part of files_completeUploadExternal, so no separate chat_postMessage call to assert
    # slack_notifier.client.chat_postMessage.assert_any_call(
    #     channel="C123",
    #     thread_ts="12345",
    #     text=mocker.ANY
    # )

def test_notify_post_message_fails(slack_notifier, k8_event_data, caplog):
    slack_notifier.client.chat_postMessage.return_value = {"ok": False, "error": "test_error"}
    slack_notifier.notify(k8_event_data)
    assert "Failed to post slack notification" in caplog.text

def test_notify_get_upload_url_fails(slack_notifier, k8_event_data, caplog):
    slack_notifier.client.chat_postMessage.return_value = {"ok": True, "ts": "12345", "channel": "C123"}
    slack_notifier.client.files_getUploadURLExternal.return_value = {"ok": False, "error": "test_error"}
    
    logs_data = [("container1", "some logs")]
    slack_notifier.notify(k8_event_data, logs=logs_data)
    
    assert "Slack files.getUploadURLExternal Failed for event default/test-pod -> container1 to Slack" in caplog.text

@patch("requests.post")
def test_notify_upload_fails(mock_post, slack_notifier, k8_event_data, caplog):
    slack_notifier.client.chat_postMessage.return_value = {"ok": True, "ts": "12345", "channel": "C123"}
    slack_notifier.client.files_getUploadURLExternal.return_value = {"ok": True, "upload_url": "http://upload.url", "file_id": "F123"}
    mock_post.side_effect = requests.exceptions.RequestException("test error")
    
    logs_data = [("container1", "some logs")]
    slack_notifier.notify(k8_event_data, logs=logs_data)
    
    assert "Failed to upload logs for event default/test-pod -> container1 to Slack" in caplog.text


def test_notify_complete_upload_fails(slack_notifier, k8_event_data, caplog, mocker):
    slack_notifier.client.chat_postMessage.return_value = {"ok": True, "ts": "12345", "channel": "C123"}
    slack_notifier.client.files_getUploadURLExternal.return_value = {"ok": True, "upload_url": "http://upload.url", "file_id": "F123"}
    mocker.patch("requests.post")
    requests.post.return_value.raise_for_status.return_value = None
    slack_notifier.client.files_completeUploadExternal.return_value = {"ok": False, "error": "test_error"}
    
    logs_data = [("container1", "some logs")]
    slack_notifier.notify(k8_event_data, logs=logs_data)
    
    assert "Slack files.completeUploadExternal Failed for event default/test-pod -> container1" in caplog.text

