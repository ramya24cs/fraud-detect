import pandas as pd
import joblib
import matplotlib.pyplot as plt

from pathlib import Path
from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss


# ============================================================
# PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

VALIDATION_PATH = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "validation_processed.csv"
)

MODEL_PATH = (
    PROJECT_ROOT
    / "ml"
    / "models"
    / "xgboost_baseline.joblib"
)

OUTPUT_DIR = PROJECT_ROOT / "ml" / "reports"


# ============================================================
# LOAD DATA AND MODEL
# ============================================================

print("=" * 70)
print("XGBOOST PROBABILITY CALIBRATION ANALYSIS")
print("=" * 70)

validation_df = pd.read_csv(VALIDATION_PATH)

X_val = validation_df.drop(columns=["Class"])
y_val = validation_df["Class"]

model = joblib.load(MODEL_PATH)

print("\nValidation shape:", X_val.shape)
print("Validation fraud cases:", int(y_val.sum()))


# ============================================================
# RAW XGBOOST PROBABILITIES
# ============================================================

raw_probabilities = model.predict_proba(X_val)[:, 1]


# ============================================================
# BRIER SCORE
# ============================================================

raw_brier = brier_score_loss(
    y_val,
    raw_probabilities
)

print("\nRaw XGBoost probability results:")
print(f"Brier Score: {raw_brier:.8f}")
print(f"Minimum probability: {raw_probabilities.min():.6f}")
print(f"Maximum probability: {raw_probabilities.max():.6f}")
print(f"Mean probability:    {raw_probabilities.mean():.6f}")


# ============================================================
# CALIBRATION CURVE
# ============================================================

fraction_positive, mean_predicted = calibration_curve(
    y_val,
    raw_probabilities,
    n_bins=10,
    strategy="quantile"
)


# ============================================================
# SAVE CALIBRATION DATA
# ============================================================

calibration_results = pd.DataFrame({
    "mean_predicted_probability": mean_predicted,
    "fraction_of_fraud": fraction_positive
})

CALIBRATION_CSV = (
    OUTPUT_DIR / "xgboost_calibration_curve.csv"
)

calibration_results.to_csv(
    CALIBRATION_CSV,
    index=False
)


# ============================================================
# PLOT CALIBRATION CURVE
# ============================================================

plt.figure(figsize=(8, 7))

plt.plot(
    [0, 1],
    [0, 1],
    linestyle="--",
    label="Perfect calibration"
)

plt.plot(
    mean_predicted,
    fraction_positive,
    marker="o",
    label="XGBoost"
)

plt.xlabel("Mean Predicted Fraud Probability")
plt.ylabel("Observed Fraud Frequency")

plt.title(
    "XGBoost Probability Calibration — Validation Set"
)

plt.legend()
plt.grid(True)

FIGURE_PATH = (
    OUTPUT_DIR / "xgboost_calibration_curve.png"
)

plt.savefig(
    FIGURE_PATH,
    dpi=300,
    bbox_inches="tight"
)

plt.close()


# ============================================================
# SAVE SUMMARY
# ============================================================

summary = pd.DataFrame({
    "Model": ["XGBoost"],
    "Brier_Score": [raw_brier],
    "Calibration_Method": ["Raw model probabilities"],
    "Evaluation_Set": ["Validation"]
})

SUMMARY_PATH = (
    OUTPUT_DIR / "calibration_summary.csv"
)

summary.to_csv(
    SUMMARY_PATH,
    index=False
)


# ============================================================
# DISPLAY
# ============================================================

print("\nCalibration curve:")
print(calibration_results.to_string(index=False))

print("\n" + "=" * 70)
print("OUTPUT FILES")
print("=" * 70)

print("\nCalibration data:")
print(CALIBRATION_CSV)

print("\nCalibration figure:")
print(FIGURE_PATH)

print("\nCalibration summary:")
print(SUMMARY_PATH)

print("\n✓ Calibration analysis completed.")