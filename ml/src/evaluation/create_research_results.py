import pandas as pd
import matplotlib.pyplot as plt

from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

THRESHOLD_RESULTS_PATH = (
    PROJECT_ROOT
    / "ml"
    / "reports"
    / "threshold_analysis_xgboost.csv"
)

REFINED_RESULTS_PATH = (
    PROJECT_ROOT
    / "ml"
    / "reports"
    / "refined_threshold_analysis.csv"
)

OUTPUT_DIR = PROJECT_ROOT / "ml" / "reports"


# ============================================================
# LOAD THRESHOLD RESULTS
# ============================================================

print("=" * 70)
print("RESEARCH RESULTS AND FIGURES")
print("=" * 70)

results = pd.read_csv(THRESHOLD_RESULTS_PATH)
refined_results = pd.read_csv(REFINED_RESULTS_PATH)

print("\nLoaded coarse threshold results:")
print(f"Rows: {len(results)}")

print("\nLoaded refined threshold results:")
print(f"Rows: {len(refined_results)}")


# ============================================================
# BASELINE THRESHOLD
# ============================================================

baseline = results[
    results["threshold"] == 0.50
].iloc[0]


# ============================================================
# REFINED THRESHOLD ANALYSIS
# ============================================================

# Find the minimum expected cost automatically.
minimum_cost = refined_results["expected_cost"].min()

# Find every threshold having that minimum cost.
best_rows = refined_results[
    refined_results["expected_cost"] == minimum_cost
].copy()

best_thresholds = best_rows["threshold"].tolist()

refined_threshold_low = min(best_thresholds)
refined_threshold_high = max(best_thresholds)

# Use the first tied row for the comparison table.
refined = best_rows.iloc[0]

refined_FP = int(refined["FP"])
refined_FN = int(refined["FN"])
refined_TP = int(refined["TP"])
refined_TN = int(refined["TN"])

refined_precision = refined["precision"]
refined_recall = refined["recall"]
refined_f1 = refined["f1"]

refined_expected_cost = minimum_cost

refined_review_rate = (
    (refined_FP + refined_TP)
    / (
        refined_FP
        + refined_TP
        + refined_TN
        + refined_FN
    )
)


# ============================================================
# COST REDUCTION
# ============================================================

baseline_expected_cost = baseline["expected_cost"]

cost_reduction = (
    baseline_expected_cost
    - refined_expected_cost
)

relative_cost_reduction = (
    cost_reduction
    / baseline_expected_cost
) * 100


# ============================================================
# MODEL COMPARISON TABLE
# ============================================================

model_comparison = pd.DataFrame({
    "Model": [
        "Logistic Regression",
        "Decision Tree",
        "XGBoost"
    ],
    "Threshold": [
        0.50,
        0.50,
        0.50
    ],
    "Precision": [
        0.053170,
        0.030856,
        0.916667
    ],
    "Recall": [
        0.928571,
        0.785714,
        0.785714
    ],
    "F1": [
        0.100580,
        0.059379,
        0.846154
    ],
    "ROC_AUC": [
        0.982786,
        0.818286,
        0.990778
    ],
    "PR_AUC": [
        0.839335,
        0.361544,
        0.858069
    ],
    "FP": [
        926,
        1382,
        4
    ],
    "FN": [
        4,
        12,
        12
    ],
})


MODEL_TABLE_PATH = (
    OUTPUT_DIR / "model_comparison_validation.csv"
)

model_comparison.to_csv(
    MODEL_TABLE_PATH,
    index=False
)


# ============================================================
# COST COMPARISON TABLE
# ============================================================

cost_comparison = pd.DataFrame({
    "Policy": [
        "XGBoost threshold = 0.50",
        "XGBoost refined cost-optimized threshold"
    ],
    "Threshold": [
        baseline["threshold"],
        f"{refined_threshold_low:.3f}-{refined_threshold_high:.3f}"
    ],
    "FP": [
        int(baseline["FP"]),
        refined_FP
    ],
    "FN": [
        int(baseline["FN"]),
        refined_FN
    ],
    "TP": [
        int(baseline["TP"]),
        refined_TP
    ],
    "TN": [
        int(baseline["TN"]),
        refined_TN
    ],
    "Precision": [
        baseline["precision"],
        refined_precision
    ],
    "Recall": [
        baseline["recall"],
        refined_recall
    ],
    "F1": [
        baseline["f1"],
        refined_f1
    ],
    "Expected_Cost": [
        baseline_expected_cost,
        refined_expected_cost
    ],
    "Review_Rate": [
        baseline["review_rate"],
        refined_review_rate
    ],
})


COST_TABLE_PATH = (
    OUTPUT_DIR / "cost_policy_comparison.csv"
)

cost_comparison.to_csv(
    COST_TABLE_PATH,
    index=False
)


# ============================================================
# FIGURE 1 — EXPECTED COST VS THRESHOLD
# ============================================================

plt.figure(figsize=(10, 6))

plt.plot(
    results["threshold"],
    results["expected_cost"],
    marker="o",
    markersize=3,
    label="Coarse threshold search"
)

# Baseline threshold
plt.axvline(
    baseline["threshold"],
    linestyle="--",
    label="Baseline threshold = 0.50"
)

# Refined tied thresholds
plt.axvline(
    refined_threshold_low,
    linestyle="--",
    label=(
        f"Refined minimum = "
        f"{refined_threshold_low:.3f}-"
        f"{refined_threshold_high:.3f}"
    )
)

if refined_threshold_high != refined_threshold_low:
    plt.axvline(
        refined_threshold_high,
        linestyle="--"
    )

# Mark minimum expected cost
plt.scatter(
    best_rows["threshold"],
    best_rows["expected_cost"],
    s=80,
    label=(
        f"Minimum expected cost = "
        f"{refined_expected_cost:.0f}"
    )
)

plt.xlabel("Decision Threshold")
plt.ylabel("Expected Cost")
plt.title("Expected Cost vs Decision Threshold — XGBoost")
plt.legend()
plt.grid(True)

COST_FIGURE_PATH = (
    OUTPUT_DIR / "expected_cost_vs_threshold.png"
)

plt.savefig(
    COST_FIGURE_PATH,
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# FIGURE 2 — PRECISION / RECALL VS THRESHOLD
# ============================================================

plt.figure(figsize=(10, 6))

plt.plot(
    results["threshold"],
    results["precision"],
    label="Precision"
)

plt.plot(
    results["threshold"],
    results["recall"],
    label="Recall"
)

plt.axvline(
    refined_threshold_low,
    linestyle="--",
    label=(
        f"Refined cost minimum = "
        f"{refined_threshold_low:.3f}-"
        f"{refined_threshold_high:.3f}"
    )
)

if refined_threshold_high != refined_threshold_low:
    plt.axvline(
        refined_threshold_high,
        linestyle="--"
    )

plt.xlabel("Decision Threshold")
plt.ylabel("Score")
plt.title("Precision and Recall vs Decision Threshold — XGBoost")
plt.legend()
plt.grid(True)

PR_FIGURE_PATH = (
    OUTPUT_DIR / "precision_recall_vs_threshold.png"
)

plt.savefig(
    PR_FIGURE_PATH,
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 70)
print("MODEL COMPARISON")
print("=" * 70)

print(
    model_comparison.to_string(index=False)
)


print("\n" + "=" * 70)
print("COST POLICY COMPARISON")
print("=" * 70)

print(
    cost_comparison.to_string(index=False)
)


print("\n" + "=" * 70)
print("REFINED COST RESULT")
print("=" * 70)

print(
    f"Minimum expected cost: "
    f"{refined_expected_cost:.0f}"
)

print(
    "Tied thresholds: "
    + ", ".join(
        f"{threshold:.3f}"
        for threshold in best_thresholds
    )
)

print(
    f"Baseline expected cost: "
    f"{baseline_expected_cost:.0f}"
)

print(
    f"Cost reduction: "
    f"{cost_reduction:.0f}"
)

print(
    f"Relative reduction: "
    f"{relative_cost_reduction:.2f}%"
)


print("\n" + "=" * 70)
print("RESEARCH OUTPUTS")
print("=" * 70)

print("\nModel comparison table:")
print(MODEL_TABLE_PATH)

print("\nCost policy table:")
print(COST_TABLE_PATH)

print("\nExpected cost figure:")
print(COST_FIGURE_PATH)

print("\nPrecision/recall figure:")
print(PR_FIGURE_PATH)

print("\nResearch results generated successfully.")