
import pytest
from abc import ABC
from sibyl.notifications.notifiable import Notifiable

def test_notifiable_is_abc():
    """
    Test that Notifiable is an abstract base class.
    """
    assert issubclass(Notifiable, ABC)

def test_notifiable_has_notify_abstract_method():
    """
    Test that Notifiable has an abstract method called notify.
    """
    assert "notify" in Notifiable.__abstractmethods__

class ConcreteNotifiable(Notifiable):
    def notify(self, event_data, logs=None):
        pass

def test_concrete_notifiable_can_be_instantiated():
    """
    Test that a concrete implementation of Notifiable can be instantiated.
    """
    try:
        concrete = ConcreteNotifiable()
        assert isinstance(concrete, Notifiable)
    except TypeError:
        pytest.fail("ConcreteNotifiable should be able to be instantiated")

