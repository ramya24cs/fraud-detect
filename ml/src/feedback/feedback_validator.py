from dataclasses import dataclass

from ml.src.feedback.feedback_labels import FeedbackLabel


@dataclass(frozen=True)
class FeedbackValidationResult:
    valid: bool
    usable_for_training: bool
    reason: str


def validate_feedback(label: FeedbackLabel) -> FeedbackValidationResult:
    if not isinstance(label, FeedbackLabel):
        return FeedbackValidationResult(
            valid=False,
            usable_for_training=False,
            reason="Invalid feedback label",
        )

    if label == FeedbackLabel.CONFIRMED_FRAUD:
        return FeedbackValidationResult(
            valid=True,
            usable_for_training=True,
            reason="Confirmed fraud label is valid for controlled training data",
        )

    if label == FeedbackLabel.CONFIRMED_GENUINE:
        return FeedbackValidationResult(
            valid=True,
            usable_for_training=True,
            reason="Confirmed genuine label is valid for controlled training data",
        )

    if label == FeedbackLabel.DISPUTED:
        return FeedbackValidationResult(
            valid=True,
            usable_for_training=False,
            reason="Disputed feedback must not directly enter training data",
        )

    if label == FeedbackLabel.INCONCLUSIVE:
        return FeedbackValidationResult(
            valid=True,
            usable_for_training=False,
            reason="Inconclusive feedback must not directly enter training data",
        )

    return FeedbackValidationResult(
        valid=False,
        usable_for_training=False,
        reason="Unsupported feedback label",
    )