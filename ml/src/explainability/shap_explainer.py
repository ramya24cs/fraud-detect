from pathlib import Path

import joblib
import pandas as pd
import shap


PROJECT_ROOT = Path(__file__).resolve().parents[3]

MODEL_PATH = PROJECT_ROOT / "ml" / "models" / "xgboost_baseline.joblib"
SCALER_PATH = PROJECT_ROOT / "ml" / "models" / "preprocessor.joblib"

FEATURES = [
    "Time",
    *[f"V{i}" for i in range(1, 29)],
    "Amount",
]

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)

explainer = shap.TreeExplainer(model)


def explain_transaction(transaction: dict, top_k: int = 5) -> list[dict]:
    input_data = pd.DataFrame(
        [[transaction[feature] for feature in FEATURES]],
        columns=FEATURES,
    )

    input_scaled = scaler.transform(input_data)

    shap_values = explainer.shap_values(input_scaled)

    if isinstance(shap_values, list):
        shap_values = shap_values[1]

    impacts = shap_values[0]

    explanation = [
        {
            "feature": feature,
            "impact": float(impact),
        }
        for feature, impact in zip(FEATURES, impacts)
    ]

    explanation.sort(
        key=lambda item: abs(item["impact"]),
        reverse=True,
    )

    return explanation[:top_k]