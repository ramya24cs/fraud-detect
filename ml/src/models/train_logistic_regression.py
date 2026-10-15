import pandas as pd
import joblib

from pathlib import Path
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    average_precision_score,
    confusion_matrix,
)


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

TRAIN_PATH = PROJECT_ROOT / "ml" / "data" / "train_processed.csv"
VALIDATION_PATH = PROJECT_ROOT / "ml" / "data" / "validation_processed.csv"

MODEL_DIR = PROJECT_ROOT / "ml" / "models"
MODEL_PATH = MODEL_DIR / "logistic_regression_baseline.joblib"


# ============================================================
# CONFIGURATION
# ============================================================

TARGET_COLUMN = "Class"

RANDOM_STATE = 42

# Initial baseline threshold.
# This is NOT the final cost-sensitive threshold.
BASELINE_THRESHOLD = 0.50


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("COST-SENSITIVE FRAUD DETECTION")
print("LOGISTIC REGRESSION BASELINE")
print("=" * 70)

train_df = pd.read_csv(TRAIN_PATH)
validation_df = pd.read_csv(VALIDATION_PATH)

print("\nLoaded data:")
print(f"Train      : {train_df.shape}")
print(f"Validation : {validation_df.shape}")


# ============================================================
# SEPARATE FEATURES AND TARGET
# ============================================================

X_train = train_df.drop(columns=[TARGET_COLUMN])
y_train = train_df[TARGET_COLUMN]

X_validation = validation_df.drop(columns=[TARGET_COLUMN])
y_validation = validation_df[TARGET_COLUMN]


print("\nFeature information:")
print(f"Number of features: {X_train.shape[1]}")
print(f"Training rows     : {X_train.shape[0]}")
print(f"Validation rows   : {X_validation.shape[0]}")


# ============================================================
# TRAIN LOGISTIC REGRESSION
# ============================================================

print("\nTraining Logistic Regression...")

model = LogisticRegression(
    class_weight="balanced",
    max_iter=1000,
    random_state=RANDOM_STATE,
)

model.fit(X_train, y_train)

print("✓ Model training completed.")


# ============================================================
# GENERATE FRAUD PROBABILITIES
# ============================================================

print("\nGenerating validation probabilities...")

validation_probabilities = model.predict_proba(X_validation)[:, 1]

print("✓ Fraud probabilities generated.")


# ============================================================
# BASELINE DECISION
# ============================================================

validation_predictions = (
    validation_probabilities >= BASELINE_THRESHOLD
).astype(int)


# ============================================================
# METRICS
# ============================================================

precision = precision_score(
    y_validation,
    validation_predictions,
    zero_division=0,
)

recall = recall_score(
    y_validation,
    validation_predictions,
    zero_division=0,
)

f1 = f1_score(
    y_validation,
    validation_predictions,
    zero_division=0,
)

roc_auc = roc_auc_score(
    y_validation,
    validation_probabilities,
)

pr_auc = average_precision_score(
    y_validation,
    validation_probabilities,
)

tn, fp, fn, tp = confusion_matrix(
    y_validation,
    validation_predictions,
    labels=[0, 1],
).ravel()


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\n" + "=" * 70)
print("VALIDATION RESULTS")
print("=" * 70)

print(f"\nThreshold : {BASELINE_THRESHOLD}")

print(f"\nPrecision : {precision:.6f}")
print(f"Recall    : {recall:.6f}")
print(f"F1 Score  : {f1:.6f}")
print(f"ROC-AUC   : {roc_auc:.6f}")
print(f"PR-AUC    : {pr_auc:.6f}")

print("\nConfusion Matrix:")
print(f"TN : {tn}")
print(f"FP : {fp}")
print(f"FN : {fn}")
print(f"TP : {tp}")


# ============================================================
# SAVE MODEL
# ============================================================

MODEL_DIR.mkdir(parents=True, exist_ok=True)

joblib.dump(model, MODEL_PATH)

print("\nModel saved to:")
print(MODEL_PATH)


# ============================================================
# PROBABILITY VALIDATION
# ============================================================

print("\nProbability validation:")
print(f"Minimum probability : {validation_probabilities.min():.6f}")
print(f"Maximum probability : {validation_probabilities.max():.6f}")
print(f"Mean probability    : {validation_probabilities.mean():.6f}")

print("\n✓ Logistic Regression baseline completed.")