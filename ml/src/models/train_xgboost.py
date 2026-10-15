import pandas as pd
import joblib

from pathlib import Path
from xgboost import XGBClassifier
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
MODEL_PATH = MODEL_DIR / "xgboost_baseline.joblib"


# ============================================================
# CONFIGURATION
# ============================================================

TARGET_COLUMN = "Class"

RANDOM_STATE = 42

BASELINE_THRESHOLD = 0.50


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("COST-SENSITIVE FRAUD DETECTION")
print("XGBOOST BASELINE")
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
# CALCULATE CLASS IMBALANCE WEIGHT
# ============================================================

negative_count = (y_train == 0).sum()
positive_count = (y_train == 1).sum()

scale_pos_weight = negative_count / positive_count

print("\nClass imbalance:")
print(f"Legitimate transactions : {negative_count}")
print(f"Fraud transactions      : {positive_count}")
print(f"scale_pos_weight        : {scale_pos_weight:.4f}")


# ============================================================
# CREATE XGBOOST MODEL
# ============================================================

model = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="binary:logistic",
    eval_metric="logloss",
    scale_pos_weight=scale_pos_weight,
    random_state=RANDOM_STATE,
    n_jobs=-1,
)


# ============================================================
# TRAIN MODEL
# ============================================================

print("\nTraining XGBoost...")

model.fit(
    X_train,
    y_train,
)

print("✓ XGBoost training completed.")


# ============================================================
# GENERATE FRAUD PROBABILITIES
# ============================================================

print("\nGenerating validation probabilities...")

validation_probabilities = model.predict_proba(
    X_validation
)[:, 1]

print("✓ Fraud probabilities generated.")


# ============================================================
# BASELINE DECISION
# ============================================================

validation_predictions = (
    validation_probabilities >= BASELINE_THRESHOLD
).astype(int)


# ============================================================
# CALCULATE METRICS
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

print("\n✓ XGBoost baseline completed.")