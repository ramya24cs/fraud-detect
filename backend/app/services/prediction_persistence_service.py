
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.models.audit_log import AuditLog
from backend.app.models.prediction import Prediction
from backend.app.models.transaction import Transaction


def persist_prediction(
    db: Session,
    external_id: str,
    features: dict[str, float],
    result: dict[str, Any],
    user_id: UUID | None = None,
) -> dict[str, Any]:
    """Persist a transaction, prediction, and audit event atomically."""
    try:
        risk_alert_status = (
            "PENDING" if result["risk_level"] == "HIGH" else "NOT_REQUIRED"
        )
        query = select(Transaction).where(
            Transaction.external_id == external_id,
        )

        if user_id is not None:
            query = query.where(Transaction.user_id == user_id)
        else:
            query = query.where(Transaction.user_id.is_(None))

        transaction = db.scalar(query.with_for_update())

        if transaction is None:
            transaction = Transaction(
                user_id=user_id,
                external_id=external_id,
                payload_json=features,
                amount=features["Amount"],
            )
            db.add(transaction)
            db.flush()
        else:
            transaction.payload_json = features
            transaction.amount = features["Amount"]
            db.flush()

        prediction = Prediction(
            transaction_id=transaction.id,
            model_version=str(result["model_version"]),
            probability=float(result["fraud_probability"]),
            risk_level=str(result["risk_level"]),
            decision=str(result["decision"]),
            expected_cost=float(result["expected_cost"]),
            risk_alert_status=risk_alert_status,
            created_at=datetime.now(timezone.utc),
        )
        db.add(prediction)
        db.flush()

        db.add(
            AuditLog(
                user_id=user_id,
                action="PREDICTION_CREATED",
                entity_type="prediction",
                entity_id=str(prediction.id),
                metadata_json={
                    "transaction_id": str(transaction.id),
                    "external_id": external_id,
                    "decision": prediction.decision,
                    "model_version": prediction.model_version,
                },
            )
        )
        if prediction.risk_level == "HIGH":
            db.add(
                AuditLog(
                    user_id=user_id,
                    action="HIGH_RISK_ALERT_TRIGGERED",
                    entity_type="prediction",
                    entity_id=str(prediction.id),
                    metadata_json={
                        "transaction_id": str(transaction.id),
                        "fraud_probability": prediction.probability,
                        "decision": prediction.decision,
                        "risk_alert_status": risk_alert_status,
                    },
                )
            )

        response = {
            "transaction_id": transaction.id,
            "prediction_id": prediction.id,
            "fraud_probability": prediction.probability,
            "risk_level": prediction.risk_level,
            "decision": prediction.decision,
            "expected_cost": prediction.expected_cost,
            "model_version": prediction.model_version,
            "explanation": result["explanation"],
            "prediction_timestamp": prediction.created_at,
            "probability_calibrated": result["probability_calibrated"],
            "review_required": prediction.decision == "REVIEW",
            "risk_alert_triggered": prediction.risk_level == "HIGH",
            "risk_alert_status": prediction.risk_alert_status,
        }

        db.commit()
        return response

    except Exception:
        db.rollback()
        raise


def update_prediction_risk_alert_status(
    db: Session,
    prediction_id: UUID,
    user_id: UUID | None,
    status: str,
) -> None:
    """Persist the delivery result for an already-triggered high-risk alert."""
    try:
        prediction = db.get(Prediction, prediction_id)
        if prediction is None:
            raise LookupError(f"Prediction {prediction_id} was not found.")

        prediction.risk_alert_status = status
        db.add(
            AuditLog(
                user_id=user_id,
                action="HIGH_RISK_ALERT_NOTIFICATION_UPDATED",
                entity_type="prediction",
                entity_id=str(prediction.id),
                metadata_json={"risk_alert_status": status},
            )
        )
        db.commit()
    except Exception:
        db.rollback()
        raise
