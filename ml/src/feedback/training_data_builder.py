import math
from dataclasses import dataclass

from ml.src.feedback.feedback_labels import FeedbackLabel
from ml.src.feedback.feedback_validator import validate_feedback


FEATURES = [
    "Time",
    *[f"V{i}" for i in range(1, 29)],
    "Amount",
]


@dataclass(frozen=True)
class TrainingExample:
    transaction_id: str
    features: dict[str, float]
    label: int


def build_training_data(
    feedback_records: list[dict],
) -> list[TrainingExample]:
    valid_records = {}

    for record in feedback_records:
        if not isinstance(record, dict):
            continue

        transaction_id = record.get("transaction_id")

        if transaction_id is None:
            continue

        normalized_transaction_id = str(transaction_id).strip()

        if not normalized_transaction_id:
            continue

        try:
            feedback_label = FeedbackLabel(record.get("label"))
        except (ValueError, TypeError):
            continue

        validation = validate_feedback(feedback_label)

        if not validation.valid or not validation.usable_for_training:
            continue

        features = record.get("features")

        if not isinstance(features, dict):
            continue

        if not all(feature in features for feature in FEATURES):
            continue

        validated_features = {}
        valid_features = True

        for feature in FEATURES:
            value = features[feature]

            if isinstance(value, bool):
                valid_features = False
                break

            try:
                numeric_value = float(value)
            except (TypeError, ValueError, OverflowError):
                valid_features = False
                break

            if not math.isfinite(numeric_value):
                valid_features = False
                break

            validated_features[feature] = numeric_value

        if not valid_features:
            continue

        training_label = (
            1
            if feedback_label == FeedbackLabel.CONFIRMED_FRAUD
            else 0
        )

        if normalized_transaction_id not in valid_records:
            valid_records[normalized_transaction_id] = {
                "label": training_label,
                "features": validated_features,
                "conflict": False,
            }
        elif valid_records[normalized_transaction_id]["label"] != training_label:
            valid_records[normalized_transaction_id]["conflict"] = True

    training_data = []

    for transaction_id, record in valid_records.items():
        if record["conflict"]:
            continue

        training_data.append(
            TrainingExample(
                transaction_id=transaction_id,
                features=record["features"],
                label=record["label"],
            )
        )

    return training_data
