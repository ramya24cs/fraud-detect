
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.services.database_health_service import (
    check_database_connection,
)

client = TestClient(app)


def test_health_endpoint_when_database_is_connected(monkeypatch):
    monkeypatch.setattr(
        "backend.app.main.check_database_connection",
        lambda: {"status": "ok", "database": "connected"},
    )

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["database"] == "connected"


def test_health_endpoint_when_database_is_unavailable(monkeypatch):
    monkeypatch.setattr(
        "backend.app.main.check_database_connection",
        lambda: {"status": "error", "database": "unavailable"},
    )

    response = client.get("/health")

    assert response.status_code == 503
