# Member 1 — Model Selection Decision

## Project

Cost-Sensitive Fraud Detection with Operator Feedback Loop

## Dataset

ULB Credit Card Fraud Detection Dataset

## Data Split

A chronological 70/15/15 split was used:

* Training set: 199,368 transactions
* Validation set: 42,718 transactions
* Test set: 42,721 transactions

The test set remains untouched during model selection and threshold experiments.

## Candidate Models

Three baseline classifiers were evaluated:

1. Logistic Regression
2. Decision Tree
3. XGBoost

All models were trained using the leakage-safe preprocessing pipeline.

## Validation Results

|Model|Threshold|Precision|Recall|F1|ROC-AUC|PR-AUC|FP|FN|
|-|-:|-:|-:|-:|-:|-:|-:|-:|
|Logistic Regression|0.50|0.053170|0.928571|0.100580|0.982786|0.839335|926|4|
|Decision Tree|0.50|0.030856|0.785714|0.059379|0.818286|0.361544|1382|12|
|XGBoost|0.50|0.916667|0.785714|0.846154|0.990778|0.858069|4|12|

## Model Selection

XGBoost was selected as the primary Member-1 model.

The main reasons are:

* Highest ROC-AUC among the evaluated models.
* Highest PR-AUC among the evaluated models.
* Highest F1 score.
* Very high precision.
* Only 4 false positives at the default 0.50 threshold.
* Strong performance under the severe class imbalance of the ULB dataset.

Logistic Regression achieved higher recall and fewer false negatives, but produced 926 false positives. This makes it less suitable for an operator-facing fraud detection system where excessive false alerts can increase manual review workload.

The Decision Tree produced substantially weaker overall performance.

## Preliminary Cost-Sensitive Experiment

A preliminary threshold experiment was performed using assumed costs:

* False Positive Cost = 5 cost units
* False Negative Cost = 100 cost units

These values are experimental assumptions for Member-1 analysis and are not the final production cost matrix.

At threshold 0.50:

* False positives = 4
* False negatives = 12
* Expected cost = 1220 cost units

A coarse threshold search identified threshold 0.04 with:

* False positives = 38
* False negatives = 8
* Expected cost = 990 cost units

A subsequent refined search over the region around the optimum identified a minimum expected cost of 980 cost units at thresholds 0.042–0.043.

Compared with the 0.50 threshold:

* Expected cost decreased from 1220 to 980.
* Reduction = 240 cost units.
* Relative reduction = approximately 19.67%.

The 0.042–0.043 result is a preliminary research experiment. Final cost values, threshold optimization, review-band policy, and three-way decision policy are owned by Member 2 according to the project architecture.

## Calibration Experiment

Raw XGBoost probabilities were also evaluated for calibration.

A temporal isotonic calibration experiment was performed using an internal calibration subset of the training data.

Results:

* Raw XGBoost Brier score: 0.00030693
* Isotonic calibrated Brier score: 0.00033157

The calibrated model did not improve the Brier score in this experiment. Therefore, raw XGBoost probabilities are retained as the primary probability output.

The calibration subset contained only 24 fraud cases, so this result should be treated as an experimental finding rather than definitive evidence that calibration cannot improve the model.

## Final Member-1 Decision

For the remaining Member-1 experiments, XGBoost is the primary model.

The untouched test set must not be used until:

1. Model selection is finalized.
2. Preprocessing decisions are finalized.
3. Cost-policy decisions are finalized with Member 2.
4. Threshold selection is finalized.
5. Any required calibration decision is finalized.

After these decisions are frozen, the test set will be used once for final unbiased evaluation.

## Research Interpretation

The validation experiments indicate that model choice alone is insufficient for the fraud detection problem.

XGBoost provides strong discrimination and precision, while the preliminary threshold experiment demonstrates that changing the decision threshold according to asymmetric fraud costs can substantially change the false-positive/false-negative trade-off.

This supports the central research direction of combining:

* strong fraud probability estimation,
* asymmetric cost-sensitive decision making,
* operator review,
* and subsequent operator feedback.

The final cost-sensitive policy and feedback-loop experiments will be integrated according to the shared Member-1/Member-2 contracts defined in the project master plan.
