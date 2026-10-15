"""Prediction-service exception and contract tests."""

from unittest.mock import MagicMock, patch
from uuid import uuid4
from datetime import datetime, timezone

import pytest
from fastapi import HTTPException

from backend.app.schemas.prediction import PredictionRequest
from backend.app.services import prediction_service
from backend.app.services.risk_service import classify_risk
from backend.app.schemas.prediction import PredictionResponse


def _valid_features():
    return {
        "Time": 1000.0,
        **{f"V{i}": 0.1 for i in range(1, 29)},
        "Amount": 150.0,
    }


def test_classify_risk_separates_probability_from_decision():
    cases = [
        (0.0, "LOW"),
        (0.2999, "LOW"),
        (0.30, "MEDIUM"),
        (0.6999, "MEDIUM"),
        (0.70, "HIGH"),
        (1.0, "HIGH"),
    ]
    for probability, expected in cases:
        assert classify_risk(
            probability,
            low_threshold=0.30,
            high_threshold=0.70,
        ) == expected


@pytest.mark.parametrize(
    "probability",
    [-0.001, 1.001, float("nan"), float("inf"), float("-inf")],
)
def test_classify_risk_rejects_invalid_probability(probability):
    with pytest.raises(ValueError):
        classify_risk(probability)


def test_evaluate_with_ml_returns_validated_decision_fields():
    fake_result = {
        "fraud_probability": 0.35,
        "decision": "REVIEW",
        "expected_cost": 7.9,
        "model_version": "xgb-cost-v1",
        "explanation": [{"feature": "V14", "impact": 1.2}],
    }

    with patch.object(
        prediction_service.importlib,
        "import_module",
    ) as import_module:
        decision_module = MagicMock()
        defaults_module = MagicMock()
        defaults_module.approved_cost_matrix.return_value = MagicMock()
        decision_module.evaluate_transaction.return_value = fake_result

        import_module.side_effect = [
            decision_module,
            defaults_module,
        ]

        result = prediction_service._evaluate_with_ml(_valid_features())

    assert result["decision"] == "REVIEW"
    assert result["risk_level"] == "MEDIUM"
    assert result["probability_calibrated"] is False
    assert 0.0 <= result["fraud_probability"] <= 1.0


def test_low_risk_prediction_has_zero_expected_cost():
    with patch.object(
        prediction_service.importlib,
        "import_module",
    ) as import_module:
        decision_module = MagicMock()
        defaults_module = MagicMock()
        defaults_module.approved_cost_matrix.return_value = MagicMock()
        decision_module.evaluate_transaction.return_value = {
            "fraud_probability": 0.10,
            "decision": "APPROVE",
            "expected_cost": 10.0,
            "model_version": "xgb-cost-v1",
            "explanation": [],
        }
        import_module.side_effect = [decision_module, defaults_module]
        result = prediction_service._evaluate_with_ml(_valid_features())

    assert result["risk_level"] == "LOW"
    assert result["expected_cost"] == 0.0


@pytest.mark.parametrize(
    "probability",
    [-0.001, 1.001, float("nan"), float("inf"), float("-inf")],
)
def test_ml_result_rejects_invalid_model_probability(probability):
    with patch.object(
        prediction_service.importlib,
        "import_module",
    ) as import_module:
        decision_module = MagicMock()
        defaults_module = MagicMock()
        defaults_module.approved_cost_matrix.return_value = MagicMock()
        decision_module.evaluate_transaction.return_value = {
            "fraud_probability": probability,
            "decision": "REVIEW",
            "expected_cost": 1.0,
            "model_version": "xgb-cost-v1",
            "explanation": [],
        }
        import_module.side_effect = [decision_module, defaults_module]
        with pytest.raises(HTTPException) as exc_info:
            prediction_service._evaluate_with_ml(_valid_features())

    assert exc_info.value.status_code == 503


def test_risk_level_is_independent_of_cost_sensitive_action():
    with patch.object(
        prediction_service.importlib,
        "import_module",
    ) as import_module:
        decision_module = MagicMock()
        defaults_module = MagicMock()
        defaults_module.approved_cost_matrix.return_value = MagicMock()
        decision_module.evaluate_transaction.return_value = {
            "fraud_probability": 0.50,
            "decision": "BLOCK",
            "expected_cost": 7.9,
            "model_version": "xgb-cost-v1",
            "explanation": [],
        }
        import_module.side_effect = [decision_module, defaults_module]
        result = prediction_service._evaluate_with_ml(_valid_features())

    assert result["risk_level"] == "MEDIUM"
    assert result["decision"] == "BLOCK"


def test_prediction_api_response_keeps_server_risk_for_frontend():
    timestamp = datetime.now(timezone.utc)
    response = PredictionResponse(
        transaction_id=uuid4(),
        fraud_probability=0.70,
        risk_level=classify_risk(0.70),
        decision="REVIEW",
        expected_cost=2.0,
        model_version="xgb-cost-v1",
        explanation_summary=prediction_service.summarize_prediction(
            fraud_probability=0.70,
            risk_level="HIGH",
            decision="REVIEW",
        ),
        explanation=[],
        prediction_timestamp=timestamp,
        probability_calibrated=False,
        review_required=True,
        risk_alert_triggered=True,
        risk_alert_status="NOT_CONFIGURED",
        risk_alert_message="SMTP is not configured.",
    )

    payload = response.model_dump(mode="json")
    assert payload["risk_level"] == "HIGH"
    assert payload["fraud_probability"] == 0.70
    assert payload["decision"] == "REVIEW"
    assert "raw model output" in payload["explanation_summary"].lower()
    assert "HIGH risk" in payload["explanation_summary"]
    assert "REVIEW" in payload["explanation_summary"]
    returned_timestamp = datetime.fromisoformat(
        payload["prediction_timestamp"].replace("Z", "+00:00")
    )
    assert returned_timestamp == timestamp
    assert payload["probability_calibrated"] is False
    assert payload["risk_alert_status"] == "NOT_CONFIGURED"


def test_evaluate_with_ml_maps_pipeline_errors_to_http_503():
    with patch.object(
        prediction_service.importlib,
        "import_module",
        side_effect=RuntimeError("simulated pipeline failure"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            prediction_service._evaluate_with_ml(_valid_features())

    assert exc_info.value.status_code == 503
    assert "prediction pipeline is unavailable" in exc_info.value.detail.lower()
    # Client response must not leak the internal exception text.
    assert "simulated pipeline failure" not in exc_info.value.detail


def test_predict_and_persist_propagates_persistence_failure_as_500():
    user = MagicMock()
    user.id = uuid4()
    request = PredictionRequest(
        transaction_id="synth-tx-001",
        features=_valid_features(),
    )

    with patch.object(
        prediction_service,
        "_evaluate_with_ml",
        return_value={
            "fraud_probability": 0.2,
            "risk_level": "MEDIUM",
            "decision": "REVIEW",
            "expected_cost": 5.0,
            "model_version": "xgb-cost-v1",
            "explanation": [],
            "probability_calibrated": False,
        },
    ), patch.object(
        prediction_service,
        "persist_prediction",
        side_effect=RuntimeError("db down"),
    ):
        with pytest.raises(HTTPException) as exc_info:
            prediction_service.predict_and_persist(
                db=MagicMock(),
                request=request,
                current_user=user,
            )

    assert exc_info.value.status_code == 500
    assert "could not be persisted" in exc_info.value.detail.lower()
    assert "db down" not in exc_info.value.detail


def test_high_risk_prediction_alerts_signed_in_user_and_saves_status():
    user = MagicMock()
    user.id = uuid4()
    user.email = "signed-in@example.test"
    prediction_id = uuid4()
    request = PredictionRequest(
        transaction_id="synth-high-risk",
        features=_valid_features(),
    )
    db = MagicMock()
    persisted = {
        "prediction_id": prediction_id,
        "transaction_id": uuid4(),
        "fraud_probability": 0.75,
        "risk_level": "HIGH",
        "decision": "REVIEW",
        "expected_cost": 9.5,
        "model_version": "xgb-cost-v1",
        "explanation": [],
        "prediction_timestamp": datetime.now(timezone.utc),
        "probability_calibrated": False,
        "review_required": True,
        "risk_alert_triggered": True,
        "risk_alert_status": "NOT_REQUIRED",
    }
    notification = {
        "status": "SENT",
        "message": "High-risk alert emailed.",
    }

    with patch.object(
        prediction_service,
        "_evaluate_with_ml",
        return_value={"fraud_probability": 0.75, "risk_level": "HIGH"},
    ), patch.object(
        prediction_service,
        "persist_prediction",
        return_value=persisted,
    ), patch.object(
        prediction_service,
        "send_prediction_risk_alert",
        return_value=notification,
    ) as send_alert, patch.object(
        prediction_service,
        "update_prediction_risk_alert_status",
    ) as save_status:
        result = prediction_service.predict_and_persist(
            db=db,
            request=request,
            current_user=user,
        )

    send_alert.assert_called_once_with(
        recipient_email="signed-in@example.test",
        transaction_id=persisted["transaction_id"],
        transaction=request.features,
        fraud_probability=0.75,
        decision="REVIEW",
    )
    save_status.assert_called_once_with(
        db=db,
        prediction_id=prediction_id,
        user_id=user.id,
        status="SENT",
    )
    assert result["risk_alert_status"] == "SENT"
    assert result["risk_alert_message"] == "High-risk alert emailed."
