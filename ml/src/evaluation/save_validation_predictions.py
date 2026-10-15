import pandas as pd
import joblib

from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

VALIDATION_PATH = (
    PROJECT_ROOT / "ml" / "data" / "validation_processed.csv"
)

LOGISTIC_MODEL_PATH = (
    PROJECT_ROOT / "ml" / "models"
    / "logistic_regression_baseline.joblib"
)

XGBOOST_MODEL_PATH = (
    PROJECT_ROOT / "ml" / "models"
    / "xgboost_baseline.joblib"
)

DECISION_TREE_MODEL_PATH = (
    PROJECT_ROOT / "ml" / "models"
    / "decision_tree_baseline.joblib"
)

OUTPUT_PATH = (
    PROJECT_ROOT / "ml" / "reports"
    / "validation_predictions.csv"
)


# ============================================================
# LOAD VALIDATION DATA
# ============================================================

print("=" * 70)
print("SAVING VALIDATION PREDICTIONS")
print("=" * 70)

validation_df = pd.read_csv(VALIDATION_PATH)

X_validation = validation_df.drop(columns=["Class"])
y_validation = validation_df["Class"]

print("\nValidation data:")
print(f"Rows     : {len(validation_df)}")
print(f"Features : {X_validation.shape[1]}")


# ============================================================
# LOAD MODELS
# ============================================================

print("\nLoading models...")

logistic_model = joblib.load(LOGISTIC_MODEL_PATH)
xgboost_model = joblib.load(XGBOOST_MODEL_PATH)
decision_tree_model = joblib.load(DECISION_TREE_MODEL_PATH)

print("✓ Logistic Regression loaded.")
print("✓ XGBoost loaded.")
print("✓ Decision Tree loaded.")


# ============================================================
# GENERATE PROBABILITIES
# ============================================================

print("\nGenerating probabilities...")

logistic_probability = logistic_model.predict_proba(
    X_validation
)[:, 1]

xgboost_probability = xgboost_model.predict_proba(
    X_validation
)[:, 1]

decision_tree_probability = decision_tree_model.predict_proba(
    X_validation
)[:, 1]

print("✓ Logistic Regression probabilities generated.")
print("✓ XGBoost probabilities generated.")
print("✓ Decision Tree probabilities generated.")


# ============================================================
# CREATE OUTPUT DATAFRAME
# ============================================================

results = pd.DataFrame({
    "actual_class": y_validation.to_numpy(),
    "logistic_probability": logistic_probability,
    "decision_tree_probability": decision_tree_probability,
    "xgboost_probability": xgboost_probability,
})


# ============================================================
# SAVE
# ============================================================

OUTPUT_PATH.parent.mkdir(
    parents=True,
    exist_ok=True,
)

results.to_csv(
    OUTPUT_PATH,
    index=False,
)


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("VALIDATION")
print("=" * 70)

print(f"\nRows saved: {len(results)}")

print("\nColumns:")
for column in results.columns:
    print(f"- {column}")

print("\nActual class distribution:")
print(results["actual_class"].value_counts())

print("\nLogistic Regression probability range:")
print(
    f"Min: {results['logistic_probability'].min():.6f}"
)
print(
    f"Max: {results['logistic_probability'].max():.6f}"
)

print("\nDecision Tree probability range:")
print(
    f"Min: {results['decision_tree_probability'].min():.6f}"
)
print(
    f"Max: {results['decision_tree_probability'].max():.6f}"
)

print("\nXGBoost probability range:")
print(
    f"Min: {results['xgboost_probability'].min():.6f}"
)
print(
    f"Max: {results['xgboost_probability'].max():.6f}"
)

print("\nSaved to:")
print(OUTPUT_PATH)

print("\n✓ Validation predictions saved successfully.")