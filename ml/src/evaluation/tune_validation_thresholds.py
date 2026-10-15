import pandas as pd
import numpy as np

INPUT = "ml/reports/validation_predictions.csv"
OUTPUT = "ml/reports/threshold_tuning_experiment.csv"

df = pd.read_csv(INPUT)
y = df["actual_class"].to_numpy(dtype=int)
p = df["xgboost_probability"].to_numpy(dtype=float)

if len(y) == 0 or not np.isfinite(p).all():
    raise ValueError("Empty data or invalid probabilities")
if not np.isin(y, [0, 1]).all() or ((p < 0) | (p > 1)).any():
    raise ValueError("Invalid labels or probabilities")

fraud = y == 1
genuine = ~fraud
n = len(y)

# Existing project cost assumptions
review_cost = 2.0
block_friction_cost = 5.0
missed_fraud_cost = 100.0
residual_risk_cost = 10.0
block_cost = 20.0

# Test threshold pairs; approve threshold must be below block threshold.
thresholds = np.unique(np.round(np.r_[
    np.arange(0.001, 0.101, 0.002),
    np.arange(0.10, 0.501, 0.01),
    np.arange(0.50, 1.00, 0.02),
    0.98, 0.99
], 6))
results = []

for a in thresholds:
    for b in thresholds:
        if a >= b:
            continue

        approve = p < a
        block = p >= b
        review = ~(approve | block)

        review_rate = review.mean()
        if review_rate > 0.01:
            continue

        missed = int((approve & fraud).sum())
        reviewed_fraud = int((review & fraud).sum())
        blocked_fraud = int((block & fraud).sum())
        false_positives = int((block & genuine).sum())
        reviewed_genuine = int((review & genuine).sum())

        cost = (
            missed * missed_fraud_cost
            + reviewed_genuine * review_cost
            + reviewed_fraud * (review_cost + residual_risk_cost)
            + false_positives * block_friction_cost
            + blocked_fraud * block_cost
        )

        results.append({
            "approve_threshold": float(a),
            "block_threshold": float(b),
            "total_cost": float(cost),
            "cost_per_transaction": float(cost / n),
            "missed_fraud": missed,
            "fraud_reviewed": reviewed_fraud,
            "fraud_blocked": blocked_fraud,
            "false_positives": false_positives,
            "review_count": int(review.sum()),
            "review_rate": float(review_rate),
            "fraud_referred_or_blocked": int(reviewed_fraud + blocked_fraud),
        })

out = pd.DataFrame(results)
if out.empty:
    raise RuntimeError("No threshold pair satisfies the review cap")

out = out.sort_values(
    ["total_cost", "missed_fraud", "review_count"],
    ascending=[True, True, True]
).reset_index(drop=True)

# Add the fixed baseline and current policy as reference rows.
def evaluate_reference(name, a, b):
    approve = p < a
    block = p >= b
    review = ~(approve | block)
    missed = int((approve & fraud).sum())
    rf = int((review & fraud).sum())
    bf = int((block & fraud).sum())
    fp = int((block & genuine).sum())
    rg = int((review & genuine).sum())
    cost = (
        missed * missed_fraud_cost
        + rg * review_cost
        + rf * (review_cost + residual_risk_cost)
        + fp * block_friction_cost
        + bf * block_cost
    )
    return {
        "policy": name, "approve_threshold": a, "block_threshold": b,
        "total_cost": cost, "cost_per_transaction": cost / n,
        "missed_fraud": missed, "fraud_reviewed": rf, "fraud_blocked": bf,
        "false_positives": fp, "review_count": int(review.sum()),
        "review_rate": float(review.mean()),
        "fraud_referred_or_blocked": rf + bf
    }

refs = pd.DataFrame([
    evaluate_reference("fixed_0.50", 0.50, 0.50),
    evaluate_reference("current_0.02_0.98", 0.02, 0.98),
])
out.insert(0, "policy", "tuned_candidate")
out = pd.concat([refs, out], ignore_index=True)
out.to_csv(OUTPUT, index=False)

print("Top 10 threshold pairs by configured cost (review rate <= 1%):")
print(out[out["policy"] == "tuned_candidate"].head(10).to_string(index=False))
print("\nReference policies:")
print(refs.to_string(index=False))
print(f"\nSaved {len(out)} rows to {OUTPUT}")
