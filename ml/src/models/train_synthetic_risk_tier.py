"""Train an experimental risk-tier model from labeled synthetic transactions."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODEL_PATH = PROJECT_ROOT / "ml" / "models" / "risk_tier_synthetic.joblib"
REPORT_PATH = (
    PROJECT_ROOT / "ml" / "reports" / "synthetic_risk_tier_metrics.json"
)

RISK_TIERS = ["LOW", "MEDIUM", "HIGH"]
CATEGORICAL_FEATURES = [
    "currency",
    "transaction_type",
    "merchant_or_recipient",
    "payment_channel",
    "location",
]
NUMERIC_FEATURES = [
    "amount",
    "account_age_days",
    "transactions_last_1h",
    "avg_amount_30d",
    "new_recipient",
    "distance_from_usual_km",
    "failed_attempts_24h",
    "hour_of_day",
    "is_weekend",
]
FEATURES = CATEGORICAL_FEATURES + NUMERIC_FEATURES
REQUIRED_COLUMNS = {
    "transaction_id",
    "transaction_datetime",
    "risk_label",
    "risk_score",
    *FEATURES,
}


def _load_data(
    data_path: Path,
) -> tuple[pd.DataFrame, pd.Series, pd.Series, int]:
    data = pd.read_csv(data_path)
    missing = REQUIRED_COLUMNS - set(data.columns)
    if missing:
        raise ValueError(f"Dataset is missing required columns: {sorted(missing)}")
    if data["transaction_id"].duplicated().any():
        raise ValueError("Dataset contains duplicate transaction_id values.")

    data["transaction_datetime"] = pd.to_datetime(
        data["transaction_datetime"],
        errors="raise",
        utc=True,
    )
    for column in NUMERIC_FEATURES:
        data[column] = pd.to_numeric(data[column], errors="raise")

    if data[FEATURES + ["risk_label", "risk_score"]].isna().any().any():
        raise ValueError("Dataset contains missing features or target values.")
    if not data[NUMERIC_FEATURES].map(
        lambda value: pd.notna(value) and abs(float(value)) != float("inf")
    ).all().all():
        raise ValueError("Numeric features must contain only finite numbers.")

    labels = data["risk_label"].astype(str).str.strip().str.upper()
    invalid_labels = sorted(set(labels) - set(RISK_TIERS))
    if invalid_labels:
        raise ValueError(f"Unexpected risk_label values: {invalid_labels}")
    if set(labels) != set(RISK_TIERS):
        raise ValueError("Dataset must contain LOW, MEDIUM, and HIGH labels.")

    risk_scores = pd.to_numeric(data["risk_score"], errors="raise")
    expected_labels = pd.Series("LOW", index=data.index)
    expected_labels.loc[risk_scores >= 35] = "MEDIUM"
    expected_labels.loc[risk_scores >= 55] = "HIGH"
    score_label_mismatch_count = int((expected_labels != labels).sum())

    data["hour_of_day"] = data["transaction_datetime"].dt.hour
    data["is_weekend"] = (
        data["transaction_datetime"].dt.dayofweek >= 5
    ).astype(int)
    features = data[FEATURES].copy()
    features[CATEGORICAL_FEATURES] = features[CATEGORICAL_FEATURES].astype(str)

    return (
        features,
        labels,
        data["transaction_datetime"],
        score_label_mismatch_count,
    )


def _create_model() -> Pipeline:
    preprocessor = ColumnTransformer(
        [
            (
                "categorical",
                OneHotEncoder(handle_unknown="ignore"),
                CATEGORICAL_FEATURES,
            ),
            ("numeric", "passthrough", NUMERIC_FEATURES),
        ]
    )
    classifier = ExtraTreesClassifier(
        n_estimators=300,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1,
    )
    return Pipeline(
        [
            ("preprocessor", preprocessor),
            ("classifier", classifier),
        ]
    )


def train(data_path: Path) -> dict[str, Any]:
    features, labels, timestamps, score_label_mismatch_count = _load_data(
        data_path
    )
    cutoff = timestamps.quantile(0.8)
    train_mask = timestamps < cutoff
    test_mask = ~train_mask

    if labels[train_mask].nunique() != len(RISK_TIERS):
        raise ValueError(
            "Chronological training split must contain all three risk tiers."
        )
    if labels[test_mask].nunique() != len(RISK_TIERS):
        raise ValueError(
            "Chronological test split must contain all three risk tiers."
        )

    evaluation_model = _create_model()
    evaluation_model.fit(features.loc[train_mask], labels.loc[train_mask])
    predictions = evaluation_model.predict(features.loc[test_mask])
    y_test = labels.loc[test_mask]

    report = classification_report(
        y_test,
        predictions,
        labels=RISK_TIERS,
        output_dict=True,
        zero_division=0,
    )
    metrics = {
        "accuracy": float(accuracy_score(y_test, predictions)),
        "balanced_accuracy": float(
            balanced_accuracy_score(y_test, predictions)
        ),
        "macro_f1": float(f1_score(y_test, predictions, average="macro")),
        "class_report": report,
        "confusion_matrix_labels": RISK_TIERS,
        "confusion_matrix": confusion_matrix(
            y_test,
            predictions,
            labels=RISK_TIERS,
        ).tolist(),
    }

    final_model = _create_model()
    final_model.fit(features, labels)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "model": final_model,
            "features": FEATURES,
            "risk_tiers": RISK_TIERS,
            "target": "risk_label",
            "model_version": "synthetic-risk-tier-v1",
        },
        MODEL_PATH,
    )

    dataset_counts = {
        tier: int((labels == tier).sum()) for tier in RISK_TIERS
    }
    test_counts = {
        tier: int((y_test == tier).sum()) for tier in RISK_TIERS
    }
    metadata = {
        "model_version": "synthetic-risk-tier-v1",
        "model_type": "ExtraTreesClassifier",
        "dataset": data_path.name,
        "dataset_is_synthetic": True,
        "target": "risk_label",
        "excluded_columns": [
            "risk_score",
            "is_fraud",
            "transaction_id",
            "reference_id",
        ],
        "features": FEATURES,
        "feature_availability_note": (
            "The model needs all listed transaction and account-context "
            "features. The current transaction form/API does not collect all "
            "of them, so this artifact is not wired into live predictions."
        ),
        "rows": len(labels),
        "class_counts": dataset_counts,
        "risk_score_label_mismatches": score_label_mismatch_count,
        "observed_label_rule": {
            "LOW": "risk_score < 35",
            "MEDIUM": "35 <= risk_score < 55",
            "HIGH": "risk_score >= 55",
        },
        "evaluation": {
            "method": "chronological 80/20 holdout",
            "cutoff_utc": cutoff.isoformat(),
            "train_rows": int(train_mask.sum()),
            "test_rows": int(test_mask.sum()),
            "test_class_counts": test_counts,
            "metrics": metrics,
            "caveat": (
                "Synthetic-data development estimate, not real-world "
                "validation. This chronological window was consulted during "
                "development experiments, so it is not a pristine final "
                "holdout. The HIGH class is sparse; inspect per-class recall "
                "before any deployment."
            ),
        },
        "artifact_path": str(MODEL_PATH.relative_to(PROJECT_ROOT)),
    }
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(metadata, indent=2, allow_nan=False) + "\n",
        encoding="utf-8",
    )

    print(json.dumps(metadata, indent=2, allow_nan=False))
    print(f"\nModel saved: {MODEL_PATH}")
    print(f"Report saved: {REPORT_PATH}")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Train an experimental LOW/MEDIUM/HIGH risk-tier model."
    )
    parser.add_argument(
        "--data-path",
        type=Path,
        required=True,
        help="Path to the synthetic labeled transactions CSV.",
    )
    args = parser.parse_args()
    train(args.data_path)


if __name__ == "__main__":
    main()
