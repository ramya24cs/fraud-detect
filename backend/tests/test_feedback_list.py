
"""Database round-trip test for operator feedback persistence."""

from uuid import uuid4

import pytest
from sqlalchemy import text

from backend.app.core.security import hash_password
from backend.app.models.audit_log import AuditLog
from backend.app.models.operator_feedback import OperatorFeedback
from backend.app.models.prediction import Prediction
from backend.app.models.transaction import Transaction
from backend.app.models.user import User
from backend.app.schemas.feedback import FeedbackRequest
from backend.app.services.feedback_service import (
    list_feedback,
    submit_feedback,
)


def _db_available() -> bool:
    try:
        from backend.app.db.session import SessionLocal

        db = SessionLocal()
        try:
            db.execute(text("SELECT 1"))
            return True
        finally:
            db.close()
    except Exception:
        return False


@pytest.mark.skipif(
    not _db_available(),
    reason="Configured database is unavailable",
)
def test_feedback_persists_and_is_retrievable_from_database():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    email = f"qa-feedback-{uuid4().hex[:8]}@example.com"
    user_id = None
    transaction_id = None

    try:
        user = User(
            email=email,
            password_hash=hash_password("Test-Password-123!"),
            role="OPERATOR",
        )
        db.add(user)
        db.flush()
        user_id = user.id

        transaction = Transaction(
            user_id=user.id,
            external_id=f"qa-feedback-{uuid4().hex[:12]}",
            payload_json={"Amount": 42.0},
            amount=42.0,
        )
        db.add(transaction)
        db.flush()
        transaction_id = transaction.id

        db.add(
            Prediction(
                transaction_id=transaction.id,
                model_version="xgb-cost-v1",
                probability=0.35,
                risk_level="MEDIUM",
                decision="REVIEW",
                expected_cost=7.5,
            )
        )
        db.commit()

        feedback = submit_feedback(
            db=db,
            request=FeedbackRequest(
                transaction_id=transaction.id,
                operator_decision="CONFIRMED_GENUINE",
                reason_code="QA_DB_ROUNDTRIP",
                comment="synthetic persistence check",
            ),
            current_user=user,
        )

        feedback_id = feedback.id

        rows, total = list_feedback(
    db=db,
    user_id=user.id,
    limit=50,
    offset=0,
    transaction_id=transaction.id,
)

        assert total == 1
        assert len(rows) == 1
        assert rows[0].id == feedback_id
        assert rows[0].user_id == user.id
        assert rows[0].reason_code == "QA_DB_ROUNDTRIP"

    finally:
        try:
            if transaction_id is not None:
                db.query(OperatorFeedback).filter(
                    OperatorFeedback.transaction_id == transaction_id
                ).delete(synchronize_session=False)

                db.query(Prediction).filter(
                    Prediction.transaction_id == transaction_id
                ).delete(synchronize_session=False)

                db.query(Transaction).filter(
                    Transaction.id == transaction_id
                ).delete(synchronize_session=False)

            if user_id is not None:
                db.query(AuditLog).filter(
                    AuditLog.user_id == user_id
                ).delete(synchronize_session=False)

                db.query(User).filter(
                    User.id == user_id
                ).delete(synchronize_session=False)

            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()
