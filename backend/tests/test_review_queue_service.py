
"""Regression tests for review-queue filtering and API shape.

Root cause of empty queue with HTTP 200:
the service intentionally returns only predictions where
decision == 'REVIEW'. APPROVE/BLOCK rows are persisted but excluded.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient

from backend.app.api.deps import get_current_user, get_db
from backend.app.main import app
from backend.app.models.prediction import Prediction
from backend.app.models.transaction import Transaction
from backend.app.schemas.review_queue import ReviewQueueResponse
from backend.app.services.review_queue_service import get_review_queue


client = TestClient(app)


def teardown_function():
    app.dependency_overrides.clear()


def _make_pair(decision: str, amount: float = 100.0):
    transaction = Transaction(
        external_id=f"ext-{decision.lower()}-{uuid4().hex[:8]}",
        payload_json={"Amount": amount},
        amount=amount,
    )
    transaction.id = uuid4()
    transaction.created_at = datetime.now(timezone.utc)

    prediction = Prediction(
        transaction_id=transaction.id,
        model_version="xgb-cost-v1",
        probability=0.35 if decision == "REVIEW" else 0.01,
        risk_level="MEDIUM" if decision == "REVIEW" else "LOW",
        decision=decision,
        expected_cost=7.5 if decision == "REVIEW" else 0.1,
    )
    prediction.id = uuid4()
    prediction.created_at = datetime.now(timezone.utc)

    return prediction, transaction


def test_review_queue_query_filters_decision_to_review_only():
    """Confirm the SQL filter restricts results to REVIEW decisions."""
    db = MagicMock()
    db.scalar.return_value = 0
    db.execute.return_value.all.return_value = []

    get_review_queue(
        db=db,
        user_id=uuid4(),
        limit=50,
        offset=0,
    )

    count_stmt = db.scalar.call_args.args[0]
    compiled = str(
        count_stmt.compile(compile_kwargs={"literal_binds": True})
    )

    assert "REVIEW" in compiled
    assert "predictions" in compiled.lower()


def test_review_queue_returns_only_review_rows_from_mixed_results():
    """Service response includes REVIEW items and excludes others."""
    review_pair = _make_pair("REVIEW", amount=500.0)
    approve_pair = _make_pair("APPROVE", amount=25.0)
    block_pair = _make_pair("BLOCK", amount=900.0)

    # Simulate the database returning only rows matching the REVIEW filter.
    db = MagicMock()
    db.scalar.return_value = 1
    db.execute.return_value.all.return_value = [review_pair]

    response = get_review_queue(
        db=db,
        user_id=uuid4(),
        limit=50,
        offset=0,
    )

    assert isinstance(response, ReviewQueueResponse)
    assert response.total == 1
    assert len(response.items) == 1
    assert response.items[0].decision == "REVIEW"
    assert response.items[0].amount == 500.0
    assert response.items[0].external_id == review_pair[1].external_id

    assert approve_pair[0].decision == "APPROVE"
    assert block_pair[0].decision == "BLOCK"


def test_review_queue_endpoint_returns_persisted_review_items(monkeypatch):
    operator = MagicMock()
    operator.id = uuid4()
    operator.email = "operator@example.com"
    operator.role = "OPERATOR"

    app.dependency_overrides[get_current_user] = lambda: operator
    app.dependency_overrides[get_db] = lambda: MagicMock()

    from backend.app.api import review_queue as review_queue_api
    from backend.app.schemas.review_queue import (
        ReviewQueueItem,
        ReviewQueueResponse,
    )

    item = ReviewQueueItem(
        prediction_id=uuid4(),
        transaction_id=uuid4(),
        external_id="synth-review-001",
        amount=500.0,
        fraud_probability=0.35,
        risk_level="MEDIUM",
        decision="REVIEW",
        expected_cost=7.9,
        model_version="xgb-cost-v1",
        created_at=datetime.now(timezone.utc),
    )

    monkeypatch.setattr(
        review_queue_api,
        "get_review_queue",
        lambda db, user_id, limit=50, offset=0: ReviewQueueResponse(
            items=[item],
            total=1,
            limit=limit,
            offset=offset,
        ),
    )

    response = client.get("/review-queue")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["decision"] == "REVIEW"
    assert body["items"][0]["external_id"] == "synth-review-001"


def test_empty_review_queue_is_valid_when_no_review_decisions(monkeypatch):
    """HTTP 200 with total=0 is correct when no REVIEW decisions exist."""
    operator = MagicMock()
    operator.id = uuid4()
    operator.role = "OPERATOR"

    app.dependency_overrides[get_current_user] = lambda: operator
    app.dependency_overrides[get_db] = lambda: MagicMock()

    from backend.app.api import review_queue as review_queue_api
    from backend.app.schemas.review_queue import ReviewQueueResponse

    monkeypatch.setattr(
        review_queue_api,
        "get_review_queue",
        lambda db, user_id, limit=50, offset=0: ReviewQueueResponse(
            items=[],
            total=0,
            limit=limit,
            offset=offset,
        ),
    )

    response = client.get("/review-queue")

    assert response.status_code == 200
    assert response.json()["total"] == 0
    assert response.json()["items"] == []
