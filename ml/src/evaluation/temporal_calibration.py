import pandas as pd
import joblib

from pathlib import Path

from xgboost import XGBClassifier
from sklearn.isotonic import IsotonicRegression
from sklearn.metrics import brier_score_loss


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

TRAIN_PATH = PROJECT_ROOT / "ml" / "data" / "train_processed.csv"
VALIDATION_PATH = PROJECT_ROOT / "ml" / "data" / "validation_processed.csv"

MODEL_OUTPUT = (
    PROJECT_ROOT
    / "ml"
    / "models"
    / "xgboost_isotonic_calibrated.joblib"
)

RESULTS_OUTPUT = (
    PROJECT_ROOT
    / "ml"
    / "reports"
    / "temporal_calibration_results.csv"
)


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("TEMPORAL XGBOOST CALIBRATION")
print("=" * 70)

train_df = pd.read_csv(TRAIN_PATH)
validation_df = pd.read_csv(VALIDATION_PATH)

X_train_full = train_df.drop(columns=["Class"])
y_train_full = train_df["Class"]

X_val = validation_df.drop(columns=["Class"])
y_val = validation_df["Class"]


# ============================================================
# TEMPORAL TRAIN/CALIBRATION SPLIT
# ============================================================

split_index = int(len(train_df) * 0.85)

X_model = X_train_full.iloc[:split_index]
y_model = y_train_full.iloc[:split_index]

X_calibration = X_train_full.iloc[split_index:]
y_calibration = y_train_full.iloc[split_index:]

print("\nDevelopment split:")
print("Model-training rows:", len(X_model))
print("Calibration rows:   ", len(X_calibration))
print("Validation rows:    ", len(X_val))

print("\nModel-training fraud cases:", int(y_model.sum()))
print("Calibration fraud cases:   ", int(y_calibration.sum()))
print("Validation fraud cases:    ", int(y_val.sum()))


# ============================================================
# TRAIN XGBOOST
# ============================================================

negative_count = (y_model == 0).sum()
positive_count = (y_model == 1).sum()

scale_pos_weight = negative_count / positive_count

print("\nScale positive weight:", scale_pos_weight)

model = XGBClassifier(
    n_estimators=300,
    max_depth=6,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="binary:logistic",
    eval_metric="logloss",
    scale_pos_weight=scale_pos_weight,
    random_state=42,
    n_jobs=-1
)

print("\nTraining XGBoost on model-training portion...")

model.fit(X_model, y_model)

print("Training complete.")


# ============================================================
# GET CALIBRATION PROBABILITIES
# ============================================================

calibration_probabilities = (
    model.predict_proba(X_calibration)[:, 1]
)


# ============================================================
# FIT ISOTONIC CALIBRATION
# ============================================================

print("\nFitting isotonic calibration...")

calibrator = IsotonicRegression(
    y_min=0.0,
    y_max=1.0,
    out_of_bounds="clip"
)

calibrator.fit(
    calibration_probabilities,
    y_calibration
)

print("Calibration complete.")


# ============================================================
# VALIDATION PROBABILITIES
# ============================================================

raw_validation_probabilities = (
    model.predict_proba(X_val)[:, 1]
)

calibrated_validation_probabilities = (
    calibrator.predict(raw_validation_probabilities)
)


# ============================================================
# BRIER SCORES
# ============================================================

raw_brier = brier_score_loss(
    y_val,
    raw_validation_probabilities
)

calibrated_brier = brier_score_loss(
    y_val,
    calibrated_validation_probabilities
)


# ============================================================
# RESULTS
# ============================================================

print("\n" + "=" * 70)
print("VALIDATION CALIBRATION RESULTS")
print("=" * 70)

print(f"\nRaw XGBoost Brier Score:        {raw_brier:.8f}")
print(f"Isotonic XGBoost Brier Score:  {calibrated_brier:.8f}")

if calibrated_brier < raw_brier:
    improvement = (
        (raw_brier - calibrated_brier)
        / raw_brier
        * 100
    )

    print(f"\nBrier score improvement: {improvement:.2f}%")
    print("Calibration improved the Brier score.")
else:
    difference = (
        (calibrated_brier - raw_brier)
        / raw_brier
        * 100
    )

    print(f"\nBrier score change: {difference:.2f}%")
    print("Calibration did not improve the Brier score.")


# ============================================================
# SAVE RESULTS
# ============================================================

results = pd.DataFrame({
    "Model": [
        "XGBoost Raw",
        "XGBoost Isotonic"
    ],
    "Brier_Score": [
        raw_brier,
        calibrated_brier
    ],
    "Calibration_Method": [
        "None",
        "Isotonic Regression"
    ],
    "Evaluation_Set": [
        "Validation",
        "Validation"
    ]
})

results.to_csv(
    RESULTS_OUTPUT,
    index=False
)


# ============================================================
# SAVE CALIBRATED MODEL
# ============================================================

artifact = {
    "model": model,
    "calibrator": calibrator,
    "calibration_method": "isotonic",
    "random_state": 42
}

joblib.dump(
    artifact,
    MODEL_OUTPUT
)


# ============================================================
# FINISH
# ============================================================

print("\nResults saved to:")
print(RESULTS_OUTPUT)

print("\nCalibrated model saved to:")
print(MODEL_OUTPUT)

print("\n✓ Temporal calibration analysis completed.")