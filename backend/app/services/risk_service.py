from __future__ import annotations

import math

from backend.app.core.config import settings


def classify_risk(
    probability: float,
    *,
    low_threshold: float | None = None,
    high_threshold: float | None = None,
) -> str:
    """Classify a fraud probability into LOW, MEDIUM, or HIGH risk.

    Thresholds are kept separate from the cost-sensitive decision logic and are
    configurable via environment variables. They are provisional defaults and
    should be recalibrated against validation data before production use.
    """
    try:
        probability_value = float(probability)
    except (TypeError, ValueError) as exc:
        raise ValueError("Probability must be a finite numeric value.") from exc

    if not math.isfinite(probability_value):
        raise ValueError("Probability must be a finite numeric value.")
    if probability_value < 0.0 or probability_value > 1.0:
        raise ValueError("Probability must be between 0.0 and 1.0.")

    lower_bound = (
        settings.RISK_LOW_THRESHOLD if low_threshold is None else low_threshold
    )
    upper_bound = (
        settings.RISK_HIGH_THRESHOLD if high_threshold is None else high_threshold
    )

    lower_bound = float(lower_bound)
    upper_bound = float(upper_bound)

    if not 0.0 <= lower_bound <= 1.0:
        raise ValueError("low_threshold must be between 0.0 and 1.0.")
    if not 0.0 <= upper_bound <= 1.0:
        raise ValueError("high_threshold must be between 0.0 and 1.0.")
    if lower_bound >= upper_bound:
        raise ValueError(
            "low_threshold must be lower than high_threshold."
        )

    if probability_value < lower_bound:
        return "LOW"
    if probability_value >= upper_bound:
        return "HIGH"
    return "MEDIUM"
