
import os
import pytest
from pydantic import ValidationError
from sibyl.settings import Settings

def test_settings_default_values():
    """
    Test that the default values are loaded correctly.
    """
    settings = Settings(SLACK_BOT_TOKEN="dummy", SLACK_CHANNEL="dummy")
    assert settings.HEALTH_CHECK_PORT == 8080
    assert settings.LOG_LEVEL == "INFO"
    assert settings.CLUSTER_NAME is None
    assert settings.POD_LOG_TAIL_LINES == 100

def test_settings_from_env():
    """
    Test that values are loaded from environment variables.
    """
    os.environ["HEALTH_CHECK_PORT"] = "9090"
    os.environ["LOG_LEVEL"] = "DEBUG"
    os.environ["SLACK_BOT_TOKEN"] = "test_token"
    os.environ["SLACK_CHANNEL"] = "test_channel"
    os.environ["CLUSTER_NAME"] = "test_cluster"
    os.environ["POD_LOG_TAIL_LINES"] = "50"

    settings = Settings()

    assert settings.HEALTH_CHECK_PORT == 9090
    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.SLACK_BOT_TOKEN == "test_token"
    assert settings.SLACK_CHANNEL == "test_channel"
    assert settings.CLUSTER_NAME == "test_cluster"
    assert settings.POD_LOG_TAIL_LINES == 50

    # Clean up environment variables
    del os.environ["HEALTH_CHECK_PORT"]
    del os.environ["LOG_LEVEL"]
    del os.environ["SLACK_BOT_TOKEN"]
    del os.environ["SLACK_CHANNEL"]
    del os.environ["CLUSTER_NAME"]
    del os.environ["POD_LOG_TAIL_LINES"]

def test_settings_validation_error():
    """
    Test that a validation error is raised for invalid values.
    """
    with pytest.raises(ValidationError):
        Settings(HEALTH_CHECK_PORT=1000, SLACK_BOT_TOKEN="dummy", SLACK_CHANNEL="dummy")

    with pytest.raises(ValidationError):
        Settings(POD_LOG_TAIL_LINES=5, SLACK_BOT_TOKEN="dummy", SLACK_CHANNEL="dummy")
    
    with pytest.raises(ValidationError):
        Settings(LOG_LEVEL="INVALID", SLACK_BOT_TOKEN="dummy", SLACK_CHANNEL="dummy")
