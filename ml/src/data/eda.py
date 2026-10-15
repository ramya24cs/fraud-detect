import pandas as pd
from pathlib import Path


# ---------------------------------------------------------
# Paths
# ---------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_PATH = PROJECT_ROOT / "ml" / "data" / "creditcard.csv"


# ---------------------------------------------------------
# Load dataset
# ---------------------------------------------------------
print("=" * 60)
print("COST-SENSITIVE FRAUD DETECTION")
print("ULB CREDIT CARD FRAUD DATASET - EDA")
print("=" * 60)

df = pd.read_csv(DATA_PATH)


# ---------------------------------------------------------
# 1. Dataset shape
# ---------------------------------------------------------
print("\n1. DATASET SHAPE")
print("-" * 60)
print(f"Rows    : {df.shape[0]}")
print(f"Columns : {df.shape[1]}")


# ---------------------------------------------------------
# 2. Column information
# ---------------------------------------------------------
print("\n2. COLUMNS")
print("-" * 60)

for column in df.columns:
    print(column)


# ---------------------------------------------------------
# 3. Data types
# ---------------------------------------------------------
print("\n3. DATA TYPES")
print("-" * 60)
print(df.dtypes)


# ---------------------------------------------------------
# 4. Missing values
# ---------------------------------------------------------
print("\n4. MISSING VALUES")
print("-" * 60)

missing_values = df.isnull().sum()

print(missing_values[missing_values > 0])

if missing_values.sum() == 0:
    print("No missing values found.")


# ---------------------------------------------------------
# 5. Duplicate transactions
# ---------------------------------------------------------
print("\n5. DUPLICATES")
print("-" * 60)

duplicate_count = df.duplicated().sum()

print(f"Duplicate rows: {duplicate_count}")


# ---------------------------------------------------------
# 6. Class distribution
# ---------------------------------------------------------
print("\n6. CLASS DISTRIBUTION")
print("-" * 60)

class_counts = df["Class"].value_counts()
class_percentages = df["Class"].value_counts(normalize=True) * 100

print("Counts:")
print(class_counts)

print("\nPercentages:")
print(class_percentages)


# ---------------------------------------------------------
# 7. Fraud ratio
# ---------------------------------------------------------
print("\n7. FRAUD RATE")
print("-" * 60)

fraud_count = (df["Class"] == 1).sum()
total_count = len(df)

fraud_rate = (fraud_count / total_count) * 100

print(f"Fraud transactions : {fraud_count}")
print(f"Total transactions : {total_count}")
print(f"Fraud rate         : {fraud_rate:.4f}%")
print(f"Legitimate rate    : {100 - fraud_rate:.4f}%")


# ---------------------------------------------------------
# 8. Transaction amount statistics
# ---------------------------------------------------------
print("\n8. TRANSACTION AMOUNT")
print("-" * 60)

print(df["Amount"].describe())


# ---------------------------------------------------------
# 9. Amount by class
# ---------------------------------------------------------
print("\n9. TRANSACTION AMOUNT BY CLASS")
print("-" * 60)

amount_by_class = df.groupby("Class")["Amount"].describe()

print(amount_by_class)


# ---------------------------------------------------------
# 10. Time statistics
# ---------------------------------------------------------
print("\n10. TIME FEATURE")
print("-" * 60)

print(df["Time"].describe())


# ---------------------------------------------------------
# 11. Feature ranges
# ---------------------------------------------------------
print("\n11. FEATURE RANGES")
print("-" * 60)

numeric_columns = df.select_dtypes(include="number").columns

feature_ranges = pd.DataFrame({
    "minimum": df[numeric_columns].min(),
    "maximum": df[numeric_columns].max(),
    "mean": df[numeric_columns].mean(),
    "std": df[numeric_columns].std()
})

print(feature_ranges)


# ---------------------------------------------------------
# 12. Class-specific feature statistics
# ---------------------------------------------------------
print("\n12. FEATURE STATISTICS BY CLASS")
print("-" * 60)

print(
    df.groupby("Class")[["Amount"]].mean()
)


# ---------------------------------------------------------
# 13. Final validation
# ---------------------------------------------------------
print("\n13. FINAL VALIDATION")
print("-" * 60)

print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns)}")
print(f"Missing values: {df.isnull().sum().sum()}")
print(f"Duplicate rows: {df.duplicated().sum()}")
print(f"Fraud cases: {(df['Class'] == 1).sum()}")
print(f"Legitimate cases: {(df['Class'] == 0).sum()}")

print("\nEDA completed successfully.")