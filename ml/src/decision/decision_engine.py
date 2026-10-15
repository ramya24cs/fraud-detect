
import math

from ml.src.decision.cost_matrix import CostMatrix, Decision
from ml.src.explainability.shap_explainer import explain_transaction
from ml.src.models.inference import predict_fraud


def evaluate_transaction(
    transaction: dict,
    cost_matrix: CostMatrix,
    top_k: int = 5,
) -> dict:
    required_features = [
        "Time",
        *[f"V{i}" for i in range(1, 29)],
        "Amount",
    ]

    if not isinstance(transaction, dict):
        raise ValueError("transaction must be a dictionary")

    missing_features = [
        feature
        for feature in required_features
        if feature not in transaction
    ]

    if missing_features:
        raise ValueError(
            f"Missing transaction features: {missing_features}"
        )

    if not isinstance(top_k, int) or isinstance(top_k, bool) or top_k < 1:
        raise ValueError("top_k must be a positive integer")

    validated_transaction = transaction.copy()

    for feature in required_features:
        value = validated_transaction[feature]

        if isinstance(value, bool):
            raise ValueError(f"{feature} must be a finite number")

        try:
            numeric_value = float(value)
        except (TypeError, ValueError):
            raise ValueError(
                f"{feature} must be a finite number"
            ) from None

        if not math.isfinite(numeric_value):
            raise ValueError(f"{feature} must be a finite number")

        validated_transaction[feature] = numeric_value

    fraud_probability = predict_fraud(validated_transaction)

    decision = cost_matrix.select_decision(fraud_probability)

    expected_cost = cost_matrix.expected_cost(
        fraud_probability=fraud_probability,
        decision=decision,
    )

    explanation = explain_transaction(
        transaction=validated_transaction,
        top_k=top_k,
    )

    return {
        "fraud_probability": fraud_probability,
        "decision": decision.value,
        "expected_cost": expected_cost,
        "model_version": "xgb-cost-v1",
        "explanation": explanation,
    }