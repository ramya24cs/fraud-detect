"""Production decision defaults for the prediction pipeline.

Sources (committed project artifacts):
- ml/reports/policy_comparison_results.csv → optimized_three_way
- ml/reports/cost_sensitivity_results.csv → baseline_reference cost matrix

Live inference uses the approved cost matrix to select actions. The legacy
threshold policy remains available for evaluation, but is not used by
evaluate_transaction.
"""

from ml.src.decision.cost_matrix import CostMatrix
from ml.src.decision.policy import DecisionPolicy


# optimized_three_way policy (lowest expected cost vs binary baseline)
APPROVE_THRESHOLD = 0.02
BLOCK_THRESHOLD = 0.98


def approved_decision_policy() -> DecisionPolicy:
    return DecisionPolicy(
        approve_threshold=APPROVE_THRESHOLD,
        block_threshold=BLOCK_THRESHOLD,
    )


def approved_cost_matrix() -> CostMatrix:
    return CostMatrix(
        review_cost=2.0,
        block_friction_cost=5.0,
        missed_fraud_cost=100.0,
        residual_risk_cost=10.0,
        block_cost=20.0,
    )
