import pytest

from ml.src.feedback.feedback_labels import FeedbackLabel
from ml.src.feedback.feedback_store import FeedbackStore


@pytest.fixture
def store(tmp_path):
    return FeedbackStore(tmp_path / "test_feedback.sqlite3")


def test_save_and_retrieve_feedback(store):
    features = {"Time": 100.0, "Amount": 250.5}

    feedback_id = store.save_feedback(
        transaction_id="TXN-001",
        operator_id="operator-01",
        label=FeedbackLabel.CONFIRMED_FRAUD,
        features=features,
    )

    records = store.get_feedback()

    assert feedback_id == 1
    assert len(records) == 1
    assert records[0]["transaction_id"] == "TXN-001"
    assert records[0]["operator_id"] == "operator-01"
    assert records[0]["label"] == "CONFIRMED_FRAUD"
    assert records[0]["features"] == features
    assert records[0]["submitted_at"]


def test_disputed_feedback_can_be_audited(store):
    store.save_feedback(
        transaction_id="TXN-002",
        operator_id="operator-02",
        label=FeedbackLabel.DISPUTED,
        features={"Amount": 100.0},
    )

    records = store.get_feedback()

    assert len(records) == 1
    assert records[0]["label"] == "DISPUTED"


def test_invalid_label_is_rejected(store):
    with pytest.raises(ValueError, match="Unsupported feedback label"):
        store.save_feedback(
            transaction_id="TXN-003",
            operator_id="operator-01",
            label="UNKNOWN",
            features={},
        )


@pytest.mark.parametrize(
    ("transaction_id", "operator_id"),
    [
        ("", "operator-01"),
        ("TXN-004", ""),
    ],
)
def test_empty_identifiers_are_rejected(store, transaction_id, operator_id):
    with pytest.raises(ValueError):
        store.save_feedback(
            transaction_id=transaction_id,
            operator_id=operator_id,
            label=FeedbackLabel.CONFIRMED_GENUINE,
            features={},
        )


def test_non_finite_features_are_rejected(store):
    with pytest.raises(ValueError, match="features must contain JSON-compatible finite values"):
        store.save_feedback(
            transaction_id="TXN-005",
            operator_id="operator-01",
            label=FeedbackLabel.CONFIRMED_FRAUD,
            features={"Amount": float("nan")},
        )

def test_get_feedback_for_transaction_returns_all_history(store):
    store.save_feedback(
        transaction_id="TXN-006",
        operator_id="operator-01",
        label=FeedbackLabel.CONFIRMED_FRAUD,
        features={"Amount": 200.0},
    )
    store.save_feedback(
        transaction_id="TXN-006",
        operator_id="operator-02",
        label=FeedbackLabel.CONFIRMED_GENUINE,
        features={"Amount": 200.0},
    )
    store.save_feedback(
        transaction_id="TXN-007",
        operator_id="operator-03",
        label=FeedbackLabel.CONFIRMED_GENUINE,
        features={"Amount": 50.0},
    )

    history = store.get_feedback_for_transaction(" TXN-006 ")

    assert len(history) == 2
    assert [record["operator_id"] for record in history] == [
        "operator-01",
        "operator-02",
    ]
    assert [record["label"] for record in history] == [
        "CONFIRMED_FRAUD",
        "CONFIRMED_GENUINE",
    ]
    assert all(record["submitted_at"] for record in history)


def test_get_feedback_for_unknown_transaction_returns_empty_list(store):
    assert store.get_feedback_for_transaction("TXN-MISSING") == []


def test_get_feedback_for_transaction_rejects_empty_id(store):
    with pytest.raises(
        ValueError,
        match="transaction_id must not be empty",
    ):
        store.get_feedback_for_transaction("   ")
def test_transaction_history_matches_full_feedback_listing(store):
    store.save_feedback(
        transaction_id="TXN-010",
        operator_id="operator-01",
        label=FeedbackLabel.CONFIRMED_FRAUD,
        features={"Amount": 200.0},
    )
    store.save_feedback(
        transaction_id="TXN-010",
        operator_id="operator-02",
        label=FeedbackLabel.DISPUTED,
        features={"Amount": 200.0},
    )
    store.save_feedback(
        transaction_id="TXN-011",
        operator_id="operator-03",
        label=FeedbackLabel.CONFIRMED_GENUINE,
        features={"Amount": 50.0},
    )

    all_feedback = store.get_feedback()
    transaction_history = store.get_feedback_for_transaction("TXN-010")

    expected_history = [
        record
        for record in all_feedback
        if record["transaction_id"] == "TXN-010"
    ]

    assert transaction_history == expected_history
    assert len(transaction_history) == 2


def test_repeated_submissions_are_preserved_in_audit_history(store):
    for _ in range(3):
        store.save_feedback(
            transaction_id="TXN-012",
            operator_id="operator-01",
            label=FeedbackLabel.CONFIRMED_FRAUD,
            features={"Amount": 300.0},
        )

    history = store.get_feedback_for_transaction("TXN-012")

    assert len(history) == 3
    assert all(
        record["label"] == "CONFIRMED_FRAUD"
        for record in history
    )
