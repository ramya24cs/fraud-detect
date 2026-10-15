
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from backend.app.models.audit_log import AuditLog
from backend.app.models.prediction import Prediction
from backend.app.models.transaction import Transaction
from backend.app.services.prediction_persistence_service import (
    persist_prediction,
)


def sample_features():
    return {
        "Time": 10.0,
        **{f"V{i}": 0.1 for i in range(1, 29)},
        "Amount": 125.0,
    }


def sample_result():
    return {
        "fraud_probability": 0.12,
        "risk_level": "MEDIUM",
        "decision": "REVIEW",
        "expected_cost": 4.5,
        "model_version": "test-v1",
        "explanation": [],
        "probability_calibrated": False,
    }


def make_mock_db():
    db = MagicMock()

    def add_side_effect(obj):
        # Simulate IDs assigned when records are inserted.
        if isinstance(obj, (Transaction, Prediction, AuditLog)):
            if getattr(obj, "id", None) is None:
                obj.id = uuid4()

    db.add.side_effect = add_side_effect
    return db


def test_persist_prediction_creates_transaction_prediction_and_audit():
    db = make_mock_db()

    # A missing transaction means the service must create one.
    db.scalar.return_value = None

    user_id = uuid4()

    result = persist_prediction(
        db=db,
        external_id="test-txn-001",
        features=sample_features(),
        result=sample_result(),
        user_id=user_id,
    )

    assert result["fraud_probability"] == 0.12
    assert result["decision"] == "REVIEW"
    assert result["model_version"] == "test-v1"
    assert result["explanation"] == []
    assert result["probability_calibrated"] is False
    assert result["review_required"] is True
    assert result["risk_alert_status"] == "NOT_REQUIRED"
    assert result["prediction_timestamp"].tzinfo is not None
    assert result["risk_alert_triggered"] is False

    added_objects = [
        call.args[0]
        for call in db.add.call_args_list
    ]

    transaction = next(
        obj
        for obj in added_objects
        if isinstance(obj, Transaction)
    )
    prediction = next(
        obj
        for obj in added_objects
        if isinstance(obj, Prediction)
    )
    audit = next(
        obj
        for obj in added_objects
        if isinstance(obj, AuditLog)
    )

    assert transaction.external_id == "test-txn-001"
    assert transaction.amount == 125.0
    assert transaction.payload_json == sample_features()

    assert prediction.transaction_id == transaction.id
    assert prediction.probability == 0.12
    assert prediction.decision == "REVIEW"
    assert prediction.model_version == "test-v1"
    assert prediction.risk_alert_status == "NOT_REQUIRED"

    assert audit.action == "PREDICTION_CREATED"
    assert audit.user_id == user_id
    assert audit.entity_id == str(prediction.id)

    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_high_risk_alert_starts_pending_until_delivery_result_is_saved():
    db = make_mock_db()
    db.scalar.return_value = None
    result = sample_result()
    result["risk_level"] = "HIGH"

    response = persist_prediction(
        db=db,
        external_id="test-high-risk-001",
        features=sample_features(),
        result=result,
        user_id=uuid4(),
    )

    assert response["risk_alert_triggered"] is True
    assert response["risk_alert_status"] == "PENDING"

    added_objects = [
        call.args[0]
        for call in db.add.call_args_list
    ]
    prediction = next(
        obj
        for obj in added_objects
        if isinstance(obj, Prediction)
    )
    alert_audit = next(
        obj
        for obj in added_objects
        if isinstance(obj, AuditLog)
        and obj.action == "HIGH_RISK_ALERT_TRIGGERED"
    )

    assert prediction.risk_alert_status == "PENDING"
    assert alert_audit.metadata_json["risk_alert_status"] == "PENDING"


def test_persist_prediction_updates_existing_transaction():
    db = make_mock_db()

    existing_transaction = Transaction(
        external_id="test-txn-002",
        payload_json={},
        amount=10.0,
    )
    existing_transaction.id = uuid4()

    db.scalar.return_value = existing_transaction

    features = sample_features()
    features["Amount"] = 250.0

    result = persist_prediction(
        db=db,
        external_id="test-txn-002",
        features=features,
        result=sample_result(),
    )

    assert existing_transaction.amount == 250.0
    assert existing_transaction.payload_json == features
    assert result["transaction_id"] == existing_transaction.id
    assert result["prediction_timestamp"].tzinfo is not None

    added_objects = [
        call.args[0]
        for call in db.add.call_args_list
    ]

    # The existing transaction must not be inserted again.
    assert not any(
        isinstance(obj, Transaction)
        for obj in added_objects
    )

    # A new prediction and audit event should still be created.
    assert any(
        isinstance(obj, Prediction)
        for obj in added_objects
    )
    assert any(
        isinstance(obj, AuditLog)
        for obj in added_objects
    )

    db.commit.assert_called_once()
    db.rollback.assert_not_called()


def test_persist_prediction_rolls_back_when_flush_fails():
    db = make_mock_db()
    db.scalar.return_value = None
    db.flush.side_effect = RuntimeError(
        "Simulated persistence failure"
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated persistence failure",
    ):
        persist_prediction(
            db=db,
            external_id="test-txn-003",
            features=sample_features(),
            result=sample_result(),
        )

    db.rollback.assert_called_once()
    db.commit.assert_not_called()
