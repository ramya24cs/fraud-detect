
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from backend.app.models.audit_log import AuditLog
from backend.app.models.operator_feedback import OperatorFeedback
from backend.app.models.prediction import Prediction
from backend.app.models.transaction import Transaction
from backend.app.schemas.feedback import FeedbackRequest
from backend.app.services.feedback_service import submit_feedback


def make_feedback_db():
    db = MagicMock()
    transaction = Transaction(
        external_id="feedback-test-001",
        payload_json={"Amount": 125.0},
        amount=125.0,
    )
    transaction.id = uuid4()

    prediction = Prediction(
        transaction_id=transaction.id,
        model_version="test-v1",
        probability=0.12,
        risk_level="MEDIUM",
        decision="REVIEW",
        expected_cost=4.5,
    )
    prediction.id = uuid4()

    # First scalar lookup returns the transaction; second returns prediction.
    db.scalar.side_effect = [transaction, prediction]

    def assign_id(obj):
        if isinstance(obj, OperatorFeedback) and getattr(obj, "id", None) is None:
            obj.id = uuid4()

    db.add.side_effect = assign_id
    return db, transaction, prediction


def test_submit_feedback_persists_feedback_and_audit():
    db, transaction, prediction = make_feedback_db()
    user = type("UserStub", (), {"id": uuid4()})()

    request = FeedbackRequest(
        transaction_id=transaction.id,
        operator_decision="CONFIRMED_FRAUD",
        reason_code="MANUAL_REVIEW",
        comment="Confirmed after operator review",
    )

    result = submit_feedback(
        db=db,
        request=request,
        current_user=user,
    )

    added_objects = [
        call.args[0] for call in db.add.call_args_list
    ]

    feedback = next(
        obj for obj in added_objects
        if isinstance(obj, OperatorFeedback)
    )
    audit = next(
        obj for obj in added_objects
        if isinstance(obj, AuditLog)
    )

    assert result is feedback
    assert feedback.transaction_id == transaction.id
    assert feedback.user_id == user.id
    assert feedback.decision == "CONFIRMED_FRAUD"
    assert feedback.reason_code == "MANUAL_REVIEW"
    assert feedback.comment == "Confirmed after operator review"

    assert audit.action == "SUBMIT_FEEDBACK"
    assert audit.user_id == user.id
    assert audit.metadata_json["prediction_id"] == str(prediction.id)

    db.commit.assert_called_once()
    db.refresh.assert_called_once_with(feedback)
    db.rollback.assert_not_called()


def test_submit_feedback_rolls_back_when_flush_fails():
    db, transaction, _ = make_feedback_db()
    user = type("UserStub", (), {"id": uuid4()})()

    request = FeedbackRequest(
        transaction_id=transaction.id,
        operator_decision="CONFIRMED_GENUINE",
        reason_code="CUSTOMER_VERIFIED",
    )

    db.flush.side_effect = RuntimeError("Simulated feedback failure")

    with pytest.raises(
        RuntimeError,
        match="Simulated feedback failure",
    ):
        submit_feedback(
            db=db,
            request=request,
            current_user=user,
        )

    db.rollback.assert_called_once()
    db.commit.assert_not_called()
