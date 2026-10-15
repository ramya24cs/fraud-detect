
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.audit_log import AuditLog
from backend.app.models.operator_feedback import OperatorFeedback
from backend.app.models.prediction import Prediction
from backend.app.models.transaction import Transaction
from backend.app.models.user import User
from backend.app.schemas.feedback import FeedbackRequest


def list_feedback(
    db: Session,
    *,
    user_id: UUID,
    limit: int = 50,
    offset: int = 0,
    transaction_id: UUID | None = None,
) -> tuple[list[OperatorFeedback], int]:
    """Return the current user's paginated feedback, newest first."""

    query = select(OperatorFeedback).where(
        OperatorFeedback.user_id == user_id
    )

    if transaction_id is not None:
        query = query.where(
            OperatorFeedback.transaction_id == transaction_id
        )

    total = db.scalar(
        select(func.count()).select_from(query.subquery())
    ) or 0

    rows = list(
        db.scalars(
            query.order_by(
                OperatorFeedback.created_at.desc(),
                OperatorFeedback.id.desc(),
            )
            .offset(offset)
            .limit(limit)
        ).all()
    )

    return rows, int(total)


def submit_feedback(
    db: Session,
    request: FeedbackRequest,
    current_user: User,
) -> OperatorFeedback:
    """Persist feedback and its audit record atomically."""

    transaction = db.scalar(
        select(Transaction).where(
            Transaction.id == request.transaction_id,
            Transaction.user_id == current_user.id,
        )
    )

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found.",
        )

    prediction = db.scalar(
        select(Prediction)
        .where(Prediction.transaction_id == transaction.id)
        .order_by(
            Prediction.created_at.desc(),
            Prediction.id.desc(),
        )
        .limit(1)
    )

    if prediction is None:
        raise HTTPException(
            status_code=409,
            detail="Feedback cannot be submitted before a prediction exists.",
        )

    reason_code = request.reason_code.strip()
    comment = request.comment.strip() if request.comment else None

    if not reason_code:
        raise HTTPException(
            status_code=422,
            detail="A non-empty reason code is required.",
        )

    try:
        feedback = OperatorFeedback(
            transaction_id=transaction.id,
            user_id=current_user.id,
            decision=request.operator_decision,
            reason_code=reason_code,
            comment=comment or None,
        )

        db.add(feedback)
        db.flush()

        db.add(
            AuditLog(
                user_id=current_user.id,
                action="SUBMIT_FEEDBACK",
                entity_type="operator_feedback",
                entity_id=str(feedback.id),
                metadata_json={
                    "transaction_id": str(transaction.id),
                    "prediction_id": str(prediction.id),
                    "operator_decision": request.operator_decision,
                    "reason_code": reason_code,
                },
            )
        )

        db.commit()
        db.refresh(feedback)
        return feedback

    except Exception:
        db.rollback()
        raise
