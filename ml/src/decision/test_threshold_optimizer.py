import numpy as np
import pytest
from ml.src.decision.cost_matrix import CostMatrix
from ml.src.decision.threshold_optimizer import optimize_threshold


def test_optimize_threshold():
    probabilities = np.array([0.01, 0.10, 0.40, 0.80, 0.95])
    labels = np.array([0, 0, 1, 1, 1])

    cost_matrix = CostMatrix(
        review_cost=2.0,
        block_friction_cost=5.0,
        missed_fraud_cost=100.0,
        residual_risk_cost=10.0,
        block_cost=20.0,
    )

    result = optimize_threshold(
        fraud_probabilities=probabilities,
        actual_labels=labels,
        cost_matrix=cost_matrix,
        thresholds=np.array([0.2, 0.5, 0.7]),
    )

    assert result.approve_threshold == 0.2
    assert result.block_threshold == 0.5
    assert result.expected_cost == 52.0
    assert result.decisions["APPROVE"] == 2
    assert result.decisions["REVIEW"] == 1
    assert result.decisions["BLOCK"] == 2
    assert result.review_rate == 0.2


def test_max_review_rate():
    probabilities = np.array([0.01, 0.10, 0.40, 0.80, 0.95])
    labels = np.array([0, 0, 1, 1, 1])

    cost_matrix = CostMatrix(
        review_cost=2.0,
        block_friction_cost=5.0,
        missed_fraud_cost=100.0,
        residual_risk_cost=10.0,
        block_cost=20.0,
    )

    result = optimize_threshold(
        fraud_probabilities=probabilities,
        actual_labels=labels,
        cost_matrix=cost_matrix,
        thresholds=np.array([0.2, 0.5, 0.7]),
        max_review_rate=0.2,
    )

    assert result.review_rate <= 0.2


def test_invalid_probabilities():
    probabilities = np.array([0.1, 1.2])
    labels = np.array([0, 1])

    cost_matrix = CostMatrix(
        review_cost=2.0,
        block_friction_cost=5.0,
        missed_fraud_cost=100.0,
        residual_risk_cost=10.0,
        block_cost=20.0,
    )

    with pytest.raises(ValueError):
        optimize_threshold(
            fraud_probabilities=probabilities,
            actual_labels=labels,
            cost_matrix=cost_matrix,
        )


def test_invalid_labels():
    probabilities = np.array([0.1, 0.8])
    labels = np.array([0, 2])

    cost_matrix = CostMatrix(
        review_cost=2.0,
        block_friction_cost=5.0,
        missed_fraud_cost=100.0,
        residual_risk_cost=10.0,
        block_cost=20.0,
    )

    with pytest.raises(ValueError):
        optimize_threshold(
            fraud_probabilities=probabilities,
            actual_labels=labels,
            cost_matrix=cost_matrix,
        )


def test_empty_input():
    probabilities = np.array([])
    labels = np.array([])

    cost_matrix = CostMatrix(
        review_cost=2.0,
        block_friction_cost=5.0,
        missed_fraud_cost=100.0,
        residual_risk_cost=10.0,
        block_cost=20.0,
    )

    with pytest.raises(ValueError):
        optimize_threshold(
            fraud_probabilities=probabilities,
            actual_labels=labels,
            cost_matrix=cost_matrix,
        )

print('All threshold optimizer tests passed')

def make_cost_matrix():
    return CostMatrix(
        review_cost=2.0,
        block_friction_cost=5.0,
        missed_fraud_cost=100.0,
        residual_risk_cost=10.0,
        block_cost=20.0,
    )


@pytest.mark.parametrize(
    "probabilities",
    [
        np.array([np.nan, 0.8]),
        np.array([np.inf, 0.8]),
        np.array([-np.inf, 0.8]),
    ],
)
def test_non_finite_probabilities_rejected(probabilities):
    with pytest.raises(ValueError):
        optimize_threshold(
            fraud_probabilities=probabilities,
            actual_labels=np.array([0, 1]),
            cost_matrix=make_cost_matrix(),
        )


@pytest.mark.parametrize(
    "labels",
    [
        np.array([0.8, 1.0]),
        np.array([0, np.nan]),
        np.array([0, np.inf]),
        np.array([0, 2]),
    ],
)
def test_invalid_or_non_finite_labels_rejected(labels):
    with pytest.raises(ValueError):
        optimize_threshold(
            fraud_probabilities=np.array([0.1, 0.8]),
            actual_labels=labels,
            cost_matrix=make_cost_matrix(),
        )


@pytest.mark.parametrize(
    "thresholds",
    [
        np.array([]),
        np.array([[0.2, 0.5]]),
        np.array([np.nan, 0.5]),
        np.array([0.2, np.inf]),
        np.array([0.0, 0.5]),
        np.array([0.2, 1.0]),
    ],
)
def test_invalid_threshold_grids_rejected(thresholds):
    with pytest.raises(ValueError):
        optimize_threshold(
            fraud_probabilities=np.array([0.1, 0.8]),
            actual_labels=np.array([0, 1]),
            cost_matrix=make_cost_matrix(),
            thresholds=thresholds,
        )


@pytest.mark.parametrize("review_rate", [-0.1, 1.1, np.nan, np.inf])
def test_invalid_max_review_rate_rejected(review_rate):
    with pytest.raises(ValueError):
        optimize_threshold(
            fraud_probabilities=np.array([0.1, 0.8]),
            actual_labels=np.array([0, 1]),
            cost_matrix=make_cost_matrix(),
            max_review_rate=review_rate,
        )
