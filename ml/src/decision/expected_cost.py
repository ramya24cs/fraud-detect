from ml.src.decision.cost_matrix import CostMatrix, Decision


def calculate_expected_cost(
    fraud_probability: float,
    decision: Decision,
    cost_matrix: CostMatrix,
) -> float:
    return cost_matrix.expected_cost(
        fraud_probability=fraud_probability,
        decision=decision,
    )