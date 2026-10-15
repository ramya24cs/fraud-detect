import pandas as pd
import joblib

from pathlib import Path
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix
)


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

TRAIN_PATH = PROJECT_ROOT / "ml" / "data" / "train_processed.csv"
VALIDATION_PATH = PROJECT_ROOT / "ml" / "data" / "validation_processed.csv"
MODEL_PATH = PROJECT_ROOT / "ml" / "models" / "decision_tree_baseline.joblib"


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("DECISION TREE BASELINE")
print("=" * 70)

train_df = pd.read_csv(TRAIN_PATH)
validation_df = pd.read_csv(VALIDATION_PATH)

X_train = train_df.drop(columns=["Class"])
y_train = train_df["Class"]

X_val = validation_df.drop(columns=["Class"])
y_val = validation_df["Class"]

print("\nTraining shape:", X_train.shape)
print("Validation shape:", X_val.shape)

print("\nTraining class distribution:")
print(y_train.value_counts())

print("\nValidation class distribution:")
print(y_val.value_counts())


# ============================================================
# CALCULATE CLASS WEIGHT
# ============================================================

negative_count = (y_train == 0).sum()
positive_count = (y_train == 1).sum()

scale = negative_count / positive_count

print(f"\nNegative samples: {negative_count}")
print(f"Positive samples: {positive_count}")
print(f"Class imbalance ratio: {scale:.4f}")


# ============================================================
# TRAIN DECISION TREE
# ============================================================

model = DecisionTreeClassifier(
    class_weight="balanced",
    max_depth=6,
    min_samples_leaf=10,
    random_state=42
)

print("\nTraining Decision Tree...")

model.fit(X_train, y_train)

print("Training complete.")


# ============================================================
# VALIDATION PREDICTIONS
# ============================================================

probabilities = model.predict_proba(X_val)[:, 1]

threshold = 0.50

predictions = (
    probabilities >= threshold
).astype(int)


# ============================================================
# METRICS
# ============================================================

precision = precision_score(
    y_val,
    predictions,
    zero_division=0
)

recall = recall_score(
    y_val,
    predictions,
    zero_division=0
)

f1 = f1_score(
    y_val,
    predictions,
    zero_division=0
)

roc_auc = roc_auc_score(
    y_val,
    probabilities
)

pr_auc = average_precision_score(
    y_val,
    probabilities
)

tn, fp, fn, tp = confusion_matrix(
    y_val,
    predictions
).ravel()


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 70)
print("VALIDATION RESULTS")
print("=" * 70)

print(f"Threshold:  {threshold:.2f}")
print(f"Precision:  {precision:.6f}")
print(f"Recall:     {recall:.6f}")
print(f"F1 Score:   {f1:.6f}")
print(f"ROC-AUC:    {roc_auc:.6f}")
print(f"PR-AUC:     {pr_auc:.6f}")

print("\nConfusion Matrix:")
print(f"TN: {tn}")
print(f"FP: {fp}")
print(f"FN: {fn}")
print(f"TP: {tp}")

print("\nProbability statistics:")
print(f"Minimum: {probabilities.min():.6f}")
print(f"Maximum: {probabilities.max():.6f}")
print(f"Mean:    {probabilities.mean():.6f}")


# ============================================================
# SAVE MODEL
# ============================================================

joblib.dump(model, MODEL_PATH)

print("\nModel saved to:")
print(MODEL_PATH)

print("\n✓ Decision Tree baseline completed.")