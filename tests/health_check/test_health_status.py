
import pytest
from sibyl.health_check.health_status import HealthStatus

def test_health_status_initial_state():
    """
    Test the initial state of the HealthStatus.
    """
    health_status = HealthStatus()
    assert health_status.is_healthy() is True
    assert health_status.is_ready() is True
    assert health_status.get_error_message() is None

def test_set_and_is_healthy():
    """
    Test the set_healthy and is_healthy methods.
    """
    health_status = HealthStatus()
    health_status.set_healthy(False, "Test error")
    assert health_status.is_healthy() is False
    assert health_status.get_error_message() == "Test error"
    health_status.set_healthy(True)
    assert health_status.is_healthy() is True
    assert health_status.get_error_message() is None

def test_set_and_is_ready():
    """
    Test the set_ready and is_ready methods.
    """
    health_status = HealthStatus()
    health_status.set_ready(False)
    assert health_status.is_ready() is False
    health_status.set_ready(True)
    assert health_status.is_ready() is True
