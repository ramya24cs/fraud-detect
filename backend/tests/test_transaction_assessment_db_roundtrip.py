"""End-to-end persistence coverage for assessment, dashboard, and review queue."""

from unittest.mock import patch
from uuid import uuid4

import pytest
from sqlalchemy import text

from backend.app.core.security import hash_password
from backend.app.models.audit_log import AuditLog
from backend.app.models.transaction import Transaction
from backend.app.models.transaction_assessment import TransactionAssessment
from backend.app.models.user import User
from backend.app.schemas.transaction_assessment import (
    ReviewDecisionRequest,
    TransactionAssessmentRequest,
    TransactionAssessmentResponse,
)
from backend.app.services.transaction_assessment_service import (
    analyze_and_persist,
    list_assessment_history,
    list_pending_reviews,
    record_review_decision,
)


def _db_available() -> bool:
    try:
        from backend.app.db.session import SessionLocal

        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


@pytest.mark.skipif(
    not _db_available(),
    reason="Configured database is unavailable",
)
def test_medium_assessment_flows_to_dashboard_and_clears_after_review():
    from backend.app.db.session import SessionLocal

    db = SessionLocal()
    user = User(
        email=f"qa-assessment-{uuid4().hex}@example.test",
        password_hash=hash_password("Test-Password-123!"),
        role="OPERATOR",
    )
    db.add(user)
    db.flush()
    user_id = user.id

    try:
        request = TransactionAssessmentRequest(
            amount=2_500,
            currency="INR",
            occurred_at="2026-10-14T17:30:00+05:30",
            transaction_type="UPI",
            merchant="Test recipient",
            channel="Mobile app",
            reference="QA-REVIEW-001",
            location="Pune",
            remarks="Disposable database round-trip test",
        )

        with patch(
            "backend.app.services.transaction_assessment_service."
            "send_review_notification",
            return_value={
                "status": "SENT",
                "message": "Email sent.",
                "subject": "Transaction review requested: MEDIUM",
                "content": "Test email body.",
            },
        ):
            result = analyze_and_persist(db, request, user)

        response = TransactionAssessmentResponse(**result)
        assert response.risk_level == "MEDIUM"
        assert response.review_required is True
        assert response.review_notification_recipient == user.email
        assert response.review_notification_content == "Test email body."

        dashboard = list_assessment_history(db, user)
        assert dashboard.total >= 1
        dashboard_item = next(
            item
            for item in dashboard.items
            if item.assessment_id == response.assessment_id
        )
        assert dashboard_item.review_decision is None
        assert dashboard_item.review_required is True

        pending = list_pending_reviews(db, user)
        assert pending.total >= 1
        assert any(
            item.assessment_id == response.assessment_id
            for item in pending.items
        )

        decision = record_review_decision(
            db,
            assessment_id=response.assessment_id,
            request=ReviewDecisionRequest(
                decision="AGREE",
                comment="Verified by round-trip test.",
            ),
            current_user=user,
        )
        assert decision.decision == "AGREE"

        refreshed_dashboard = list_assessment_history(db, user)
        reviewed_item = next(
            item
            for item in refreshed_dashboard.items
            if item.assessment_id == response.assessment_id
        )
        assert reviewed_item.review_decision == "AGREE"
        assert reviewed_item.reviewed_at is not None

        refreshed_pending = list_pending_reviews(db, user)
        assert all(
            item.assessment_id != response.assessment_id
            for item in refreshed_pending.items
        )
    finally:
        transaction_ids = [
            row[0]
            for row in db.query(Transaction.id)
            .filter(Transaction.user_id == user_id)
            .all()
        ]
        if transaction_ids:
            db.query(AuditLog).filter(
                AuditLog.user_id == user_id
            ).delete(synchronize_session=False)
            db.query(TransactionAssessment).filter(
                TransactionAssessment.transaction_id.in_(transaction_ids)
            ).delete(synchronize_session=False)
            db.query(Transaction).filter(
                Transaction.id.in_(transaction_ids)
            ).delete(synchronize_session=False)
        db.query(AuditLog).filter(
            AuditLog.user_id == user_id
        ).delete(synchronize_session=False)
        db.query(User).filter(User.id == user_id).delete(synchronize_session=False)
        db.commit()
        db.close()
