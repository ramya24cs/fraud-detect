
import pytest
from pydantic import ValidationError

from backend.app.schemas.prediction import (
    FEATURE_NAMES,
    PredictionRequest,
)


def valid_features():
    return {name: 1.0 for name in FEATURE_NAMES}


def test_prediction_request_accepts_all_required_features():
    request = PredictionRequest(
        transaction_id="test-transaction-001",
        features=valid_features(),
    )

    assert len(request.features) == 30
    assert request.features["Amount"] == 1.0


def test_prediction_request_rejects_missing_feature():
    features = valid_features()
    features.pop("Amount")

    with pytest.raises(ValidationError):
        PredictionRequest(
            transaction_id="test-transaction-002",
            features=features,
        )


def test_prediction_request_rejects_non_finite_feature():
    features = valid_features()
    features["Amount"] = float("nan")

    with pytest.raises(ValidationError):
        PredictionRequest(
            transaction_id="test-transaction-003",
            features=features,
        )
