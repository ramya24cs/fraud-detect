
from __future__ import annotations

import importlib
import logging
import math
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from backend.app.models.user import User
from backend.app.schemas.prediction import PredictionRequest
from backend.app.services.prediction_persistence_service import (
    persist_prediction,
    update_prediction_risk_alert_status,
)
from backend.app.services.risk_service import classify_risk
from backend.app.services.review_notification_service import (
    send_prediction_risk_alert,
)
from ml.src.decision.cost_matrix import Decision

logger = logging.getLogger(__name__)


def summarize_prediction(
    fraud_probability: float,
    risk_level: str,
    decision: str,
) -> str:
    """Explain the model estimate and action without claiming causal evidence."""
    return (
        f"The raw model output is {fraud_probability:.2%} fraud probability "
        f"({risk_level} risk). The expected-cost policy recommends {decision}."
    )


def _evaluate_with_ml(features: dict[str, float]) -> dict[str, Any]:
    """Evaluate a transaction using the existing ML decision engine."""
    try:
        decision_module = importlib.import_module(
            "ml.src.decision.decision_engine"
        )
        defaults_module = importlib.import_module(
            "ml.src.decision.defaults"
        )

        # Action is selected by minimum expected cost; risk tier is calculated
        # independently below from the configured probability bands.
        cost_matrix = defaults_module.approved_cost_matrix()

        result = decision_module.evaluate_transaction(
            transaction=features,
            cost_matrix=cost_matrix,
            top_k=5,
        )

        if not isinstance(result, dict):
            raise ValueError(
                "Decision engine must return a dictionary."
            )

        required = {
            "fraud_probability",
            "decision",
            "expected_cost",
            "model_version",
            "explanation",
        }

        missing = required - set(result)
        if missing:
            raise ValueError(
                f"Decision engine result is missing fields: "
                f"{sorted(missing)}"
            )

        probability = float(result["fraud_probability"])
        expected_cost = float(result["expected_cost"])

        if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
            raise ValueError(
                "Fraud probability must be finite and between 0 and 1."
            )

        if not math.isfinite(expected_cost) or expected_cost < 0:
            raise ValueError(
                "Expected cost must be finite and non-negative."
            )

        if result["decision"] not in {decision.value for decision in Decision}:
            raise ValueError(
                "Decision engine returned an invalid decision."
            )

        risk_level = classify_risk(probability)
        result["risk_level"] = risk_level
        if risk_level == "LOW":
            result["expected_cost"] = 0.0
        result["probability_calibrated"] = False
        return result

    except HTTPException:
        raise
    except Exception as exc:
        # Print the complete traceback to the API container logs.
        logger.exception("ML prediction pipeline failed")

        # Keep internal exception details out of the client response.
        raise HTTPException(
            status_code=503,
            detail=(
                "The prediction pipeline is unavailable or returned "
                "an invalid result. Check the API container logs "
                "for the underlying exception."
            ),
        ) from exc


def predict_and_persist(
    db: Session,
    request: PredictionRequest,
    current_user: User,
) -> dict[str, Any]:
    """Evaluate a transaction and persist its prediction and audit event."""
    result = _evaluate_with_ml(request.features)

    try:
        response = persist_prediction(
            db=db,
            external_id=request.transaction_id,
            features=request.features,
            result=result,
            user_id=current_user.id,
        )
    except Exception as exc:
        logger.exception(
            "Prediction evaluated, but persistence failed"
        )
        raise HTTPException(
            status_code=500,
            detail=(
                "The prediction was evaluated but could not be persisted."
            ),
        ) from exc

    if response["risk_level"] == "HIGH":
        notification = send_prediction_risk_alert(
            recipient_email=current_user.email,
            transaction_id=response["transaction_id"],
            transaction=request.features,
            fraud_probability=response["fraud_probability"],
            decision=response["decision"],
        )
        response["risk_alert_status"] = notification["status"]
        response["risk_alert_message"] = notification["message"]
        try:
            update_prediction_risk_alert_status(
                db=db,
                prediction_id=response["prediction_id"],
                user_id=current_user.id,
                status=notification["status"],
            )
        except Exception:
            logger.exception(
                "Prediction alert status could not be saved for %s",
                response["prediction_id"],
            )
            response["risk_alert_status"] = "STATUS_NOT_SAVED"
            response["risk_alert_message"] = (
                "The prediction and alert were processed, but the alert "
                "delivery status could not be saved. Check backend logs."
            )
    else:
        response["risk_alert_message"] = None

    response["explanation_summary"] = summarize_prediction(
        fraud_probability=response["fraud_probability"],
        risk_level=response["risk_level"],
        decision=response["decision"],
    )
    return response
