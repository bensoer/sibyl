
import pytest
from unittest.mock import Mock, patch, MagicMock
from queue import Queue, Empty
import signal
import os

# Set dummy env vars to allow main to be imported without pydantic errors
os.environ["SLACK_BOT_TOKEN"] = "dummy"
os.environ["SLACK_CHANNEL"] = "dummy"

# Since main.py runs code on import, we need to patch things before importing
with patch('sibyl.main.HealthStatusThread'), \
     patch('sibyl.main.EventWatchThread'), \
     patch('sibyl.main.LogFetcher'), \
     patch('sibyl.main.SlackNotifier'), \
     patch('sibyl.main.signal.signal'), \
     patch('builtins.print'):
    from sibyl import main

@pytest.fixture
def mock_main_dependencies(mocker):
    mocker.patch('sibyl.main.settings', MagicMock())
    mocker.patch('sibyl.main.HealthStatusThread')
    mocker.patch('sibyl.main.EventWatchThread')
    mocker.patch('sibyl.main.LogFetcher')
    mocker.patch('sibyl.main.SlackNotifier')
    mocker.patch('sibyl.main.Queue')
    # Keep the loop running until we explicitly stop it
    mocker.patch('sibyl.main.CONTINUE_PROCESSING', True)


def test_main_loop_pod_event(mock_main_dependencies):
    mock_queue = main.Queue.return_value
    mock_event = MagicMock()
    mock_event.involved_object.kind = "Pod"
    mock_event.source.component = "kubelet"
    
    mock_queue.get.side_effect = [mock_event, SystemExit] # Stop after one event

    log_fetcher_instance = main.LogFetcher.return_value
    log_fetcher_instance.fetch_pod_logs_from_event.return_value = [("test-container", "some logs")]
    
    slack_notifier_instance = main.SlackNotifier.return_value

    with pytest.raises(SystemExit):
        main.main()

    log_fetcher_instance.fetch_pod_logs_from_event.assert_called_once_with(mock_event, tail_lines=main.settings.POD_LOG_TAIL_LINES)
    slack_notifier_instance.notify.assert_called_once_with(mock_event, logs=[("test-container", "some logs")])

def test_main_loop_non_pod_event(mock_main_dependencies):
    mock_queue = main.Queue.return_value
    mock_event = MagicMock()
    mock_event.involved_object.kind = "Deployment"
    
    mock_queue.get.side_effect = [mock_event, SystemExit]

    log_fetcher_instance = main.LogFetcher.return_value
    slack_notifier_instance = main.SlackNotifier.return_value
    
    with pytest.raises(SystemExit):
        main.main()

    log_fetcher_instance.fetch_pod_logs_from_event.assert_not_called()
    slack_notifier_instance.notify.assert_called_once_with(mock_event, logs=[])


def test_main_loop_empty_queue(mock_main_dependencies):
    mock_queue = main.Queue.return_value
    mock_queue.get.side_effect = [Empty, SystemExit]

    log_fetcher_instance = main.LogFetcher.return_value
    slack_notifier_instance = main.SlackNotifier.return_value

    with pytest.raises(SystemExit):
        main.main()
    
    log_fetcher_instance.fetch_pod_logs_from_event.assert_not_called()
    slack_notifier_instance.notify.assert_not_called()


def test_signal_handler():
    # To test the signal handler, we can't easily send signals.
    # Instead, we will call the handler function directly and check its effect.
    main.CONTINUE_PROCESSING = True
    main.signal_handler(signal.SIGINT, None)
    assert main.CONTINUE_PROCESSING is False

# Clean up environment variables
del os.environ["SLACK_BOT_TOKEN"]
del os.environ["SLACK_CHANNEL"]
