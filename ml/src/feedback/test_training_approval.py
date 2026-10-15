from ml.src.feedback.training_approval import (
    TrainingApproval,
    filter_approved_feedback,
)


def make_record(transaction_id, label="CONFIRMED_FRAUD"):
    return {
        "transaction_id": transaction_id,
        "label": label,
        "features": {"Amount": 100.0},
    }


def test_only_approved_transactions_are_returned():
    records = [make_record("txn-001"), make_record("txn-002")]
    approval = TrainingApproval(
        approved_transaction_ids=frozenset({"txn-001"})
    )

    result = filter_approved_feedback(records, approval)

    assert [record["transaction_id"] for record in result] == ["txn-001"]


def test_unapproved_feedback_is_excluded():
    records = [make_record("txn-001")]
    approval = TrainingApproval(approved_transaction_ids=frozenset())

    assert filter_approved_feedback(records, approval) == []


def test_approval_filter_preserves_duplicates_for_conflict_detection():
    records = [
        make_record("txn-001", "CONFIRMED_FRAUD"),
        make_record("txn-001", "CONFIRMED_GENUINE"),
    ]
    approval = TrainingApproval(
        approved_transaction_ids=frozenset({"txn-001"})
    )

    result = filter_approved_feedback(records, approval)

    assert len(result) == 2
    assert {record["label"] for record in result} == {
        "CONFIRMED_FRAUD",
        "CONFIRMED_GENUINE",
    }


def test_empty_and_malformed_records_are_ignored():
    records = [None, {}, make_record("   "), make_record("txn-001")]
    approval = TrainingApproval(
        approved_transaction_ids=frozenset({"txn-001"})
    )

    result = filter_approved_feedback(records, approval)

    assert len(result) == 1
    assert result[0]["transaction_id"] == "txn-001"


def test_transaction_id_is_normalized_for_matching():
    records = [make_record(" txn-001 ")]
    approval = TrainingApproval(
        approved_transaction_ids=frozenset({"txn-001"})
    )

    result = filter_approved_feedback(records, approval)

    assert len(result) == 1
    assert result[0]["transaction_id"] == " txn-001 "


def test_approved_transaction_ids_are_normalized_for_matching():
    records = [make_record("txn-001")]
    approval = TrainingApproval(
        approved_transaction_ids=frozenset({" txn-001 "})
    )

    result = filter_approved_feedback(records, approval)

    assert len(result) == 1
    assert result[0]["transaction_id"] == "txn-001"