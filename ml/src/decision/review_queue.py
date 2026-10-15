from dataclasses import dataclass

import numpy as np

from ml.src.decision.review_band import ReviewBand


@dataclass(frozen=True)
class ReviewQueueResult:
    selected_indices: list[int]
    total_candidates: int
    capacity: int | None


def build_review_queue(
    fraud_probabilities: np.ndarray,
    review_band: ReviewBand,
) -> ReviewQueueResult:
    probabilities = np.asarray(
        fraud_probabilities,
        dtype=float,
    )

    if np.any((probabilities < 0) | (probabilities > 1)):
        raise ValueError(
            "fraud_probabilities must be between 0 and 1"
        )

    candidate_indices = [
        index
        for index, probability in enumerate(probabilities)
        if review_band.contains(float(probability))
    ]

    if review_band.capacity is None:
        selected_indices = candidate_indices
    else:
        selected_indices = sorted(
            candidate_indices,
            key=lambda index: probabilities[index],
            reverse=True,
        )[:review_band.capacity]

    return ReviewQueueResult(
        selected_indices=selected_indices,
        total_candidates=len(candidate_indices),
        capacity=review_band.capacity,
    )