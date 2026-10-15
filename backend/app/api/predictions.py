
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.deps import get_current_user
from backend.app.db.session import get_db
from backend.app.models.prediction import Prediction
from backend.app.models.transaction import Transaction
from backend.app.models.user import User
from backend.app.schemas.prediction import (
    PredictionRequest,
    PredictionResponse,
)
from backend.app.schemas.transaction_assessment import (
    AssessmentHistoryList,
    PendingReviewList,
    ReviewDecisionRequest,
    ReviewDecisionResponse,
    RiskAlertList,
    TransactionAssessmentRequest,
    TransactionAssessmentResponse,
)
from backend.app.services.prediction_service import (
    predict_and_persist,
    summarize_prediction,
)
from backend.app.services.transaction_assessment_service import (
    analyze_and_persist,
    list_assessment_history,
    list_pending_reviews,
    list_risk_alerts,
    record_review_decision,
)


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)


@router.post(
    "/predict",
    response_model=PredictionResponse,
    status_code=status.HTTP_201_CREATED,
)
def predict_transaction(
    request: PredictionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PredictionResponse:
    """Evaluate a transaction and persist its prediction."""

    result = predict_and_persist(
        db=db,
        request=request,
        current_user=current_user,
    )

    return PredictionResponse(**result)


@router.post(
    "/analyze",
    response_model=TransactionAssessmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def analyze_transaction(
    request: TransactionAssessmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TransactionAssessmentResponse:
    """Assess a transaction using the configured amount bands."""
    result = analyze_and_persist(
        db=db,
        request=request,
        current_user=current_user,
    )
    return TransactionAssessmentResponse(**result)


@router.get("/risk-alerts", response_model=RiskAlertList)
def get_risk_alerts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskAlertList:
    """List persisted high anomaly alerts for the authenticated user."""
    return list_risk_alerts(db=db, current_user=current_user)


@router.get("/assessments", response_model=AssessmentHistoryList)
def get_assessments(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AssessmentHistoryList:
    """List transaction-form assessments for the authenticated account."""
    if limit < 1 or limit > 500 or offset < 0:
        raise HTTPException(status_code=422, detail="Invalid pagination.")
    return list_assessment_history(
        db=db,
        current_user=current_user,
        limit=limit,
        offset=offset,
    )


@router.get("/reviews/pending", response_model=PendingReviewList)
def get_pending_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> PendingReviewList:
    """List the current user's assessments waiting for a human decision."""
    return list_pending_reviews(db=db, current_user=current_user)


@router.post(
    "/assessments/{assessment_id}/review",
    response_model=ReviewDecisionResponse,
)
def review_assessment(
    assessment_id: UUID,
    request: ReviewDecisionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ReviewDecisionResponse:
    """Record an authenticated human agree/disagree decision."""
    return record_review_decision(
        db=db,
        assessment_id=assessment_id,
        request=request,
        current_user=current_user,
    )


@router.get("/{transaction_id}")
def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    """Retrieve the current user's transaction and its latest prediction."""

    transaction_query = select(Transaction).where(
        Transaction.user_id == current_user.id
    )

    try:
        transaction_uuid = UUID(transaction_id)
    except ValueError:
        transaction_uuid = None

    if transaction_uuid is not None:
        transaction = db.scalar(
            transaction_query.where(Transaction.id == transaction_uuid)
        )
    else:
        transaction = db.scalar(
            transaction_query.where(
                Transaction.external_id == transaction_id
            )
        )

    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No prediction exists for this transaction.",
        )

    return {
        "transaction_id": str(transaction.id),
        "external_id": transaction.external_id,
        "amount": transaction.amount,
        "features": transaction.payload_json,
        "created_at": transaction.created_at,
        "prediction": {
            "fraud_probability": prediction.probability,
            "risk_level": prediction.risk_level,
            "decision": prediction.decision,
            "expected_cost": prediction.expected_cost,
            "model_version": prediction.model_version,
            "explanation_summary": summarize_prediction(
                fraud_probability=prediction.probability,
                risk_level=prediction.risk_level,
                decision=prediction.decision,
            ),
            "prediction_timestamp": prediction.created_at,
            "probability_calibrated": False,
            "review_required": prediction.decision == "REVIEW",
            "risk_alert_status": prediction.risk_alert_status,
            "risk_alert_triggered": prediction.risk_level == "HIGH",
            "created_at": prediction.created_at,
        },
    }
