from pathlib import Path

import pandas as pd

from ml.src.decision.cost_matrix import CostMatrix
from ml.src.decision.threshold_optimizer import optimize_threshold


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
    / "cost_sensitivity_results.csv"
)


# These are research scenarios, not final production costs.
COST_SCENARIOS = [
    {
        "scenario": "baseline_reference",
        "review_cost": 2.0,
        "block_friction_cost": 5.0,
        "missed_fraud_cost": 100.0,
        "residual_risk_cost": 10.0,
        "block_cost": 20.0,
    },
    {
        "scenario": "higher_fraud_loss",
        "review_cost": 2.0,
        "block_friction_cost": 5.0,
        "missed_fraud_cost": 200.0,
        "residual_risk_cost": 10.0,
        "block_cost": 20.0,
    },
    {
        "scenario": "high_review_cost",
        "review_cost": 10.0,
        "block_friction_cost": 5.0,
        "missed_fraud_cost": 100.0,
        "residual_risk_cost": 10.0,
        "block_cost": 20.0,
    },
]


THRESHOLDS = [
    i / 100
    for i in range(1, 100)
]


def run_cost_sensitivity():
    print("=" * 70)
    print("COST-SENSITIVITY EXPERIMENT")
    print("=" * 70)

    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Validation predictions not found: {INPUT_PATH}"
        )

    df = pd.read_csv(INPUT_PATH)

    required_columns = {
        "actual_class",
        "xgboost_probability",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    probabilities = df["xgboost_probability"].to_numpy()
    actual_labels = df["actual_class"].to_numpy()

    results = []

    for scenario in COST_SCENARIOS:
        cost_matrix = CostMatrix(
            review_cost=scenario["review_cost"],
            block_friction_cost=scenario["block_friction_cost"],
            missed_fraud_cost=scenario["missed_fraud_cost"],
            residual_risk_cost=scenario["residual_risk_cost"],
            block_cost=scenario["block_cost"],
        )

        result = optimize_threshold(
            fraud_probabilities=probabilities,
            actual_labels=actual_labels,
            cost_matrix=cost_matrix,
            thresholds=THRESHOLDS,
        )

        results.append(
            {
                "scenario": scenario["scenario"],
                "review_cost": scenario["review_cost"],
                "block_friction_cost": scenario["block_friction_cost"],
                "missed_fraud_cost": scenario["missed_fraud_cost"],
                "residual_risk_cost": scenario["residual_risk_cost"],
                "block_cost": scenario["block_cost"],
                "approve_threshold": result.approve_threshold,
                "block_threshold": result.block_threshold,
                "expected_cost": result.expected_cost,
                "approve_count": result.decisions["APPROVE"],
                "review_count": result.decisions["REVIEW"],
                "block_count": result.decisions["BLOCK"],
                "review_rate": result.review_rate,
            }
        )

    results_df = pd.DataFrame(results)

    OUTPUT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    results_df.to_csv(
        OUTPUT_PATH,
        index=False,
    )

    print("\nResults:")
    print(results_df.to_string(index=False))

    print("\nResults saved to:")
    print(OUTPUT_PATH)


if __name__ == "__main__":
    run_cost_sensitivity()