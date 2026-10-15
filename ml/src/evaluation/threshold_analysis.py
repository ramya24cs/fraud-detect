import pandas as pd
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

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
    / "threshold_analysis_xgboost.csv"
)


# ============================================================
# COST CONFIGURATION
# ============================================================

FALSE_POSITIVE_COST = 5
FALSE_NEGATIVE_COST = 100

# Thresholds from 0.01 to 0.99
THRESHOLDS = [
    i / 100
    for i in range(1, 100)
]


# ============================================================
# LOAD VALIDATION PREDICTIONS
# ============================================================

print("=" * 70)
print("COST-SENSITIVE THRESHOLD ANALYSIS")
print("=" * 70)

df = pd.read_csv(INPUT_PATH)

y_true = df["actual_class"]
probabilities = df["xgboost_probability"]

print("\nValidation data:")
print(f"Rows: {len(df)}")

print("\nCosts:")
print(f"False Positive Cost : {FALSE_POSITIVE_COST}")
print(f"False Negative Cost : {FALSE_NEGATIVE_COST}")


# ============================================================
# THRESHOLD EVALUATION FUNCTION
# ============================================================

def evaluate_threshold(
    y_true,
    probabilities,
    threshold,
    fp_cost,
    fn_cost,
):
    predictions = (
        probabilities >= threshold
    ).astype(int)

    true_negative = (
        (y_true == 0) & (predictions == 0)
    ).sum()

    false_positive = (
        (y_true == 0) & (predictions == 1)
    ).sum()

    false_negative = (
        (y_true == 1) & (predictions == 0)
    ).sum()

    true_positive = (
        (y_true == 1) & (predictions == 1)
    ).sum()

    expected_cost = (
        false_positive * fp_cost
        + false_negative * fn_cost
    )

    total_transactions = len(y_true)

    review_rate = (
        (false_positive + true_positive)
        / total_transactions
    )

    precision = (
        true_positive
        / (true_positive + false_positive)
        if (true_positive + false_positive) > 0
        else 0.0
    )

    recall = (
        true_positive
        / (true_positive + false_negative)
        if (true_positive + false_negative) > 0
        else 0.0
    )

    f1 = (
        2 * precision * recall
        / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )

    return {
        "threshold": threshold,
        "TN": true_negative,
        "FP": false_positive,
        "FN": false_negative,
        "TP": true_positive,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "expected_cost": expected_cost,
        "review_rate": review_rate,
    }


# ============================================================
# RUN THRESHOLD EXPERIMENT
# ============================================================

results = []

for threshold in THRESHOLDS:

    result = evaluate_threshold(
        y_true=y_true,
        probabilities=probabilities,
        threshold=threshold,
        fp_cost=FALSE_POSITIVE_COST,
        fn_cost=FALSE_NEGATIVE_COST,
    )

    results.append(result)


results_df = pd.DataFrame(results)


# ============================================================
# FIND OPTIMAL THRESHOLD
# ============================================================

optimal_row = results_df.loc[
    results_df["expected_cost"].idxmin()
]

optimal_threshold = optimal_row["threshold"]
minimum_cost = optimal_row["expected_cost"]


# ============================================================
# BASELINE 0.5 RESULT
# ============================================================

baseline_row = results_df[
    results_df["threshold"] == 0.50
].iloc[0]

baseline_cost = baseline_row["expected_cost"]


# ============================================================
# COST REDUCTION
# ============================================================

cost_reduction = (
    baseline_cost - minimum_cost
)

if baseline_cost > 0:
    cost_reduction_percentage = (
        cost_reduction / baseline_cost
    ) * 100
else:
    cost_reduction_percentage = 0.0


# ============================================================
# SAVE RESULTS
# ============================================================

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

results_df.to_csv(
    OUTPUT_PATH,
    index=False,
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 70)
print("BASELINE THRESHOLD = 0.50")
print("=" * 70)

print(
    f"FP          : {int(baseline_row['FP'])}"
)

print(
    f"FN          : {int(baseline_row['FN'])}"
)

print(
    f"TP          : {int(baseline_row['TP'])}"
)

print(
    f"TN          : {int(baseline_row['TN'])}"
)

print(
    f"Expected Cost : {baseline_cost:.2f}"
)


print("\n" + "=" * 70)
print("OPTIMAL COST-SENSITIVE THRESHOLD")
print("=" * 70)

print(
    f"Threshold   : {optimal_threshold:.2f}"
)

print(
    f"FP          : {int(optimal_row['FP'])}"
)

print(
    f"FN          : {int(optimal_row['FN'])}"
)

print(
    f"TP          : {int(optimal_row['TP'])}"
)

print(
    f"TN          : {int(optimal_row['TN'])}"
)

print(
    f"Precision   : {optimal_row['precision']:.6f}"
)

print(
    f"Recall      : {optimal_row['recall']:.6f}"
)

print(
    f"F1          : {optimal_row['f1']:.6f}"
)

print(
    f"Expected Cost : {minimum_cost:.2f}"
)

print(
    f"Review Rate : "
    f"{optimal_row['review_rate'] * 100:.4f}%"
)


print("\n" + "=" * 70)
print("COST COMPARISON")
print("=" * 70)

print(
    f"Cost at 0.50       : {baseline_cost:.2f}"
)

print(
    f"Minimum cost       : {minimum_cost:.2f}"
)

print(
    f"Cost reduction     : {cost_reduction:.2f}"
)

print(
    f"Cost reduction (%) : "
    f"{cost_reduction_percentage:.2f}%"
)


# ============================================================
# TOP 10 LOWEST-COST THRESHOLDS
# ============================================================

print("\n" + "=" * 70)
print("TOP 10 LOWEST-COST THRESHOLDS")
print("=" * 70)

top_10 = results_df.sort_values(
    "expected_cost"
).head(10)

print(
    top_10[
        [
            "threshold",
            "FP",
            "FN",
            "precision",
            "recall",
            "f1",
            "expected_cost",
            "review_rate",
        ]
    ].to_string(index=False)
)


print("\nResults saved to:")
print(OUTPUT_PATH)

print("\n✓ Cost-sensitive threshold analysis completed.")