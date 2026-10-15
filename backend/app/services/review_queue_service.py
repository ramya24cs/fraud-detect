
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.models.prediction import Prediction
from backend.app.models.transaction import Transaction
from backend.app.schemas.review_queue import (
    ReviewQueueItem,
    ReviewQueueResponse,
)


def get_review_queue(
    db: Session,
    user_id: UUID,
    limit: int = 50,
    offset: int = 0,
) -> ReviewQueueResponse:
    base_query = (
        select(Prediction, Transaction)
        .join(
            Transaction,
            Prediction.transaction_id == Transaction.id,
        )
        .where(
            Prediction.decision == "REVIEW",
            Transaction.user_id == user_id,
        )
    )

    total = db.scalar(
        select(func.count()).select_from(base_query.subquery())
    ) or 0

    rows = db.execute(
        base_query
        .order_by(
            Prediction.created_at.desc(),
            Prediction.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    ).all()

    items = [
        ReviewQueueItem(
            prediction_id=prediction.id,
            transaction_id=transaction.id,
            external_id=transaction.external_id,
            amount=transaction.amount,
            fraud_probability=prediction.probability,
            risk_level=prediction.risk_level,
            decision=prediction.decision,
            expected_cost=prediction.expected_cost,
            model_version=prediction.model_version,
            created_at=prediction.created_at,
        )
        for prediction, transaction in rows
    ]

    return ReviewQueueResponse(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )
