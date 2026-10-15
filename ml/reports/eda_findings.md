# Exploratory Data Analysis Findings

## 1. Dataset Overview

The ULB Credit Card Fraud Detection dataset contains 284,807 transactions and 31 columns, including 30 input features and the binary target variable `Class`.

- Total transactions: 284,807
- Legitimate transactions: 284,315
- Fraudulent transactions: 492
- Fraud rate: 0.1727%
- Missing values: 0

The dataset is therefore highly imbalanced, with fraudulent transactions representing only a very small proportion of the total observations.

## 2. Class Imbalance

The class distribution shows that approximately 99.83% of transactions are legitimate and only 0.17% are fraudulent.

This severe class imbalance makes accuracy an unsuitable primary evaluation metric. Precision, recall, F1-score, PR-AUC, ROC-AUC, confusion matrix, and expected fraud cost are therefore considered in the model evaluation.

## 3. Transaction Amount Distribution

Transaction amounts are strongly right-skewed.

- Mean amount: 88.35
- Median amount: 22.00
- Maximum amount: 25,691.16

The large difference between the mean and median indicates the presence of high-value transactions.

## 4. Transaction Amount by Class

The average transaction amount for fraudulent transactions is higher than that of legitimate transactions:

- Legitimate mean: 88.29
- Fraud mean: 122.21

However, the median fraud amount is lower:

- Legitimate median: 22.00
- Fraud median: 9.25

Therefore, fraud cannot be characterized simply as involving higher transaction amounts. The distribution is highly variable, and transaction amount should be considered together with other features.

## 5. Fraud Transactions Over Time

Fraudulent transactions occur throughout the observed time period, with noticeable variation in their distribution.

The `Time` feature represents elapsed time from the beginning of the dataset rather than a real-world calendar timestamp.

The observed temporal variation supports evaluating the models using a chronological train-validation-test split to reduce the risk of using future observations to predict earlier observations.

## 6. Fraud Rate Over Time

The fraud rate varies across the 20 time bins, approximately ranging from 0.03% to 0.70%.

This indicates that the prevalence of fraud is not completely constant throughout the dataset.

The temporal variation provides additional justification for using a chronological split rather than relying only on a random split.

## 7. Feature-Level Class Separation

The difference between legitimate and fraudulent transaction means was calculated for each anonymized feature.

The largest absolute mean differences were observed for:

| Feature | Absolute Mean Difference |
|---|---:|
| V3 | 7.045 |
| V14 | 6.984 |
| V17 | 6.677 |
| V12 | 6.270 |
| V10 | 5.687 |
| V7 | 5.578 |
| V1 | 4.780 |
| V4 | 4.550 |
| V16 | 4.147 |
| V11 | 3.807 |

V3, V14, V17, V12, and V10 show strong univariate separation between the two classes.

This analysis represents class-level mean separation and should not be interpreted as model feature importance. Features with small mean differences may still provide useful information to nonlinear models such as XGBoost.

## 8. Duplicate Analysis

The dataset contains repeated rows.

A total of 1,081 duplicate occurrences were identified, corresponding to 1,854 rows belonging to repeated groups when all members of duplicate groups are counted.

No duplicate groups were found with conflicting target labels.

Importantly, no identical feature rows were found across the train-validation, train-test, or validation-test splits after the chronological split.

Therefore, duplicate transactions were retained rather than blindly removed, while the absence of cross-split duplicate rows was documented as a leakage check.

## 9. EDA Conclusion

The ULB dataset presents three important characteristics relevant to fraud detection:

1. Severe class imbalance.
2. Temporal variation in fraud occurrence.
3. Different distributions between legitimate and fraudulent transactions.

These characteristics motivate the use of imbalance-aware learning, chronological evaluation, probability-based fraud detection, and cost-sensitive decision analysis.

The EDA findings support the subsequent development of Logistic Regression, Decision Tree, and XGBoost baseline models and the evaluation of fraud detection using precision, recall, F1-score, PR-AUC, ROC-AUC, confusion matrices, and expected cost.