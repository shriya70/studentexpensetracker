
import app as app_module
import pytest
from datetime import date


@pytest.fixture
def client(tmp_path, monkeypatch):
    # Give every test its own temporary database.
    db_path = tmp_path / "expenses.db"
    monkeypatch.setattr(app_module, "DB_PATH", str(db_path))
    app_module.init_db()
    return app_module.app.test_client()


def test_home_page_is_available(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Student Expense Tracker" in response.data


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_readiness_endpoint(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ready"


def test_status_contains_runtime_details(client):
    data = client.get("/api/status").get_json()
    assert data["service"] == "student-expense-tracker"
    assert "hostname" in data
    assert data["uptime_seconds"] >= 0
    assert data["checks"]["metrics"] == "enabled"


def test_metrics_endpoint_exposes_prometheus_metrics(client):
    client.get("/health")
    response = client.get("/metrics")
    assert response.status_code == 200
    assert b"cloudops_http_requests_total" in response.data


def test_add_and_list_expense(client):
    response = client.post(
        "/api/expenses",
        json={
            "amount": 150,
            "category": "Food",
            "note": "Lunch at college",
            "spent_on": date.today().isoformat(),
        },
    )

    assert response.status_code == 201

    expense_id = response.get_json()["id"]
    listing = client.get("/api/expenses")

    assert listing.status_code == 200
    expense = next(
        item for item in listing.get_json()
        if item["id"] == expense_id
    )
    assert expense["amount"] == 150
    assert expense["category"] == "Food"
    assert expense["note"] == "Lunch at college"


def test_invalid_expense_is_rejected(client):
    response = client.post(
        "/api/expenses",
        json={
            "amount": -10,
            "category": "Food",
            "spent_on": date.today().isoformat(),
        },
    )

    assert response.status_code == 400


def test_delete_expense(client):
    created = client.post(
        "/api/expenses",
        json={
            "amount": 80,
            "category": "Transport",
            "note": "Bus fare",
            "spent_on": date.today().isoformat(),
        },
    )
    assert created.status_code == 201

    expense_id = created.get_json()["id"]
    deleted = client.delete(f"/api/expenses/{expense_id}")

    assert deleted.status_code == 200

    remaining = client.get("/api/expenses").get_json()
    assert all(item["id"] != expense_id for item in remaining)
