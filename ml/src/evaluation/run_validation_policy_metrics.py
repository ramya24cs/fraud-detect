import pandas as pd
import numpy as np

df = pd.read_csv("ml/reports/validation_predictions.csv")
y = df["actual_class"].to_numpy(dtype=int)
p = df["xgboost_probability"].to_numpy(dtype=float)

if len(y) == 0 or not np.isfinite(p).all():
    raise ValueError("Empty data or invalid probabilities")
if not np.isin(y, [0, 1]).all() or ((p < 0) | (p > 1)).any():
    raise ValueError("Invalid labels or probabilities")

fraud = y == 1
genuine = y == 0
n = len(y)

costs = {
    "review": 2.0,
    "block_genuine": 5.0,
    "missed_fraud": 100.0,
    "residual_risk": 10.0,
    "block_fraud": 20.0,
}

print(f"Validation rows: {n:,}")
print(f"Genuine: {genuine.sum():,} | Fraud: {fraud.sum():,}")

for name, approve_t, block_t in [
    ("Fixed threshold 0.50", 0.50, 0.50),
    ("Three-way 0.02/0.98", 0.02, 0.98),
]:
    approve = p < approve_t
    block = p >= block_t
    review = ~(approve | block)

    missed = int((approve & fraud).sum())
    reviewed_fraud = int((review & fraud).sum())
    blocked_fraud = int((block & fraud).sum())
    false_positives = int((block & genuine).sum())
    reviewed_genuine = int((review & genuine).sum())

    total_cost = (
        missed * costs["missed_fraud"]
        + reviewed_genuine * costs["review"]
        + reviewed_fraud * (costs["review"] + costs["residual_risk"])
        + false_positives * costs["block_genuine"]
        + blocked_fraud * costs["block_fraud"]
    )

    print(f"\n--- {name} ---")
    print(f"Approved: {approve.sum():,}")
    print(f"Reviewed: {review.sum():,} ({review.mean():.2%})")
    print(f"Blocked: {block.sum():,}")
    print(f"Missed fraud (approved): {missed}")
    print(f"Fraud sent to review: {reviewed_fraud}")
    print(f"Fraud blocked: {blocked_fraud}")
    print(f"False positives (genuine blocked): {false_positives}")
    print(f"Blocked-fraud precision: {blocked_fraud / block.sum():.4%}" if block.sum() else "Blocked-fraud precision: N/A")
    print(f"Blocked-fraud recall: {blocked_fraud / fraud.sum():.4%}" if fraud.sum() else "Blocked-fraud recall: N/A")
    print(f"Fraud caught or referred: {(blocked_fraud + reviewed_fraud) / fraud.sum():.4%}" if fraud.sum() else "Fraud caught or referred: N/A")
    print(f"Total expected cost: {total_cost:,.2f}")
    print(f"Cost per transaction: {total_cost / n:.4f}")

print("\nValidation-only results; no files overwritten.")
