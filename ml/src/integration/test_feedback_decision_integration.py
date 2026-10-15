import numpy as np

from ml.src.decision import decision_engine
from ml.src.decision.cost_matrix import CostMatrix, Decision
from ml.src.decision.review_band import ReviewBand
from ml.src.decision.review_queue import build_review_queue
from ml.src.feedback.feedback_labels import FeedbackLabel
from ml.src.feedback.feedback_store import FeedbackStore
from ml.src.feedback.feedback_training_pipeline import (
    build_approved_training_data_from_store,
)
from ml.src.feedback.training_approval import TrainingApproval


def test_prediction_review_feedback_approval_flow(tmp_path, monkeypatch):
    transaction = {
        "Time": 100.0,
        **{f"V{i}": 0.0 for i in range(1, 29)},
        "Amount": 125.0,
    }

    monkeypatch.setattr(
        decision_engine,
        "predict_fraud",
        lambda features: 0.45,
    )
    monkeypatch.setattr(
        decision_engine,
        "explain_transaction",
        lambda transaction, top_k: {"top_features": []},
    )

    costs = CostMatrix(
        review_cost=5.0,
        block_friction_cost=100.0,
        missed_fraud_cost=100.0,
        residual_risk_cost=20.0,
        block_cost=2.0,
    )

    result = decision_engine.evaluate_transaction(
        transaction,
        costs,
    )

    assert result["fraud_probability"] == 0.45
    assert result["decision"] == Decision.REVIEW.value

    queue = build_review_queue(
        np.array([result["fraud_probability"]]),
        ReviewBand(lower=0.20, upper=0.80),
    )

    assert queue.selected_indices == [0]
    assert queue.total_candidates == 1

    store = FeedbackStore(tmp_path / "integration_feedback.sqlite")
    store.save_feedback(
        transaction_id="integration-tx-001",
        operator_id="test-operator",
        label=FeedbackLabel.CONFIRMED_FRAUD,
        features=transaction,
    )

    saved_feedback = store.get_feedback_for_transaction(
        "integration-tx-001"
    )
    assert len(saved_feedback) == 1
    assert saved_feedback[0]["operator_id"] == "test-operator"

    no_approval = TrainingApproval(
        approved_transaction_ids=frozenset()
    )
    assert build_approved_training_data_from_store(
        store, no_approval
    ) == []

    approved = TrainingApproval(
        approved_transaction_ids=frozenset({"integration-tx-001"})
    )
    training_data = build_approved_training_data_from_store(
        store, approved
    )

    assert len(training_data) == 1
    assert training_data[0].transaction_id == "integration-tx-001"
    assert training_data[0].label == 1
    assert training_data[0].features["Amount"] == 125.0
