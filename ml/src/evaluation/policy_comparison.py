
from pathlib import Path

import numpy as np
import pandas as pd

from ml.src.decision.cost_matrix import CostMatrix


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
    / "policy_comparison_results.csv"
)

COST_MATRIX = CostMatrix(
    review_cost=2.0,
    block_friction_cost=5.0,
    missed_fraud_cost=100.0,
    residual_risk_cost=10.0,
    block_cost=20.0,
)


def evaluate_policy(
    probabilities,
    labels,
    approve_threshold,
    block_threshold,
    policy_type,
):
    probabilities = np.asarray(probabilities, dtype=float)
    labels = np.asarray(labels)

    if probabilities.ndim != 1 or labels.ndim != 1:
        raise ValueError("Probabilities and labels must be one-dimensional")

    if len(probabilities) == 0 or len(probabilities) != len(labels):
        raise ValueError("Probabilities and labels must have equal nonzero length")

    if not np.isfinite(probabilities).all():
        raise ValueError("Probabilities must be finite")

    if ((probabilities < 0) | (probabilities > 1)).any():
        raise ValueError("Probabilities must be between 0 and 1")

    if not np.isin(labels, [0, 1]).all():
        raise ValueError("Labels must contain only 0 and 1")

    if not 0 <= approve_threshold <= 1:
        raise ValueError("approve_threshold must be between 0 and 1")

    if not 0 <= block_threshold <= 1:
        raise ValueError("block_threshold must be between 0 and 1")

    if policy_type == "binary":
        if approve_threshold != block_threshold:
            raise ValueError("Binary policy requires equal thresholds")

        approve = probabilities < approve_threshold
        block = ~approve
        review = np.zeros(len(probabilities), dtype=bool)

    elif policy_type == "three_way":
        if approve_threshold >= block_threshold:
            raise ValueError(
                "Three-way policy requires approve_threshold "
                "to be lower than block_threshold"
            )

        approve = probabilities < approve_threshold
        block = probabilities >= block_threshold
        review = ~approve & ~block

    else:
        raise ValueError(f"Unsupported policy type: {policy_type}")

    approve_fraud = int((approve & (labels == 1)).sum())
    review_genuine = int((review & (labels == 0)).sum())
    review_fraud = int((review & (labels == 1)).sum())
    block_genuine = int((block & (labels == 0)).sum())
    block_fraud = int((block & (labels == 1)).sum())

    expected_cost = (
        approve_fraud * COST_MATRIX.missed_fraud_cost
        + review_genuine * COST_MATRIX.review_cost
        + review_fraud
        * (
            COST_MATRIX.review_cost
            + COST_MATRIX.residual_risk_cost
        )
        + block_genuine * COST_MATRIX.block_friction_cost
        + block_fraud * COST_MATRIX.block_cost
    )

    total = len(labels)

    return {
        "approve_threshold": approve_threshold,
        "block_threshold": block_threshold,
        "expected_cost": float(expected_cost),
        "approve_count": int(approve.sum()),
        "review_count": int(review.sum()),
        "block_count": int(block.sum()),
        "review_rate": float(review.sum() / total),
    }


def main():
    print("=" * 70)
    print("POLICY COMPARISON")
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
            f"Missing validation columns: {sorted(missing_columns)}"
        )

    probabilities = df["xgboost_probability"].to_numpy()
    labels = df["actual_class"].to_numpy()

    policies = [
        {
            "policy": "baseline_0.50",
            "approve_threshold": 0.50,
            "block_threshold": 0.50,
            "policy_type": "binary",
        },
        {
            "policy": "optimized_three_way",
            "approve_threshold": 0.02,
            "block_threshold": 0.98,
            "policy_type": "three_way",
        },
    ]

    results = []

    for policy in policies:
        result = evaluate_policy(
            probabilities=probabilities,
            labels=labels,
            approve_threshold=policy["approve_threshold"],
            block_threshold=policy["block_threshold"],
            policy_type=policy["policy_type"],
        )

        result["policy"] = policy["policy"]
        result["policy_type"] = policy["policy_type"]
        results.append(result)

    results_df = pd.DataFrame(results)

    baseline_cost = results_df.loc[
        results_df["policy"] == "baseline_0.50",
        "expected_cost",
    ].iloc[0]

    optimized_cost = results_df.loc[
        results_df["policy"] == "optimized_three_way",
        "expected_cost",
    ].iloc[0]

    cost_reduction = baseline_cost - optimized_cost

    cost_reduction_percentage = (
        cost_reduction / baseline_cost * 100
        if baseline_cost > 0
        else 0.0
    )

    results_df["cost_reduction_vs_baseline"] = 0.0
    results_df["cost_reduction_percentage_vs_baseline"] = 0.0

    optimized_mask = results_df["policy"] == "optimized_three_way"

    results_df.loc[
        optimized_mask,
        "cost_reduction_vs_baseline",
    ] = cost_reduction

    results_df.loc[
        optimized_mask,
        "cost_reduction_percentage_vs_baseline",
    ] = cost_reduction_percentage

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(OUTPUT_PATH, index=False)

    print("\nResults:")
    print(results_df.to_string(index=False))

    print("\nCost reduction under the configured cost assumptions:")
    print(f"Absolute: {cost_reduction:.2f}")
    print(f"Percentage: {cost_reduction_percentage:.2f}%")

    print("\nResults saved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
