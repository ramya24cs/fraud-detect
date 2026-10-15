"""Focused inference/pipeline tests using synthetic transactions."""

from pathlib import Path

import joblib
import pytest

from ml.src.decision.decision_engine import evaluate_transaction
from ml.src.models.inference import predict_fraud


MODEL_PATH = Path("ml/models/xgboost_baseline.joblib")
PREPROCESSOR_PATH = Path("ml/models/preprocessor.joblib")


def synthetic_transaction(**overrides):
    tx = {
        "Time": 1000.0,
        **{f"V{i}": 0.1 for i in range(1, 29)},
        "Amount": 150.0,
    }
    tx.update(overrides)
    return tx


def test_model_artifacts_exist_and_load():
    assert MODEL_PATH.exists()
    assert PREPROCESSOR_PATH.exists()
    model = joblib.load(MODEL_PATH)
    scaler = joblib.load(PREPROCESSOR_PATH)
    assert model is not None
    assert scaler is not None


def test_predict_fraud_returns_probability_in_unit_interval():
    probability = predict_fraud(synthetic_transaction())
    assert isinstance(probability, float)
    assert 0.0 <= probability <= 1.0


def test_predict_fraud_rejects_missing_features():
    tx = synthetic_transaction()
    del tx["Amount"]
    with pytest.raises(ValueError, match="Missing required features"):
        predict_fraud(tx)


def test_predict_fraud_rejects_non_dictionary():
    with pytest.raises(TypeError, match="dictionary"):
        predict_fraud(["not", "a", "dict"])  # type: ignore[arg-type]


def test_predict_fraud_rejects_non_finite_values():
    with pytest.raises(ValueError, match="finite"):
        predict_fraud(synthetic_transaction(Amount=float("nan")))


def test_evaluate_transaction_action_uses_cost_matrix_with_real_model():
    # This is an explicitly synthetic model-input fixture, not a transaction
    # that can be constructed from ordinary form fields.
    from ml.src.decision.defaults import (
        approved_cost_matrix,
    )

    tx = {
        "Time": 50000.0,
        "Amount": 500.0,
        **{f"V{i}": 0.0 for i in range(1, 29)},
    }
    tx["V14"] = -2.0
    tx["V12"] = -1.4
    tx["V10"] = -1.0
    tx["V17"] = -0.8
    tx["V4"] = 1.0

    cost_matrix = approved_cost_matrix()

    probability = predict_fraud(tx)
    result = evaluate_transaction(tx, cost_matrix, top_k=3)

    assert result["decision"] == cost_matrix.select_decision(probability).value
    assert result["fraud_probability"] == probability
    assert result["expected_cost"] >= 0
    assert isinstance(result["explanation"], list)
    assert len(result["explanation"]) <= 3


def test_evaluate_transaction_action_uses_cost_matrix_for_synthetic_input():
    from ml.src.decision.defaults import (
        approved_cost_matrix,
    )

    cost_matrix = approved_cost_matrix()
    result = evaluate_transaction(
        synthetic_transaction(),
        cost_matrix,
        top_k=2,
    )
    assert result["decision"] == cost_matrix.select_decision(
        result["fraud_probability"]
    ).value
