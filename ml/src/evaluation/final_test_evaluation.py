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


# ------------------------------------------------------------
# Load test data and model
# ------------------------------------------------------------

test_df = pd.read_csv(TEST_PATH)
model = joblib.load(MODEL_PATH)


# ------------------------------------------------------------
# Separate features and target
# ------------------------------------------------------------

X_test = test_df.drop(columns=["Class"])
y_test = test_df["Class"]


# ------------------------------------------------------------
# Generate fraud probabilities
# ------------------------------------------------------------

fraud_probability = model.predict_proba(X_test)[:, 1]


# ------------------------------------------------------------
# Baseline threshold
# ------------------------------------------------------------

threshold = 0.50

y_pred = (fraud_probability >= threshold).astype(int)


# ------------------------------------------------------------
# Metrics
# ------------------------------------------------------------

precision = precision_score(y_test, y_pred, zero_division=0)
recall = recall_score(y_test, y_pred, zero_division=0)
f1 = f1_score(y_test, y_pred, zero_division=0)
roc_auc = roc_auc_score(y_test, fraud_probability)
pr_auc = average_precision_score(y_test, fraud_probability)

tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()


# ------------------------------------------------------------
# Expected cost
# Preliminary Member 1 reporting only
# Final production policy belongs to Member 2.
# ------------------------------------------------------------

FP_COST = 5
FN_COST = 100

expected_cost = (FP_COST * fp) + (FN_COST * fn)


# ------------------------------------------------------------
# Display results
# ------------------------------------------------------------

print("=" * 60)
print("FINAL XGBOOST TEST EVALUATION")
print("=" * 60)

print(f"Test samples: {len(y_test)}")
print(f"Fraud cases: {y_test.sum()}")
print(f"Threshold: {threshold}")

print()
print("Metrics")
print("-" * 60)
print(f"Precision : {precision:.6f}")
print(f"Recall    : {recall:.6f}")
print(f"F1        : {f1:.6f}")
print(f"ROC-AUC   : {roc_auc:.6f}")
print(f"PR-AUC    : {pr_auc:.6f}")

print()
print("Confusion Matrix")
print("-" * 60)
print(f"TN: {tn}")
print(f"FP: {fp}")
print(f"FN: {fn}")
print(f"TP: {tp}")

print()
print("Expected Cost")
print("-" * 60)
print(f"FP cost: {FP_COST}")
print(f"FN cost: {FN_COST}")
print(f"Expected cost: {expected_cost}")

print("=" * 60)