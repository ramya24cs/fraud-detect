from dataclasses import dataclass
from typing import Protocol

from ml.src.feedback.feedback_training_pipeline import (
    build_approved_training_data_from_store,
)
from ml.src.feedback.training_approval import TrainingApproval
from ml.src.feedback.training_data_builder import TrainingExample


class FeedbackSource(Protocol):
    def get_feedback(self) -> list[dict]:
        ...


@dataclass(frozen=True)
class RetrainingPlan:
    transaction_ids: tuple[str, ...]
    examples: tuple[TrainingExample, ...]


def prepare_retraining(
    feedback_source: FeedbackSource,
    approval: TrainingApproval | None,
) -> RetrainingPlan:
    if approval is None:
        raise PermissionError(
            "Explicit training approval is required."
        )

    examples = build_approved_training_data_from_store(
        feedback_source,
        approval,
    )

    if not examples:
        raise ValueError(
            "Retraining refused: no valid approved training examples."
        )

    transaction_ids = tuple(
        example.transaction_id for example in examples
    )

    return RetrainingPlan(
        transaction_ids=transaction_ids,
        examples=tuple(examples),
    )
