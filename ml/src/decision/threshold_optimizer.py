
from dataclasses import dataclass

import numpy as np

from ml.src.decision.cost_matrix import CostMatrix, Decision


@dataclass(frozen=True)
class ThresholdResult:
    approve_threshold: float
    block_threshold: float
    expected_cost: float
    decisions: dict[str, int]
    review_rate: float


def optimize_threshold(
    fraud_probabilities: np.ndarray,
    actual_labels: np.ndarray,
    cost_matrix: CostMatrix,
    thresholds: np.ndarray | None = None,
    max_review_rate: float | None = None,
) -> ThresholdResult:
    try:
        probabilities = np.asarray(fraud_probabilities, dtype=float)
        raw_labels = np.asarray(actual_labels)
    except (TypeError, ValueError) as exc:
        raise ValueError("Probabilities and labels must be numeric") from exc

    if probabilities.ndim != 1 or raw_labels.ndim != 1:
        raise ValueError("Probabilities and labels must be one-dimensional")

    if len(probabilities) != len(raw_labels):
        raise ValueError(
            "fraud_probabilities and actual_labels must have the same length"
        )

    if len(probabilities) == 0:
        raise ValueError("Input arrays must not be empty")

    if not np.all(np.isfinite(probabilities)):
        raise ValueError("fraud_probabilities must contain only finite values")

    if np.any((probabilities < 0) | (probabilities > 1)):
        raise ValueError("fraud_probabilities must be between 0 and 1")

    try:
        numeric_labels = raw_labels.astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError("actual_labels must contain only 0 or 1") from exc

    if not np.all(np.isfinite(numeric_labels)):
        raise ValueError("actual_labels must contain only finite values")

    if not np.all(np.isin(numeric_labels, [0, 1])):
        raise ValueError("actual_labels must contain only 0 or 1")

    labels = numeric_labels.astype(int)

    if thresholds is None:
        threshold_values = np.arange(0.01, 1.00, 0.01)
    else:
        try:
            threshold_values = np.asarray(thresholds, dtype=float)
        except (TypeError, ValueError) as exc:
            raise ValueError("thresholds must be numeric") from exc

    if threshold_values.ndim != 1 or threshold_values.size == 0:
        raise ValueError("thresholds must be a non-empty one-dimensional array")

    if not np.all(np.isfinite(threshold_values)):
        raise ValueError("thresholds must contain only finite values")

    if np.any((threshold_values <= 0) | (threshold_values >= 1)):
        raise ValueError("thresholds must be strictly between 0 and 1")

    threshold_values = np.unique(threshold_values)

    if max_review_rate is not None:
        if (
            not np.isfinite(max_review_rate)
            or not 0 <= max_review_rate <= 1
        ):
            raise ValueError("max_review_rate must be between 0 and 1")

    best_result = None
    n = len(probabilities)

    for approve_threshold in threshold_values:
        approve = probabilities < approve_threshold
        approve_count = int(np.sum(approve))
        approve_fraud = int(np.sum(approve & (labels == 1)))

        for block_threshold in threshold_values:
            if approve_threshold >= block_threshold:
                continue

            block = probabilities >= block_threshold
            block_count = int(np.sum(block))
            block_fraud = int(np.sum(block & (labels == 1)))
            block_genuine = int(np.sum(block & (labels == 0)))

            review = ~approve & ~block
            review_count = int(np.sum(review))
            review_fraud = int(np.sum(review & (labels == 1)))
            review_genuine = int(np.sum(review & (labels == 0)))

            review_rate = review_count / n

            if (
                max_review_rate is not None
                and review_rate > max_review_rate
            ):
                continue

            total_cost = (
                approve_fraud * cost_matrix.missed_fraud_cost
                + review_genuine * cost_matrix.review_cost
                + review_fraud
                * (
                    cost_matrix.review_cost
                    + cost_matrix.residual_risk_cost
                )
                + block_genuine * cost_matrix.block_friction_cost
                + block_fraud * cost_matrix.block_cost
            )

            result = ThresholdResult(
                approve_threshold=float(approve_threshold),
                block_threshold=float(block_threshold),
                expected_cost=float(total_cost),
                decisions={
                    Decision.APPROVE.value: approve_count,
                    Decision.REVIEW.value: review_count,
                    Decision.BLOCK.value: block_count,
                },
                review_rate=float(review_rate),
            )

            if (
                best_result is None
                or result.expected_cost < best_result.expected_cost
            ):
                best_result = result

    if best_result is None:
        raise ValueError(
            "No valid threshold policy satisfies the supplied constraints"
        )

    return best_result