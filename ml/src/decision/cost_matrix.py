import math
from dataclasses import dataclass
from enum import Enum


class Decision(str, Enum):
    APPROVE = "APPROVE"
    REVIEW = "REVIEW"
    BLOCK = "BLOCK"


@dataclass(frozen=True)
class CostMatrix:
    review_cost: float
    block_friction_cost: float
    missed_fraud_cost: float
    residual_risk_cost: float
    block_cost: float

    def __post_init__(self):
        for name, value in vars(self).items():
            if not math.isfinite(value) or value < 0:
                raise ValueError(f"{name} must be a finite non-negative value")

    def expected_cost(self, fraud_probability: float, decision: Decision) -> float:
        if not math.isfinite(fraud_probability) or not 0.0 <= fraud_probability <= 1.0:
            raise ValueError("fraud_probability must be between 0 and 1")

        genuine_probability = 1.0 - fraud_probability

        if decision == Decision.APPROVE:
            return fraud_probability * self.missed_fraud_cost

        if decision == Decision.REVIEW:
            return (
                genuine_probability * self.review_cost
                + fraud_probability
                * (self.review_cost + self.residual_risk_cost)
            )

        if decision == Decision.BLOCK:
            return (
                genuine_probability * self.block_friction_cost
                + fraud_probability * self.block_cost
            )

        raise ValueError(f"Unsupported decision: {decision}")

    def select_decision(self, fraud_probability: float) -> Decision:
        """Choose the action with the lowest configured expected cost.

        Ties prefer REVIEW, then APPROVE, then BLOCK to avoid silently
        approving or blocking when the supplied costs are identical.
        """
        decisions = (Decision.REVIEW, Decision.APPROVE, Decision.BLOCK)
        return min(
            decisions,
            key=lambda decision: self.expected_cost(
                fraud_probability,
                decision,
            ),
        )