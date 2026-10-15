# Member 1 ML Handoff

## 1. Project

Project: Cost-Sensitive Fraud Detection with Operator Feedback Loop

Member: Member 1 - Machine Learning

Primary dataset: ULB Credit Card Fraud Detection

Primary model: XGBoost

Model version: xgb-cost-v1

---

## 2. Final ML Model

Model file:

ml/models/xgboost_baseline.joblib

Preprocessor:

ml/models/preprocessor.joblib

Metadata:

ml/models/model_metadata.json

The XGBoost model was selected after comparing:

- Logistic Regression
- Decision Tree
- XGBoost

The final held-out test evaluation was performed only after model selection.

---

## 3. Stable Inference Interface

The ML inference interface is:

ml/src/models/inference.py

Main function:

```python
predict_fraud(transaction: dict) -> float
```

The function accepts one transaction and returns a fraud probability between 0 and 1.

Example:

```python
from models.inference import predict_fraud

probability = predict_fraud(transaction)
```

---

## 4. Required Input Features

The transaction dictionary must contain these features in the following order:

- Time
- V1
- V2
- V3
- V4
- V5
- V6
- V7
- V8
- V9
- V10
- V11
- V12
- V13
- V14
- V15
- V16
- V17
- V18
- V19
- V20
- V21
- V22
- V23
- V24
- V25
- V26
- V27
- V28
- Amount

The target column `Class` is not supplied during inference.

---

## 5. Preprocessing

The inference module automatically loads:

ml/models/preprocessor.joblib

The preprocessor is a StandardScaler fitted only on the training data.

Raw transaction features must be passed to `predict_fraud()`.

The caller should NOT manually scale the transaction before calling the function.

---

## 6. Output

The current ML interface returns only:

```text
fraud_probability
```

Example:

```text
0.9973905682563782
```

Interpretation:

- Probability close to 0: lower estimated fraud risk
- Probability close to 1: higher estimated fraud risk

The probability itself is the ML output.

---

## 7. Responsibilities of Member 2

Member 2 should consume the fraud probability produced by Member 1.

Member 2 owns:

- false-positive / false-negative cost matrix
- expected-cost calculation
- final threshold policy
- APPROVE / REVIEW / BLOCK decision logic
- review band
- review capacity
- SHAP explanation
- operator feedback processing
- feedback-driven retraining experiments
- final policy experiments

The Member 1 inference function should not be modified to contain these responsibilities.

---

## 8. Responsibilities of Member 3

Member 3 can integrate the ML inference interface into the backend.

The backend should:

1. Receive transaction data.
2. Pass the required features to `predict_fraud()`.
3. Receive the fraud probability.
4. Pass the probability to the appropriate decision/cost logic.
5. Return the final API response.

The backend should not duplicate model preprocessing or load a different model version.

---

## 9. Responsibilities of Member 4

The frontend should ultimately display the backend response.

The frontend should not directly load the `.joblib` model.

The frontend should consume the backend API response.

---

## 10. Frozen Prediction Contract

The intended final prediction response is:

```json
{
  "transaction_id": "TX-000001",
  "fraud_probability": 0.9132,
  "risk_level": "HIGH",
  "decision": "REVIEW",
  "expected_cost": 12.74,
  "model_version": "xgb-cost-v1",
  "explanation": [
    {
      "feature": "v14",
      "impact": 0.81
    },
    {
      "feature": "amount",
      "impact": 0.22
    }
  ]
}
```

Important:

Member 1 currently provides the `fraud_probability` and `model_version`.

The final `decision`, `expected_cost`, and `explanation` are produced by the other project components according to their assigned responsibilities.

---

## 11. Final Test Performance

The final XGBoost model was evaluated on the untouched chronological test set.

Test results at threshold 0.50:

- Precision: 0.812500
- Recall: 0.750000
- F1: 0.780000
- ROC-AUC: 0.978265
- PR-AUC: 0.768924

Confusion matrix:

- TN: 42660
- FP: 9
- FN: 13
- TP: 39

Preliminary cost experiment:

- FP cost: 5
- FN cost: 100
- Expected cost: 1345

The FP/FN costs are experimental cost units, not monetary values.

---

## 12. Preliminary Cost-Sensitive Result

On the validation set, a preliminary threshold experiment found tied minimum expected-cost thresholds:

- 0.042
- 0.043

At the refined policy:

- Expected cost: 980
- FP: 36
- FN: 8
- TP: 48
- TN: 42626
- Precision: 0.571429
- Recall: 0.857143
- F1: 0.685714

Compared with the XGBoost 0.50 validation baseline:

- Baseline expected cost: 1220
- Refined expected cost: 980
- Cost reduction: 240
- Relative reduction: 19.67%

This is a preliminary Member 1 research result.

The final production decision policy belongs to Member 2.

---

## 13. Calibration

A temporal isotonic calibration experiment was performed.

The calibrated model did not improve the validation Brier score.

Therefore:

- Raw XGBoost probabilities remain the primary ML output.
- The isotonic calibrated model is retained only as an experiment artifact.
- The calibrated model should not replace the primary model without further evidence.

---

## 14. Important Integration Rules

### Do

- Use `ml/src/models/inference.py`.
- Use `xgboost_baseline.joblib`.
- Use `preprocessor.joblib`.
- Preserve the required feature names.
- Preserve the feature order.
- Use the returned fraud probability.
- Preserve model version `xgb-cost-v1`.

### Do not

- Train another model inside the backend.
- Manually scale input before calling inference.
- Change the feature order.
- Add decision logic to `predict_fraud()`.
- Replace XGBoost with the calibration experiment model without evaluation.
- Treat the 0.042/0.043 threshold as the final production policy.
- Load the `.joblib` model directly from the frontend.

---

## 15. Verification

The inference interface was tested successfully.

Normal transaction:

```text
2.7644355213851668e-05
```

Fraud transaction:

```text
0.9973905682563782
```

This confirms that the model and preprocessing pipeline load correctly and produce valid fraud probabilities.

---

## 16. Member 1 Branch

Branch:

member1-ml

The branch contains the completed Member 1 ML implementation, research artifacts, model metadata, inference interface, and final ML report.

Before integration, other members should pull/merge the latest `member1-ml` branch rather than recreating the ML implementation independently.
