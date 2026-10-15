
from pathlib import Path

import numpy as np
import pandas as pd

from ml.src.decision.cost_matrix import CostMatrix, Decision
from ml.src.decision.review_band import ReviewBand
from ml.src.decision.review_queue import build_review_queue


PROJECT_ROOT = Path(__file__).resolve().parents[3]

INPUT_PATH = (
    PROJECT_ROOT
    / "ml"
    / "reports"
    / "validation_predictions.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "ml"
    / "reports"
    / "review_capacity_results.csv"
)

REVIEW_LOWER = 0.02
REVIEW_UPPER = 0.98
RISK_THRESHOLD = 0.50

CAPACITIES = [5, 10, 25, 50, None]

COST_MATRIX = CostMatrix(
    review_cost=2.0,
    block_friction_cost=5.0,
    missed_fraud_cost=100.0,
    residual_risk_cost=10.0,
    block_cost=20.0,
)


def calculate_cost(decisions, labels):
    total_cost = 0.0

    for decision, label in zip(decisions, labels):
        if decision == Decision.APPROVE.value and label == 1:
            total_cost += COST_MATRIX.missed_fraud_cost

        elif decision == Decision.REVIEW.value:
            if label == 0:
                total_cost += COST_MATRIX.review_cost
            else:
                total_cost += (
                    COST_MATRIX.review_cost
                    + COST_MATRIX.residual_risk_cost
                )

        elif decision == Decision.BLOCK.value:
            if label == 0:
                total_cost += COST_MATRIX.block_friction_cost
            else:
                total_cost += COST_MATRIX.block_cost

    return float(total_cost)


def run_experiment():
    print("=" * 70)
    print("REVIEW CAPACITY AND OVERFLOW EXPERIMENT")
    print("=" * 70)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Validation predictions not found: {INPUT_PATH}"
        )

    df = pd.read_csv(INPUT_PATH)

    required_columns = {"actual_class", "xgboost_probability"}
    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    probabilities = df["xgboost_probability"].to_numpy(dtype=float)
    labels = df["actual_class"].to_numpy()

    if len(probabilities) == 0:
        raise ValueError("Validation data must not be empty")

    if not np.isfinite(probabilities).all():
        raise ValueError("Probabilities must be finite")

    if ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError("Probabilities must be between 0 and 1")

    if not np.isin(labels, [0, 1]).all():
        raise ValueError("Labels must contain only 0 and 1")

    strategies = ["APPROVE", "BLOCK", "RISK_THRESHOLD"]
    results = []

    for capacity in CAPACITIES:
        band = ReviewBand(
            lower=REVIEW_LOWER,
            upper=REVIEW_UPPER,
            capacity=capacity,
        )

        queue = build_review_queue(
            fraud_probabilities=probabilities,
            review_band=band,
        )

        selected = np.zeros(len(probabilities), dtype=bool)
        selected[queue.selected_indices] = True

        in_band = (
            (probabilities >= REVIEW_LOWER)
            & (probabilities < REVIEW_UPPER)
        )

        overflow = in_band & ~selected

        for strategy in strategies:
            decisions = np.full(
                len(probabilities),
                Decision.APPROVE.value,
                dtype=object,
            )

            decisions[probabilities >= REVIEW_UPPER] = (
                Decision.BLOCK.value
            )
            decisions[selected] = Decision.REVIEW.value

            if strategy == "APPROVE":
                decisions[overflow] = Decision.APPROVE.value

            elif strategy == "BLOCK":
                decisions[overflow] = Decision.BLOCK.value

            else:
                decisions[
                    overflow & (probabilities >= RISK_THRESHOLD)
                ] = Decision.BLOCK.value

                decisions[
                    overflow & (probabilities < RISK_THRESHOLD)
                ] = Decision.APPROVE.value

            total_cost = calculate_cost(decisions, labels)

            fraud_count = int((labels == 1).sum())
            selected_frauds = int(((labels == 1) & selected).sum())

            review_count = int(
                (decisions == Decision.REVIEW.value).sum()
            )
            approve_count = int(
                (decisions == Decision.APPROVE.value).sum()
            )
            block_count = int(
                (decisions == Decision.BLOCK.value).sum()
            )

            results.append(
                {
                    "capacity": (
                        "unlimited" if capacity is None else capacity
                    ),
                    "overflow_strategy": strategy,
                    "total_candidates": queue.total_candidates,
                    "review_count": review_count,
                    "overflow_count": int(overflow.sum()),
                    "approve_count": approve_count,
                    "block_count": block_count,
                    "detected_frauds_in_review": selected_frauds,
                    "review_precision": (
                        selected_frauds / review_count
                        if review_count
                        else 0.0
                    ),
                    "review_recall": (
                        selected_frauds / fraud_count
                        if fraud_count
                        else 0.0
                    ),
                    "expected_cost": total_cost,
                    "review_rate": review_count / len(probabilities),
                }
            )

    results_df = pd.DataFrame(results)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(OUTPUT_PATH, index=False)

    print("\nResults:")
    print(results_df.to_string(index=False))

    print("\nResults saved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    run_experiment()
