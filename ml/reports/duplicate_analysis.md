\# Duplicate Transaction Analysis



\## Dataset



Dataset: ULB Credit Card Fraud Detection Dataset



The dataset contains 284,807 transactions with 30 input features and one target variable (`Class`).



\## Duplicate Analysis



The original dataset contains repeated rows.



\- Total duplicate occurrences identified using all columns: 1,081

\- Rows belonging to duplicate groups when `keep=False`: 1,854

\- Duplicate groups: 773

\- Duplicate rows with Class=0: 1,822

\- Duplicate rows with Class=1: 32

\- Duplicate groups containing conflicting Class labels: 0



\## Cross-Split Leakage Check



The dataset was split chronologically into training, validation, and test sets.



Duplicate feature rows were checked across the three splits while excluding the target column (`Class`).



Results:



| Split Pair | Duplicate Feature Rows |

|---|---:|

| Train vs Validation | 0 |

| Train vs Test | 0 |

| Validation vs Test | 0 |



\## Decision



The duplicate transactions were not removed from the dataset.



The main reason is that duplicate rows do not cross the train/validation/test boundaries. Therefore, they do not introduce duplicate-row leakage between evaluation splits.



Removing duplicates would also unnecessarily modify the original dataset distribution.



The duplicates are therefore retained, while their presence and the cross-split leakage check are explicitly documented.



\## Research Interpretation



The chronological train/validation/test split contains no duplicated feature rows shared between different splits. Therefore, the reported validation and test results are not affected by direct duplicate-row overlap across evaluation boundaries.



This analysis does not imply that the dataset is free from all forms of temporal or distributional dependence. It only establishes that exact duplicate feature rows do not cross the three evaluation splits.
