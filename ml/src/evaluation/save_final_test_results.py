from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import (
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

TEST_PATH = PROJECT_ROOT / "ml" / "data" / "test_processed.csv"
MODEL_PATH = PROJECT_ROOT / "ml" / "models" / "xgboost_baseline.joblib"
OUTPUT_PATH = PROJECT_ROOT / "ml" / "reports" / "final_test_results.csv"


# ------------------------------------------------------------
# Load data and model
# ------------------------------------------------------------

test_df = pd.read_csv(TEST_PATH)
model = joblib.load(MODEL_PATH)

X_test = test_df.drop(columns=["Class"])
y_test = test_df["Class"]


# ------------------------------------------------------------
# Predictions
# ------------------------------------------------------------

probability = model.predict_proba(X_test)[:, 1]

threshold = 0.50
prediction = (probability >= threshold).astype(int)


# ------------------------------------------------------------
# Metrics
# ------------------------------------------------------------

precision = precision_score(y_test, prediction, zero_division=0)
recall = recall_score(y_test, prediction, zero_division=0)
f1 = f1_score(y_test, prediction, zero_division=0)
roc_auc = roc_auc_score(y_test, probability)
pr_auc = average_precision_score(y_test, probability)

tn, fp, fn, tp = confusion_matrix(
    y_test,
    prediction
).ravel()


# ------------------------------------------------------------
# Preliminary cost calculation
# ------------------------------------------------------------

FP_COST = 5
FN_COST = 100

expected_cost = (FP_COST * fp) + (FN_COST * fn)


# ------------------------------------------------------------
# Create results table
# ------------------------------------------------------------

results = pd.DataFrame([
    {
        "model": "XGBoost",
        "dataset": "ULB Credit Card Fraud Detection",
        "split": "test",
        "threshold": threshold,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "roc_auc": roc_auc,
        "pr_auc": pr_auc,
        "tn": tn,
        "fp": fp,
        "fn": fn,
        "tp": tp,
        "fp_cost": FP_COST,
        "fn_cost": FN_COST,
        "expected_cost": expected_cost
    }
])


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

results.to_csv(OUTPUT_PATH, index=False)

print(f"Saved final test results to: {OUTPUT_PATH}")
print()
print(results.to_string(index=False))