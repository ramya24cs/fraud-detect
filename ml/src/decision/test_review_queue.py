
import numpy as np
import pytest

from ml.src.decision.review_band import ReviewBand
from ml.src.decision.review_queue import build_review_queue


def test_unlimited_capacity_selects_all_candidates():
    probabilities = np.array([0.01, 0.10, 0.40, 0.80, 0.99])
    band = ReviewBand(lower=0.02, upper=0.98)

    result = build_review_queue(probabilities, band)

    assert result.total_candidates == 3
    assert result.selected_indices == [1, 2, 3]


def test_capacity_selects_highest_probability_candidates():
    probabilities = np.array([0.10, 0.80, 0.40, 0.70])
    band = ReviewBand(lower=0.02, upper=0.98, capacity=2)

    result = build_review_queue(probabilities, band)

    assert result.total_candidates == 4
    assert result.selected_indices == [1, 3]


def test_zero_capacity_selects_none():
    probabilities = np.array([0.10, 0.40, 0.80])
    band = ReviewBand(lower=0.02, upper=0.98, capacity=0)

    result = build_review_queue(probabilities, band)

    assert result.total_candidates == 3
    assert result.selected_indices == []


@pytest.mark.parametrize(
    "probabilities",
    [
        np.array([np.nan, 0.5]),
        np.array([np.inf, 0.5]),
        np.array([-np.inf, 0.5]),
        np.array([-0.1, 0.5]),
        np.array([0.5, 1.1]),
    ],
)
def test_invalid_probabilities_rejected(probabilities):
    band = ReviewBand(lower=0.02, upper=0.98)

    with pytest.raises(ValueError):
        build_review_queue(probabilities, band)
