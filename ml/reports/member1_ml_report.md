# Member 1 - Machine Learning Report

## 1. Project

**Project:** Cost-Sensitive Fraud Detection with Operator Feedback Loop

**Member:** Member 1 - Machine Learning

**Primary Dataset:** ULB Credit Card Fraud Detection Dataset

---

## 2. Dataset

The ULB Credit Card Fraud Detection dataset contains 284,807 credit-card transactions.

The target variable is `Class`:

- `0` - legitimate transaction
- `1` - fraudulent transaction

### Class distribution

| Class | Count | Percentage |
|---|---:|---:|
| Legitimate | 284,315 | 99.8273% |
| Fraud | 492 | 0.1727% |
| Total | 284,807 | 100% |

The dataset therefore exhibits severe class imbalance.

The input features are:

- `Time`
- `V1` to `V28`
- `Amount`

The target is:

- `Class`

---

## 3. Data Quality and Duplicate Analysis

The dataset contains 1,081 repeated duplicate occurrences.

When all members of duplicate groups are counted, 1,854 rows belong to duplicate groups.

There are 773 unique duplicate groups.

No duplicate group was found with conflicting `Class` labels.

The duplicate transactions were retained because they represent observations present in the original dataset and no conflicting labels were identified.

A cross-split duplicate check was also performed using the feature columns excluding `Class`.

No feature-identical rows were found across:

- train and validation
- train and test
- validation and test

Therefore, no cross-split duplicate leakage was detected.

---

## 4. Data Splitting Strategy

A chronological split was used instead of a random split.

This better represents a realistic fraud-detection scenario where a model is trained on earlier transactions and evaluated on later transactions.

### Split

| Split | Rows | Fraud cases |
|---|---:|---:|
| Training | 199,368 | 384 |
| Validation | 42,718 | 56 |
| Test | 42,721 | 52 |

The test set was kept untouched during model selection and threshold experimentation.

Time ranges:

- Training: `0.0` to `132929.0`
- Validation: `132930.0` to `151328.0`
- Test: `151329.0` to `172792.0`

All 284,807 rows were accounted for.

---

## 5. Preprocessing

The selected input features were:

`Time`, `V1` to `V28`, and `Amount`.

A `StandardScaler` was used.

The scaler was fitted only on the training data and then used to transform validation and test data.

This prevents information from the validation or test sets from influencing preprocessing.

The saved preprocessing artifact is:

```text
ml/models/preprocessor.joblib
```

Processed datasets:

```text
ml/data/train_processed.csv
ml/data/validation_processed.csv
ml/data/test_processed.csv
```

---

## 6. Exploratory Data Analysis

The following research EDA artifacts were generated:

```text
ml/reports/eda_class_distribution.png
ml/reports/eda_amount_distribution.png
ml/reports/eda_amount_by_class.png
ml/reports/eda_fraud_over_time.png
ml/reports/eda_fraud_rate_over_time.png
```

Important findings:

- Fraud represents only 0.1727% of all transactions.
- The transaction amount has a mean of approximately 88.35 and median of 22.00.
- Fraud transactions have a mean amount of approximately 122.21 and median of 9.25.
- Fraud transaction amounts range up to approximately 2,125.87.
- Fraud transactions occur across the time range rather than being restricted to one period.
- Fraud rates across 20 time bins vary approximately from 0.03% to 0.70%.

The largest mean absolute class separations were observed for:

| Feature | Mean separation |
|---|---:|
| V3 | 7.045452 |
| V14 | 6.983787 |
| V17 | 6.677371 |
| V12 | 6.270225 |
| V10 | 5.686707 |
| V7 | 5.578368 |
| V1 | 4.780206 |
| V4 | 4.549889 |
| V16 | 4.147110 |
| V11 | 3.806749 |

These values describe class separation and should not be interpreted as model feature importance.

---

## 7. Baseline Model Comparison

Three baseline models were trained using the training data and evaluated on the validation set.

### Logistic Regression

Configuration:

```text
class_weight = balanced
max_iter = 1000
random_state = 42
```

Validation results:

| Metric | Value |
|---|---:|
| Precision | 0.053170 |
| Recall | 0.928571 |
| F1 | 0.100580 |
| ROC-AUC | 0.982786 |
| PR-AUC | 0.839335 |
| TN | 41,736 |
| FP | 926 |
| FN | 4 |
| TP | 52 |

Artifact:

```text
ml/models/logistic_regression_baseline.joblib
```

### Decision Tree

Configuration:

```text
class_weight = balanced
max_depth = 6
min_samples_leaf = 10
random_state = 42
```

Validation results:

| Metric | Value |
|---|---:|
| Precision | 0.030856 |
| Recall | 0.785714 |
| F1 | 0.059379 |
| ROC-AUC | 0.818286 |
| PR-AUC | 0.361544 |
| TN | 41,280 |
| FP | 1,382 |
| FN | 12 |
| TP | 44 |

Artifact:

```text
ml/models/decision_tree_baseline.joblib
```

### XGBoost

The XGBoost model used class weighting through `scale_pos_weight`.

```text
scale_pos_weight = 518.1875
```

Configuration:

```text
n_estimators = 300
max_depth = 6
learning_rate = 0.05
subsample = 0.8
colsample_bytree = 0.8
objective = binary:logistic
eval_metric = logloss
random_state = 42
n_jobs = -1
```

Validation results:

| Metric | Value |
|---|---:|
| Precision | 0.916667 |
| Recall | 0.785714 |
| F1 | 0.846154 |
| ROC-AUC | 0.990778 |
| PR-AUC | 0.858069 |
| TN | 42,658 |
| FP | 4 |
| FN | 12 |
| TP | 44 |

Artifact:

```text
ml/models/xgboost_baseline.joblib
```

XGBoost was selected as the primary Member 1 model because it achieved the strongest overall validation performance, including the highest PR-AUC and ROC-AUC among the tested models while maintaining very high precision.

---

## 8. Cost-Sensitive Threshold Experiment

A preliminary validation-only threshold experiment was performed using the following cost assumptions:

```text
False Positive Cost = 5
False Negative Cost = 100
```

These values are cost units, not monetary values.

The purpose of this experiment was to study how the classification threshold affects expected cost.

The refined search identified a tied minimum around:

```text
0.042 - 0.043
```

At the refined threshold:

| Metric | Value |
|---|---:|
| Expected cost | 980 |
| FP | 36 |
| FN | 8 |
| TP | 48 |
| TN | 42,626 |
| Precision | 0.571429 |
| Recall | 0.857143 |
| F1 | 0.685714 |

At the conventional XGBoost threshold of 0.50:

| Metric | Value |
|---|---:|
| Expected cost | 1,220 |
| FP | 4 |
| FN | 12 |
| TP | 44 |
| TN | 42,658 |
| Precision | 0.916667 |
| Recall | 0.785714 |
| F1 | 0.846154 |

The refined threshold reduced validation expected cost by 240 cost units, approximately 19.67%.

This is a preliminary Member 1 research experiment.

The final production decision policy, cost matrix implementation, review band, and threshold policy are owned by Member 2.

---

## 9. Calibration Experiment

A temporal calibration experiment was performed.

The original training portion was divided into:

- Model-training subset: 169,462 rows with 360 fraud cases
- Calibration subset: 29,906 rows with 24 fraud cases

Isotonic calibration was evaluated on the later validation set.

Results:

| Model | Brier Score |
|---|---:|
| Raw XGBoost | 0.00030693 |
| Isotonic calibrated XGBoost | 0.00033157 |

The isotonic calibration increased the Brier score by approximately 8.03%.

Because the calibration subset contained only 24 fraud cases and calibration did not improve the Brier score, the raw XGBoost probabilities were retained as the primary model output.

Calibration artifact:

```text
ml/models/xgboost_isotonic_calibrated.joblib
```

This artifact is retained for research comparison and is not the primary production model.

---

## 10. Stable ML Inference Interface

A stable model-side inference function was implemented:

```text
ml/src/models/inference.py
```

The function accepts a transaction dictionary containing:

```text
Time
V1 - V28
Amount
```

and returns:

```text
fraud_probability
```

The inference module loads:

```text
ml/models/xgboost_baseline.joblib
ml/models/preprocessor.joblib
```

The same training preprocessing is applied before prediction.

Inference was tested using both a legitimate and a fraudulent validation transaction.

Example results:

```text
Normal transaction probability:
0.0000276444

Fraud transaction probability:
0.9973905683
```

This confirms that the model-side probability inference is functioning correctly.

---

## 11. Model Metadata

The reproducibility metadata is stored in:

```text
ml/models/model_metadata.json
```

The metadata records:

- model version
- model type
- dataset
- target
- input features
- preprocessing method
- chronological split
- imbalance handling
- XGBoost parameters
- inference output

The model version is:

```text
xgb-cost-v1
```

---

## 12. Final Held-Out Test Evaluation

After model selection and validation experiments were completed, the untouched chronological test set was evaluated once using the selected raw XGBoost model at the conventional threshold of 0.50.

### Final test results

| Metric | Value |
|---|---:|
| Precision | 0.812500 |
| Recall | 0.750000 |
| F1 | 0.780000 |
| ROC-AUC | 0.978265 |
| PR-AUC | 0.768924 |
| TN | 42,660 |
| FP | 9 |
| FN | 13 |
| TP | 39 |

Using the preliminary research cost assumptions:

```text
FP Cost = 5
FN Cost = 100
```

the test expected cost is:

```text
1345
```

The test set was not used for model selection, threshold tuning, or calibration decisions.

Final test results are stored in:

```text
ml/reports/final_test_results.csv
```

---

## 13. Research Artifacts

The following research artifacts were generated:

```text
ml/reports/model_comparison_validation.csv
ml/reports/cost_policy_comparison.csv
ml/reports/refined_threshold_analysis.csv
ml/reports/validation_predictions.csv
ml/reports/temporal_calibration_results.csv
ml/reports/final_test_results.csv
```

Research figures include:

```text
ml/reports/expected_cost_vs_threshold.png
ml/reports/precision_recall_vs_threshold.png
```

---

## 14. Model Selection Decision

The final Member 1 model is:

```text
XGBoost
```

with:

```text
ml/models/xgboost_baseline.joblib
```

The model uses:

- chronological train/validation/test splitting
- leakage-safe preprocessing
- class imbalance handling
- validation-based model comparison
- cost-sensitive threshold analysis
- calibration analysis
- reproducible inference
- model metadata

The raw XGBoost probability output is retained as the primary model probability.

The final production decision logic is intentionally separated from the model probability and belongs to the decision layer.

---

## 15. Member 1 Contribution to the Research Project

Member 1 provides the machine-learning foundation for the complete system:

1. Dataset validation and documentation
2. Exploratory data analysis
3. Leakage-safe preprocessing
4. Chronological data splitting
5. Baseline model comparison
6. XGBoost model training
7. Class-imbalance handling
8. Validation and held-out test evaluation
9. Preliminary cost-sensitive threshold analysis
10. Calibration analysis
11. Stable probability inference
12. Model metadata and reproducibility artifacts
13. Research figures and comparison tables

The operator feedback loop, final decision policy, SHAP explanation service, review workflow, and feedback-driven retraining pipeline are integrated by the other project members according to the project architecture.

---

## 16. Research Interpretation

The experiments show that severe class imbalance makes conventional accuracy unsuitable as the primary evaluation criterion.

The selected XGBoost model achieved strong validation performance and maintained strong performance on the untouched chronological test set.

The preliminary cost-sensitive experiment demonstrates that changing the decision threshold can substantially reduce expected business cost when false negatives are more expensive than false positives.

The calibration experiment did not improve probability quality under the available temporal calibration data, so raw XGBoost probabilities were retained.

The complete system can subsequently use operator feedback to collect reviewed transaction outcomes and support future model improvement while preserving the separation between probability estimation and production decision policy.
