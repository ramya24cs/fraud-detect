from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.audit_log import AuditLog
from backend.app.models.transaction import Transaction
from backend.app.models.transaction_assessment import TransactionAssessment
from backend.app.models.user import User
from backend.app.schemas.transaction_assessment import (
    AssessmentHistoryItem,
    AssessmentHistoryList,
    PendingReviewItem,
    PendingReviewList,
    ReviewDecisionRequest,
    ReviewDecisionResponse,
    RiskAlertItem,
    RiskAlertList,
    TransactionAssessmentBatchRequest,
    TransactionAssessmentRequest,
)
from backend.app.services.review_notification_service import (
    send_batch_review_notification,
    send_review_notification,
)

logger = logging.getLogger(__name__)

POLICY_VERSION = "transaction-review-v1"
LOW_AMOUNT_MAX = 2_000.0
HIGH_AMOUNT_MIN = 99_999.0
BATCH_EMAIL_AMOUNT_THRESHOLD = 50_000.0


def assess_transaction_amount(current: dict[str, Any]) -> dict[str, Any]:
    """Assign a provisional risk band using only the entered amount."""
    amount = float(current["amount"])

    if amount <= LOW_AMOUNT_MAX:
        risk_level = "LOW"
        anomaly_score = 0
        reason = "No additional human review is required."
    elif amount < HIGH_AMOUNT_MIN:
        risk_level = "MEDIUM"
        anomaly_score = 50
        reason = "This transaction needs a human review."
    else:
        risk_level = "HIGH"
        anomaly_score = 100
        reason = "This transaction needs a human review."

    return {
        "anomaly_score": anomaly_score,
        "risk_level": risk_level,
        "reasons": [reason],
        "history_count": 0,
        "review_required": risk_level in {"MEDIUM", "HIGH"},
        "alert_created": risk_level == "HIGH",
    }


def analyze_and_persist(
    db: Session,
    request: TransactionAssessmentRequest,
    current_user: User,
) -> dict[str, Any]:
    """Persist an account-owned transaction and its amount-band assessment."""
    payload = {
        "amount": request.amount,
        "currency": request.currency,
        "occurred_at": request.occurred_at.isoformat(),
        "transaction_type": request.transaction_type,
        "merchant": request.merchant,
        "channel": request.channel,
        "reference": request.reference,
        "location": request.location,
        "remarks": request.remarks,
        "assessment_type": "fixed-amount-thresholds",
    }

    try:
        outcome = assess_transaction_amount(payload)

        transaction = Transaction(
            user_id=current_user.id,
            external_id=f"assessment-{uuid4()}",
            payload_json=payload,
            amount=request.amount,
        )
        db.add(transaction)
        db.flush()

        assessment = TransactionAssessment(
            transaction_id=transaction.id,
            anomaly_score=outcome["anomaly_score"],
            risk_level=outcome["risk_level"],
            reasons=outcome["reasons"],
            history_count=outcome["history_count"],
            review_required=outcome["review_required"],
            alert_created=outcome["alert_created"],
            policy_version=POLICY_VERSION,
        )
        db.add(assessment)
        db.flush()

        db.add(
            AuditLog(
                user_id=current_user.id,
                action="TRANSACTION_ASSESSED",
                entity_type="transaction_assessment",
                entity_id=str(assessment.id),
                metadata_json={
                    "transaction_id": str(transaction.id),
                    "risk_level": assessment.risk_level,
                    "anomaly_score": assessment.anomaly_score,
                    "policy_version": POLICY_VERSION,
                },
            )
        )
        db.commit()
        db.refresh(assessment)

        notification = (
            send_review_notification(
                assessment_id=assessment.id,
                recipient_email=current_user.email,
                transaction=payload,
                risk_level=assessment.risk_level,
            )
            if assessment.review_required
            else {
                "status": "NOT_REQUIRED",
                "message": None,
                "subject": None,
                "content": None,
            }
        )

        return {
            "assessment_id": assessment.id,
            "transaction_id": transaction.id,
            "amount": request.amount,
            "currency": request.currency,
            "occurred_at": request.occurred_at,
            "anomaly_score": assessment.anomaly_score,
            "risk_level": assessment.risk_level,
            "reasons": assessment.reasons,
            "history_count": assessment.history_count,
            "review_required": assessment.review_required,
            "alert_created": assessment.alert_created,
            "policy_version": assessment.policy_version,
            "review_notification_status": notification["status"],
            "review_notification_message": notification["message"],
            "review_notification_recipient": (
                current_user.email if assessment.review_required else None
            ),
            "review_notification_subject": notification["subject"],
            "review_notification_content": notification["content"],
            "created_at": assessment.created_at,
        }
    except Exception:
        db.rollback()
        logger.exception("Failed to assess and persist transaction")
        raise


def analyze_batch_and_persist(
    db: Session,
    request: TransactionAssessmentBatchRequest,
    current_user: User,
) -> dict[str, Any]:
    """Assess a file batch and email once if any amount exceeds the threshold."""
    pending_results: list[dict[str, Any]] = []
    batch_assessments: list[dict[str, Any]] = []

    try:
        for item in request.transactions:
            payload = {
                "amount": item.amount,
                "currency": item.currency,
                "occurred_at": item.occurred_at.isoformat(),
                "transaction_type": item.transaction_type,
                "merchant": item.merchant,
                "channel": item.channel,
                "reference": item.reference,
                "location": item.location,
                "remarks": item.remarks,
                "assessment_type": "fixed-amount-thresholds",
            }
            outcome = assess_transaction_amount(payload)
            transaction = Transaction(
                user_id=current_user.id,
                external_id=f"assessment-{uuid4()}",
                payload_json=payload,
                amount=item.amount,
            )
            db.add(transaction)
            db.flush()

            assessment = TransactionAssessment(
                transaction_id=transaction.id,
                anomaly_score=outcome["anomaly_score"],
                risk_level=outcome["risk_level"],
                reasons=outcome["reasons"],
                history_count=outcome["history_count"],
                review_required=outcome["review_required"],
                alert_created=outcome["alert_created"],
                policy_version=POLICY_VERSION,
            )
            db.add(assessment)
            db.flush()
            db.add(
                AuditLog(
                    user_id=current_user.id,
                    action="TRANSACTION_ASSESSED",
                    entity_type="transaction_assessment",
                    entity_id=str(assessment.id),
                    metadata_json={
                        "transaction_id": str(transaction.id),
                        "risk_level": assessment.risk_level,
                        "anomaly_score": assessment.anomaly_score,
                        "policy_version": POLICY_VERSION,
                        "assessment_source": "file_batch",
                    },
                )
            )
            pending_results.append(
                {
                    "request": item,
                    "payload": payload,
                    "transaction": transaction,
                    "assessment": assessment,
                }
            )

        db.commit()
        for result in pending_results:
            db.refresh(result["assessment"])
    except Exception:
        db.rollback()
        logger.exception("Failed to assess and persist transaction batch")
        raise

    risk_rank = {"LOW": 0, "MEDIUM": 1, "HIGH": 2}
    overall_risk_level = max(
        (
            result["assessment"].risk_level
            for result in pending_results
        ),
        key=risk_rank.__getitem__,
    )
    threshold_items = [
        {
            "assessment_id": result["assessment"].id,
            "risk_level": result["assessment"].risk_level,
            "amount": result["request"].amount,
            "currency": result["request"].currency,
            "occurred_at": result["request"].occurred_at.isoformat(),
            "reference": result["request"].reference,
            "merchant": result["request"].merchant,
        }
        for result in pending_results
        if result["request"].amount > BATCH_EMAIL_AMOUNT_THRESHOLD
    ]

    if threshold_items:
        notification = send_batch_review_notification(
            recipient_email=current_user.email,
            assessments=threshold_items,
            total_transactions=len(pending_results),
            threshold_amount=BATCH_EMAIL_AMOUNT_THRESHOLD,
        )
    else:
        notification = {
            "status": "NOT_REQUIRED",
            "message": (
                "No transaction amount exceeded 50,000; no email was sent."
            ),
            "recipient": None,
            "subject": None,
            "content": None,
        }

    assessments = []
    for result in pending_results:
        request_item = result["request"]
        transaction = result["transaction"]
        assessment = result["assessment"]
        assessments.append(
            {
                "assessment_id": assessment.id,
                "transaction_id": transaction.id,
                "amount": request_item.amount,
                "currency": request_item.currency,
                "occurred_at": request_item.occurred_at,
                "anomaly_score": assessment.anomaly_score,
                "risk_level": assessment.risk_level,
                "reasons": assessment.reasons,
                "history_count": assessment.history_count,
                "review_required": assessment.review_required,
                "alert_created": assessment.alert_created,
                "policy_version": assessment.policy_version,
                "review_notification_status": "NOT_REQUIRED",
                "review_notification_message": None,
                "review_notification_recipient": None,
                "review_notification_subject": None,
                "review_notification_content": None,
                "created_at": assessment.created_at,
            }
        )

    return {
        "assessments": assessments,
        "overall_risk_level": overall_risk_level,
        "review_notification_status": notification["status"],
        "review_notification_message": notification["message"],
        "review_notification_recipient": notification["recipient"],
        "review_notification_subject": notification["subject"],
        "review_notification_content": notification["content"],
    }


def list_risk_alerts(
    db: Session,
    current_user: User,
    limit: int = 50,
) -> RiskAlertList:
    """Return the authenticated user's saved HIGH amount assessments."""
    query = (
        select(TransactionAssessment, Transaction)
        .join(Transaction, Transaction.id == TransactionAssessment.transaction_id)
        .where(
            Transaction.user_id == current_user.id,
            TransactionAssessment.alert_created.is_(True),
        )
    )
    total = int(
        db.scalar(select(func.count()).select_from(query.subquery())) or 0
    )
    rows = db.execute(
        query.order_by(
            TransactionAssessment.created_at.desc(),
            TransactionAssessment.id.desc(),
        ).limit(limit)
    ).all()

    items = [
        RiskAlertItem(
            assessment_id=assessment.id,
            transaction_id=transaction.id,
            reference=(transaction.payload_json or {}).get("reference"),
            amount=transaction.amount,
            currency=(transaction.payload_json or {}).get("currency", "N/A"),
            anomaly_score=assessment.anomaly_score or 0,
            risk_level=assessment.risk_level,
            reasons=assessment.reasons,
            created_at=assessment.created_at,
        )
        for assessment, transaction in rows
    ]
    return RiskAlertList(items=items, total=total)


def list_pending_reviews(
    db: Session,
    current_user: User,
) -> PendingReviewList:
    """Return unreviewed assessments awaiting a human decision."""
    query = (
        select(TransactionAssessment, Transaction)
        .join(Transaction, Transaction.id == TransactionAssessment.transaction_id)
        .where(
            TransactionAssessment.review_required.is_(True),
            TransactionAssessment.reviewed_at.is_(None),
            Transaction.user_id == current_user.id,
        )
    )
    total = int(
        db.scalar(select(func.count()).select_from(query.subquery())) or 0
    )
    rows = db.execute(
        query.order_by(
            TransactionAssessment.created_at.desc(),
            TransactionAssessment.id.desc(),
        )
    ).all()

    items: list[PendingReviewItem] = []
    for assessment, transaction in rows:
        payload = transaction.payload_json or {}
        items.append(
            PendingReviewItem(
                assessment_id=assessment.id,
                transaction_id=transaction.id,
                amount=transaction.amount,
                currency=payload["currency"],
                occurred_at=payload["occurred_at"],
                transaction_type=payload["transaction_type"],
                merchant=payload.get("merchant"),
                channel=payload["channel"],
                reference=payload.get("reference"),
                location=payload.get("location"),
                anomaly_score=assessment.anomaly_score or 0,
                risk_level=assessment.risk_level,
                reasons=assessment.reasons,
                history_count=assessment.history_count,
                created_at=assessment.created_at,
            )
        )
    return PendingReviewList(items=items, total=total)


def list_assessment_history(
    db: Session,
    current_user: User,
    *,
    limit: int = 200,
    offset: int = 0,
) -> AssessmentHistoryList:
    query = (
        select(TransactionAssessment, Transaction)
        .join(Transaction, Transaction.id == TransactionAssessment.transaction_id)
        .where(
            Transaction.payload_json["assessment_type"]
            .as_string()
            .in_(("account-history-anomaly", "fixed-amount-thresholds")),
            Transaction.user_id == current_user.id,
        )
    )

    total = int(
        db.scalar(select(func.count()).select_from(query.subquery())) or 0
    )
    rows = db.execute(
        query.order_by(
            TransactionAssessment.created_at.desc(),
            TransactionAssessment.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    ).all()

    items: list[AssessmentHistoryItem] = []
    for assessment, transaction in rows:
        payload = transaction.payload_json or {}
        items.append(
            AssessmentHistoryItem(
                assessment_id=assessment.id,
                transaction_id=transaction.id,
                amount=transaction.amount,
                currency=payload.get("currency", "N/A"),
                occurred_at=payload.get(
                    "occurred_at", transaction.created_at
                ),
                transaction_type=payload.get("transaction_type", "Unknown"),
                merchant=payload.get("merchant"),
                channel=payload.get("channel", "Unknown"),
                reference=payload.get("reference"),
                location=payload.get("location"),
                anomaly_score=assessment.anomaly_score or 0,
                risk_level=assessment.risk_level,
                reasons=assessment.reasons,
                history_count=assessment.history_count,
                created_at=assessment.created_at,
                review_required=assessment.review_required,
                alert_created=assessment.alert_created,
                review_decision=assessment.review_decision,
                review_comment=assessment.review_comment,
                reviewed_at=assessment.reviewed_at,
                policy_version=assessment.policy_version,
            )
        )
    return AssessmentHistoryList(items=items, total=total)


def record_review_decision(
    db: Session,
    *,
    assessment_id: UUID,
    request: ReviewDecisionRequest,
    current_user: User,
) -> ReviewDecisionResponse:
    query = (
        select(TransactionAssessment, Transaction)
        .join(Transaction, Transaction.id == TransactionAssessment.transaction_id)
        .where(TransactionAssessment.id == assessment_id)
    )
    if current_user.role != "ADMIN":
        query = query.where(Transaction.user_id == current_user.id)
    row = db.execute(query.with_for_update()).one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="Assessment not found.")

    assessment, transaction = row
    if not assessment.review_required:
        raise HTTPException(
            status_code=409,
            detail="This assessment does not require human review.",
        )
    if assessment.reviewed_at is not None:
        raise HTTPException(
            status_code=409,
            detail="A human decision has already been recorded.",
        )

    try:
        assessment.review_decision = request.decision
        assessment.review_comment = request.comment
        assessment.reviewed_by = current_user.id
        assessment.reviewed_at = datetime.now(timezone.utc)
        db.add(
            AuditLog(
                user_id=current_user.id,
                action="ASSESSMENT_REVIEWED",
                entity_type="transaction_assessment",
                entity_id=str(assessment.id),
                metadata_json={
                    "transaction_id": str(transaction.id),
                    "review_decision": request.decision,
                },
            )
        )
        db.commit()
        db.refresh(assessment)
    except Exception as exc:
        db.rollback()
        logger.exception(
            "Failed to record human decision for assessment %s",
            assessment_id,
        )
        raise HTTPException(
            status_code=500,
            detail="The human review decision could not be saved.",
        ) from exc

    return ReviewDecisionResponse(
        assessment_id=assessment.id,
        transaction_id=transaction.id,
        decision=request.decision,
        comment=assessment.review_comment,
        reviewed_at=assessment.reviewed_at,
    )
