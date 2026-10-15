
from pathlib import Path

import joblib
import numpy as np
import pandas as pd


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_PATH = PROJECT_ROOT / "ml" / "models" / "xgboost_baseline.joblib"
SCALER_PATH = PROJECT_ROOT / "ml" / "models" / "preprocessor.joblib"


# ------------------------------------------------------------
# Feature order
# ------------------------------------------------------------

FEATURES = [
    "Time",
    *[f"V{i}" for i in range(1, 29)],
    "Amount",
]


# ------------------------------------------------------------
# Load model and scaler
# ------------------------------------------------------------

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)


# ------------------------------------------------------------
# Prediction function
# ------------------------------------------------------------

def predict_fraud(transaction: dict) -> float:
    """
    Predict the fraud probability for one transaction.

    Required features:
        Time, V1...V28, Amount

    Returns:
        A fraud probability between 0 and 1.

    Raises:
        TypeError: If transaction is not a dictionary.
        ValueError: If features are missing or values are invalid.
    """

    # Check input type
    if not isinstance(transaction, dict):
        raise TypeError("Transaction must be a dictionary.")

    # Check required features
    missing_features = [
        feature for feature in FEATURES
        if feature not in transaction
    ]

    if missing_features:
        raise ValueError(
            f"Missing required features: {', '.join(missing_features)}"
        )

    # Convert values into a numeric DataFrame
    try:
        input_data = pd.DataFrame(
            [[transaction[feature] for feature in FEATURES]],
            columns=FEATURES,
        ).astype(float)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            "All transaction features must be numeric."
        ) from exc

    # Reject NaN and infinite values
    if not np.isfinite(input_data.to_numpy()).all():
        raise ValueError(
            "Transaction features must be finite numbers."
        )

    # Apply the saved preprocessing
    input_scaled = scaler.transform(input_data)

    # Predict fraud probability
    fraud_probability = model.predict_proba(input_scaled)[0, 1]

    return float(fraud_probability)
