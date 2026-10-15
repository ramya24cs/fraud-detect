import pytest

from ml.src.feedback.feedback_labels import FeedbackLabel
from ml.src.feedback.feedback_store import FeedbackStore
from ml.src.feedback.retraining_guard import prepare_retraining
from ml.src.feedback.training_approval import TrainingApproval
from ml.src.feedback.training_data_builder import FEATURES


def make_features():
    return {
        feature: float(index)
        for index, feature in enumerate(FEATURES)
    }


def test_retraining_requires_approval(tmp_path):
    store = FeedbackStore(tmp_path / "feedback.sqlite3")

    with pytest.raises(PermissionError):
        prepare_retraining(store, None)


def test_retraining_refuses_empty_approval(tmp_path):
    store = FeedbackStore(tmp_path / "feedback.sqlite3")

    store.save_feedback(
        "txn-001",
        "operator-1",
        FeedbackLabel.CONFIRMED_FRAUD,
        make_features(),
    )

    approval = TrainingApproval(frozenset())

    with pytest.raises(ValueError, match="no valid approved"):
        prepare_retraining(store, approval)


def test_retraining_returns_only_approved_examples(tmp_path):
    store = FeedbackStore(tmp_path / "feedback.sqlite3")

    store.save_feedback(
        "txn-approved",
        "operator-1",
        FeedbackLabel.CONFIRMED_FRAUD,
        make_features(),
    )
    store.save_feedback(
        "txn-unapproved",
        "operator-2",
        FeedbackLabel.CONFIRMED_GENUINE,
        make_features(),
    )

    approval = TrainingApproval(
        frozenset({"txn-approved"})
    )

    plan = prepare_retraining(store, approval)

    assert len(plan.examples) == 1
    assert plan.transaction_ids == ("txn-approved",)
    assert plan.examples[0].label == 1


def test_retraining_rejects_disputed_feedback(tmp_path):
    store = FeedbackStore(tmp_path / "feedback.sqlite3")

    store.save_feedback(
        "txn-002",
        "operator-1",
        FeedbackLabel.DISPUTED,
        make_features(),
    )

    approval = TrainingApproval(
        frozenset({"txn-002"})
    )

    with pytest.raises(ValueError, match="no valid approved"):
        prepare_retraining(store, approval)
