
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.api.deps import get_current_user, get_db
from backend.app.main import app


client = TestClient(app)


def setup_operator_auth(monkeypatch):
    operator = MagicMock()
    operator.id = uuid4()
    operator.email = "operator@example.com"
    operator.role = "OPERATOR"

    app.dependency_overrides[get_current_user] = lambda: operator
    app.dependency_overrides[get_db] = lambda: MagicMock()

    return operator


def teardown_function():
    app.dependency_overrides.clear()


def test_dashboard_summary_requires_authentication():
    response = client.get("/dashboard/summary")

    assert response.status_code == 401


def test_review_queue_requires_authentication():
    response = client.get("/review-queue")

    assert response.status_code == 401


def test_audit_logs_reject_operator(monkeypatch):
    setup_operator_auth(monkeypatch)

    response = client.get("/audit-logs")

    assert response.status_code == 403


def test_dashboard_summary_works_for_authenticated_operator(monkeypatch):
    setup_operator_auth(monkeypatch)

    from backend.app.api import dashboard

    monkeypatch.setattr(
        dashboard,
        "get_dashboard_summary",
        lambda db, user_id: {
            "total_transactions": 0,
            "total_predictions": 0,
            "review_count": 0,
            "blocked_count": 0,
            "approved_count": 0,
            "feedback_count": 0,
        },
    )

    response = client.get("/dashboard/summary")

    assert response.status_code == 200
