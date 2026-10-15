from dataclasses import dataclass

from ml.src.decision.cost_matrix import Decision


@dataclass(frozen=True)
class DecisionPolicy:
    approve_threshold: float
    block_threshold: float

    def __post_init__(self):
        if not 0.0 <= self.approve_threshold <= 1.0:
            raise ValueError("approve_threshold must be between 0 and 1")

        if not 0.0 <= self.block_threshold <= 1.0:
            raise ValueError("block_threshold must be between 0 and 1")

        if self.approve_threshold >= self.block_threshold:
            raise ValueError(
                "approve_threshold must be lower than block_threshold"
            )

    def decide(self, fraud_probability: float) -> Decision:
        if not 0.0 <= fraud_probability <= 1.0:
            raise ValueError("fraud_probability must be between 0 and 1")

        if fraud_probability < self.approve_threshold:
            return Decision.APPROVE

        if fraud_probability >= self.block_threshold:
            return Decision.BLOCK

        return Decision.REVIEW