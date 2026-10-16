from datetime import datetime, timezone
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import ValidationError

from backend.app.models.transaction import Transaction
from backend.app.models.transaction_assessment import TransactionAssessment
from backend.app.schemas.transaction_assessment import (
    ReviewDecisionRequest,
    TransactionAssessmentBatchRequest,
    TransactionAssessmentRequest,
)
from backend.app.services.transaction_assessment_service import (
    analyze_batch_and_persist,
    analyze_and_persist,
    assess_transaction_amount,
    list_assessment_history,
    list_pending_reviews,
)


def _transaction(**overrides):
    current = {
        "amount": 100.0,
        "currency": "INR",
        "merchant": "Known shop",
        "transaction_type": "UPI",
        "channel": "Mobile app",
        "location": "Pune",
    }
    current.update(overrides)
    return current


@pytest.mark.parametrize(
    ("amount", "expected_risk", "review_required", "alert_created"),
    [
        (1.0, "LOW", False, False),
        (2_000.0, "LOW", False, False),
        (2_000.01, "MEDIUM", True, False),
        (99_998.99, "MEDIUM", True, False),
        (99_999.0, "HIGH", True, True),
        (100_000.0, "HIGH", True, True),
    ],
)
def test_assessment_uses_configured_amount_bands_only(
    amount,
    expected_risk,
    review_required,
    alert_created,
):
    result = assess_transaction_amount(
        _transaction(
            amount=amount,
            merchant="Different merchant",
            transaction_type="Card",
            channel="ATM",
            location="Different city",
        )
    )

    assert result["risk_level"] == expected_risk
    assert result["review_required"] is review_required
    assert result["alert_created"] is alert_created
    assert result["history_count"] == 0


def test_same_numeric_cutoffs_apply_to_every_selected_currency():
    for currency in ("INR", "USD", "EUR", "GBP"):
        result = assess_transaction_amount(
            _transaction(amount=2_500, currency=currency)
        )
        assert result["risk_level"] == "MEDIUM"
        assert result["review_required"] is True
        assert "2,000" not in result["reasons"][0]
        assert "99,999" not in result["reasons"][0]


@pytest.mark.parametrize(
    ("amount", "user_email", "expected_risk", "expected_email_status"),
    [
        (1_000, "signed-in@example.test", "LOW", "NOT_REQUIRED"),
        (2_500, "signed-in@example.test", "MEDIUM", "SENT"),
        (100_000, "signed-in@example.test", "HIGH", "SENT"),
        (2_500, "another-user@example.test", "MEDIUM", "SENT"),
    ],
)
def test_medium_and_high_amount_assessments_send_email_for_human_review(
    amount,
    user_email,
    expected_risk,
    expected_email_status,
):
    db = MagicMock()
    user = MagicMock(id=uuid4(), email=user_email)
    db.add.side_effect = lambda obj: (
        setattr(obj, "id", uuid4())
        if isinstance(obj, (Transaction, TransactionAssessment))
        else None
    )
    db.refresh.side_effect = lambda assessment: setattr(
        assessment,
        "created_at",
        datetime.now(timezone.utc),
    )
    request = TransactionAssessmentRequest(
        amount=amount,
        currency="INR",
        occurred_at="2026-10-14T17:30:00+05:30",
        transaction_type="UPI",
        channel="Mobile app",
    )

    with patch(
        "backend.app.services.transaction_assessment_service."
        "send_review_notification",
        return_value={
            "status": "SENT",
            "message": "Email sent.",
            "subject": "Transaction review requested: MEDIUM",
            "content": "Attempted transaction details",
        },
    ) as send_notification:
        result = analyze_and_persist(db, request, user)

    assert result["risk_level"] == expected_risk
    assert result["review_notification_status"] == expected_email_status
    assert result["review_required"] is (expected_risk != "LOW")
    if expected_risk == "LOW":
        send_notification.assert_not_called()
        assert result["review_notification_content"] is None
    else:
        send_notification.assert_called_once()
        assert (
            send_notification.call_args.kwargs["recipient_email"]
            == user.email
        )
        assert result["review_notification_recipient"] == user.email
        assert (
            result["review_notification_content"]
            == "Attempted transaction details"
        )


def _batch_assessment_request(*amounts):
    return TransactionAssessmentBatchRequest(
        transactions=[
            TransactionAssessmentRequest(
                amount=amount,
                currency="INR",
                occurred_at="2026-10-14T17:30:00+05:30",
                transaction_type="UPI",
                channel="Mobile app",
                reference=f"batch-{index}",
            )
            for index, amount in enumerate(amounts, start=1)
        ]
    )


def _batch_test_db():
    db = MagicMock()
    db.add.side_effect = lambda obj: (
        setattr(obj, "id", uuid4())
        if isinstance(obj, (Transaction, TransactionAssessment))
        else None
    )
    db.refresh.side_effect = lambda assessment: setattr(
        assessment,
        "created_at",
        datetime.now(timezone.utc),
    )
    return db


def test_batch_assessment_sends_one_email_for_rows_above_amount_threshold():
    db = _batch_test_db()
    user = MagicMock(id=uuid4(), email="signed-in@example.test")

    with patch(
        "backend.app.services.transaction_assessment_service."
        "send_review_notification"
    ) as send_single, patch(
        "backend.app.services.transaction_assessment_service."
        "send_batch_review_notification",
        return_value={
            "status": "SENT",
            "message": "One email sent.",
            "recipient": user.email,
            "subject": "Batch threshold exceeded",
            "content": "Rows above threshold",
        },
    ) as send_batch:
        result = analyze_batch_and_persist(
            db,
            _batch_assessment_request(2_500, 100_000, 150_000, 1_000),
            user,
        )

    assert result["overall_risk_level"] == "HIGH"
    assert [item["risk_level"] for item in result["assessments"]] == [
        "MEDIUM",
        "HIGH",
        "HIGH",
        "LOW",
    ]
    assert result["review_notification_status"] == "SENT"
    send_single.assert_not_called()
    send_batch.assert_called_once()
    assert len(send_batch.call_args.kwargs["assessments"]) == 2
    assert send_batch.call_args.kwargs["assessments"][0]["amount"] == 100_000
    assert send_batch.call_args.kwargs["total_transactions"] == 4
    assert send_batch.call_args.kwargs["threshold_amount"] == 50_000
    db.commit.assert_called_once()


def test_medium_only_batch_sends_no_email():
    db = _batch_test_db()
    user = MagicMock(id=uuid4(), email="signed-in@example.test")

    with patch(
        "backend.app.services.transaction_assessment_service."
        "send_review_notification"
    ) as send_single, patch(
        "backend.app.services.transaction_assessment_service."
        "send_batch_review_notification"
    ) as send_batch:
        result = analyze_batch_and_persist(
            db,
            _batch_assessment_request(2_500, 50_000),
            user,
        )

    assert result["overall_risk_level"] == "MEDIUM"
    assert result["review_notification_status"] == "NOT_REQUIRED"
    send_single.assert_not_called()
    send_batch.assert_not_called()
    db.commit.assert_called_once()


def test_medium_transaction_just_above_50000_triggers_one_batch_email():
    db = _batch_test_db()
    user = MagicMock(id=uuid4(), email="signed-in@example.test")

    with patch(
        "backend.app.services.transaction_assessment_service."
        "send_batch_review_notification",
        return_value={
            "status": "SENT",
            "message": "One email sent.",
            "recipient": user.email,
            "subject": "Threshold exceeded",
            "content": "Medium-risk transaction",
        },
    ) as send_batch:
        result = analyze_batch_and_persist(
            db,
            _batch_assessment_request(50_000.01, 10_000),
            user,
        )

    assert result["assessments"][0]["risk_level"] == "MEDIUM"
    assert result["review_notification_status"] == "SENT"
    send_batch.assert_called_once()
    assert len(send_batch.call_args.kwargs["assessments"]) == 1
    assert send_batch.call_args.kwargs["assessments"][0]["amount"] == 50_000.01


def test_dashboard_history_query_includes_only_admins_own_assessments():
    db = MagicMock()
    db.scalar.return_value = 0
    db.execute.return_value.all.return_value = []
    user = MagicMock(id=uuid4(), role="ADMIN")

    result = list_assessment_history(db, user)

    sql = str(
        db.execute.call_args.args[0].compile(
            compile_kwargs={"literal_binds": True}
        )
    )

    assert result.total == 0
    assert "account-history-anomaly" in sql
    assert "fixed-amount-thresholds" in sql
    assert "transactions.user_id" in sql
    assert user.id.hex in sql


def test_pending_review_query_includes_only_admins_own_transactions():
    db = MagicMock()
    db.scalar.return_value = 0
    db.execute.return_value.all.return_value = []
    user = MagicMock(id=uuid4(), role="ADMIN")

    result = list_pending_reviews(db, user)

    sql = str(
        db.execute.call_args.args[0].compile(
            compile_kwargs={"literal_binds": True}
        )
    )

    assert result.total == 0
    assert "review_required" in sql
    assert "reviewed_at IS NULL" in sql
    assert "transactions.user_id" in sql
    assert user.id.hex in sql


def test_assessment_request_normalizes_currency_and_text():
    request = TransactionAssessmentRequest(
        amount=125.5,
        currency="inr",
        occurred_at="2026-10-14T17:30:00+05:30",
        transaction_type=" UPI ",
        channel=" Mobile app ",
        merchant="  Shop  ",
    )

    assert request.currency == "INR"
    assert request.transaction_type == "UPI"
    assert request.channel == "Mobile app"
    assert request.merchant == "Shop"


def test_assessment_request_rejects_empty_required_text_and_bad_currency():
    common = {
        "amount": 125.5,
        "currency": "INR",
        "occurred_at": "2026-10-14T17:30:00+05:30",
        "transaction_type": "UPI",
        "channel": "Mobile app",
    }

    for invalid in (
        {**common, "transaction_type": "  "},
        {**common, "channel": "  "},
        {**common, "currency": "IN"},
    ):
        with pytest.raises(ValidationError):
            TransactionAssessmentRequest(**invalid)


def test_review_decision_accepts_only_agree_or_disagree():
    assert ReviewDecisionRequest(decision="AGREE").decision == "AGREE"
    assert ReviewDecisionRequest(decision="DISAGREE").decision == "DISAGREE"
    with pytest.raises(ValidationError):
        ReviewDecisionRequest(decision="APPROVE")
