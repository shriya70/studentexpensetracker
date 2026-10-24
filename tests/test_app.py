import json

from app import app


def test_home_page_is_available():
    response = app.test_client().get("/")
    assert response.status_code == 200
    assert b"CloudOps Mini Lab" in response.data


def test_health_endpoint():
    response = app.test_client().get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_readiness_endpoint():
    response = app.test_client().get("/ready")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ready"


def test_status_contains_runtime_details():
    data = app.test_client().get("/api/status").get_json()
    assert data["service"] == "cloudops-mini-lab"
    assert "hostname" in data
    assert data["uptime_seconds"] >= 0
    assert data["checks"]["metrics"] == "enabled"


def test_metrics_endpoint_exposes_prometheus_metrics():
    client = app.test_client()
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"cloudops_http_requests_total" in response.data
