
import pytest
from sibyl.health_check.health_status_thread import HealthStatusThread

@pytest.fixture
def health_thread():
    return HealthStatusThread()

def test_health_status_thread_init(health_thread):
    from sibyl.health_check.health_status import HealthStatus
    assert isinstance(health_thread.get_health_status(), HealthStatus)

def test_create_health_app(health_thread):
    app = health_thread.create_health_app()
    assert app is not None
    # Check if routes are registered
    rules = [rule.rule for rule in app.url_map.iter_rules()]
    assert '/health' in rules
    assert '/ready' in rules

def test_health_endpoint_healthy(health_thread):
    app = health_thread.create_health_app()
    client = app.test_client()
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json == {"status": "healthy"}

def test_health_endpoint_unhealthy(health_thread):
    app = health_thread.create_health_app()
    client = app.test_client()
    health_thread.get_health_status().set_healthy(False, "Test error")
    response = client.get('/health')
    assert response.status_code == 503
    assert response.json == {"status": "unhealthy", "error": "Test error"}

def test_ready_endpoint_ready(health_thread):
    app = health_thread.create_health_app()
    client = app.test_client()
    response = client.get('/ready')
    assert response.status_code == 200
    assert response.json == {"status": "ready"}

def test_ready_endpoint_not_ready(health_thread):
    app = health_thread.create_health_app()
    client = app.test_client()
    health_thread.get_health_status().set_ready(False)
    response = client.get('/ready')
    assert response.status_code == 503
    assert response.json == {"status": "not_ready"}
