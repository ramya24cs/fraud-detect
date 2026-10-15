import pandas as pd

from pathlib import Path


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

PREDICTIONS_PATH = (
    PROJECT_ROOT
    / "ml"
    / "reports"
    / "validation_predictions.csv"
)

OUTPUT_PATH = (
    PROJECT_ROOT
    / "ml"
    / "reports"
    / "refined_threshold_analysis.csv"
)


# ============================================================
# COST ASSUMPTIONS
# ============================================================

# Preliminary research experiment.
# Final costs will be defined by Member 2.

FP_COST = 5
FN_COST = 100


# ============================================================
# LOAD VALIDATION PREDICTIONS
# ============================================================

df = pd.read_csv(PREDICTIONS_PATH)

y_true = df["actual_class"]
probabilities = df["xgboost_probability"]


print("=" * 70)
print("REFINED XGBOOST THRESHOLD ANALYSIS")
print("=" * 70)

print("\nValidation rows:", len(df))
print("Fraud cases:", int(y_true.sum()))

print("\nCost assumptions:")
print("False Positive Cost:", FP_COST)
print("False Negative Cost:", FN_COST)


# ============================================================
# REFINED THRESHOLD GRID
# ============================================================

thresholds = [
    round(x / 1000, 3)
    for x in range(30, 51)
]


results = []


# ============================================================
# EVALUATE EACH THRESHOLD
# ============================================================

for threshold in thresholds:

    predictions = (
        probabilities >= threshold
    ).astype(int)

    tp = int(((y_true == 1) & (predictions == 1)).sum())
    tn = int(((y_true == 0) & (predictions == 0)).sum())
    fp = int(((y_true == 0) & (predictions == 1)).sum())
    fn = int(((y_true == 1) & (predictions == 0)).sum())

    precision = (
        tp / (tp + fp)
        if (tp + fp) > 0
        else 0
    )

    recall = (
        tp / (tp + fn)
        if (tp + fn) > 0
        else 0
    )

    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    expected_cost = (
        fp * FP_COST
        + fn * FN_COST
    )

    review_rate = (
        (fp + tp) / len(y_true)
    )

    results.append({
        "threshold": threshold,
        "TP": tp,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "expected_cost": expected_cost,
        "review_rate": review_rate
    })


# ============================================================
# RESULTS DATAFRAME
# ============================================================

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    "threshold"
)


# ============================================================
# FIND BEST THRESHOLD
# ============================================================

best_row = results_df.loc[
    results_df["expected_cost"].idxmin()
]


# ============================================================
# SAVE RESULTS
# ============================================================

results_df.to_csv(
    OUTPUT_PATH,
    index=False
)


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 70)
print("REFINED RESULTS")
print("=" * 70)

print(
    results_df.to_string(index=False)
)


print("\n" + "=" * 70)
print("BEST REFINED THRESHOLD")
print("=" * 70)

print(
    f"Threshold:      {best_row['threshold']:.3f}"
)

print(
    f"Expected Cost:  {best_row['expected_cost']:.0f}"
)

print(
    f"FP:             {best_row['FP']}"
)

print(
    f"FN:             {best_row['FN']}"
)

print(
    f"Precision:      {best_row['precision']:.6f}"
)

print(
    f"Recall:         {best_row['recall']:.6f}"
)

print(
    f"F1:             {best_row['f1']:.6f}"
)

print(
    f"Review Rate:    {best_row['review_rate']:.6%}"
)


print("\nResults saved to:")
print(OUTPUT_PATH)

print("\n✓ Refined threshold analysis completed.")