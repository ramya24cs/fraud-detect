import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


# =========================================================
# Paths
# =========================================================
PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_PATH = PROJECT_ROOT / "ml" / "data" / "creditcard.csv"
REPORTS_DIR = PROJECT_ROOT / "ml" / "reports"

REPORTS_DIR.mkdir(parents=True, exist_ok=True)


# =========================================================
# Load dataset
# =========================================================
df = pd.read_csv(DATA_PATH)

print("=" * 60)
print("COST-SENSITIVE FRAUD DETECTION")
print("RESEARCH-ORIENTED EDA")
print("=" * 60)


# =========================================================
# 1. Class distribution
# =========================================================
class_counts = df["Class"].value_counts().sort_index()

print("\n1. CLASS DISTRIBUTION")
print("-" * 60)
print(class_counts)

print("\nClass percentages:")
print((class_counts / len(df) * 100).round(4))


# Save class distribution
class_distribution = pd.DataFrame({
    "class": class_counts.index,
    "count": class_counts.values,
    "percentage": (class_counts.values / len(df)) * 100
})

class_distribution.to_csv(
    REPORTS_DIR / "eda_class_distribution.csv",
    index=False
)


# =========================================================
# 2. Class distribution plot
# =========================================================
plt.figure(figsize=(7, 5))

plt.bar(
    ["Legitimate", "Fraud"],
    class_counts.values
)

plt.title("Class Distribution")
plt.xlabel("Transaction Class")
plt.ylabel("Number of Transactions")

plt.tight_layout()

plt.savefig(
    REPORTS_DIR / "eda_class_distribution.png",
    dpi=300
)

plt.close()


# =========================================================
# 3. Transaction amount distribution
# =========================================================
print("\n2. TRANSACTION AMOUNT")
print("-" * 60)
print(df["Amount"].describe())


plt.figure(figsize=(8, 5))

plt.hist(
    df["Amount"],
    bins=100
)

plt.title("Transaction Amount Distribution")
plt.xlabel("Transaction Amount")
plt.ylabel("Number of Transactions")

plt.tight_layout()

plt.savefig(
    REPORTS_DIR / "eda_amount_distribution.png",
    dpi=300
)

plt.close()


# =========================================================
# 4. Transaction amount by class
# =========================================================
print("\n3. TRANSACTION AMOUNT BY CLASS")
print("-" * 60)

amount_by_class = (
    df.groupby("Class")["Amount"]
    .agg(["count", "mean", "median", "std", "min", "max"])
)

print(amount_by_class)


amount_by_class.to_csv(
    REPORTS_DIR / "eda_amount_by_class.csv"
)


# =========================================================
# 5. Amount distribution by class
# =========================================================
legitimate_amounts = df.loc[
    df["Class"] == 0, "Amount"
]

fraud_amounts = df.loc[
    df["Class"] == 1, "Amount"
]


plt.figure(figsize=(8, 5))

plt.hist(
    legitimate_amounts,
    bins=100,
    alpha=0.6,
    label="Legitimate"
)

plt.hist(
    fraud_amounts,
    bins=100,
    alpha=0.6,
    label="Fraud"
)

plt.title("Transaction Amount Distribution by Class")
plt.xlabel("Transaction Amount")
plt.ylabel("Number of Transactions")
plt.legend()

# Logarithmic y-axis makes the rare fraud distribution visible
plt.yscale("log")

plt.tight_layout()

plt.savefig(
    REPORTS_DIR / "eda_amount_by_class.png",
    dpi=300
)

plt.close()


# =========================================================
# 6. Fraud transactions over time
# =========================================================
fraud_transactions = df[df["Class"] == 1].copy()

print("\n4. FRAUD TRANSACTIONS OVER TIME")
print("-" * 60)

print(
    f"Fraud Time range: "
    f"{fraud_transactions['Time'].min()} "
    f"to "
    f"{fraud_transactions['Time'].max()}"
)


plt.figure(figsize=(10, 5))

plt.scatter(
    fraud_transactions["Time"],
    fraud_transactions["Amount"],
    s=10,
    alpha=0.6
)

plt.title("Fraud Transactions Over Time")
plt.xlabel("Time")
plt.ylabel("Transaction Amount")

plt.tight_layout()

plt.savefig(
    REPORTS_DIR / "eda_fraud_over_time.png",
    dpi=300
)

plt.close()


# =========================================================
# 7. Fraud rate over time
# =========================================================
# Divide the timeline into 20 equal-width bins.
df["time_bin"] = pd.cut(
    df["Time"],
    bins=20,
    include_lowest=True
)

fraud_rate_by_time = (
    df.groupby("time_bin", observed=False)["Class"]
    .agg(["count", "sum"])
)

fraud_rate_by_time["fraud_rate_percent"] = (
    fraud_rate_by_time["sum"]
    / fraud_rate_by_time["count"]
    * 100
)


print("\n5. FRAUD RATE OVER TIME")
print("-" * 60)
print(fraud_rate_by_time)


fraud_rate_by_time.to_csv(
    REPORTS_DIR / "eda_fraud_rate_over_time.csv"
)


plt.figure(figsize=(10, 5))

plt.plot(
    range(1, len(fraud_rate_by_time) + 1),
    fraud_rate_by_time["fraud_rate_percent"],
    marker="o"
)

plt.title("Fraud Rate Across Time Bins")
plt.xlabel("Time Bin")
plt.ylabel("Fraud Rate (%)")

plt.tight_layout()

plt.savefig(
    REPORTS_DIR / "eda_fraud_rate_over_time.png",
    dpi=300
)

plt.close()


# =========================================================
# 8. Feature class separation
# =========================================================
feature_columns = [
    column
    for column in df.columns
    if column.startswith("V")
]

feature_separation = []

for feature in feature_columns:

    legitimate_mean = df.loc[
        df["Class"] == 0, feature
    ].mean()

    fraud_mean = df.loc[
        df["Class"] == 1, feature
    ].mean()

    separation = abs(
        fraud_mean - legitimate_mean
    )

    feature_separation.append({
        "feature": feature,
        "legitimate_mean": legitimate_mean,
        "fraud_mean": fraud_mean,
        "absolute_mean_difference": separation
    })


feature_separation = pd.DataFrame(
    feature_separation
).sort_values(
    "absolute_mean_difference",
    ascending=False
)


print("\n6. TOP FEATURES BY CLASS MEAN SEPARATION")
print("-" * 60)

print(
    feature_separation.head(10).to_string(index=False)
)


feature_separation.to_csv(
    REPORTS_DIR / "eda_feature_class_separation.csv",
    index=False
)


# =========================================================
# 9. Final validation
# =========================================================
print("\n7. FINAL VALIDATION")
print("-" * 60)

print(f"Rows: {len(df)}")
print(f"Columns: {len(df.columns) - 1}")
print(f"Missing values: {df.isnull().sum().sum()}")
print(f"Fraud cases: {(df['Class'] == 1).sum()}")
print(f"Legitimate cases: {(df['Class'] == 0).sum()}")

print("\nResearch EDA completed successfully.")

print("\nGenerated research artifacts:")
print("- eda_class_distribution.png")
print("- eda_amount_distribution.png")
print("- eda_amount_by_class.png")
print("- eda_fraud_over_time.png")
print("- eda_fraud_rate_over_time.png")
print("- eda_class_distribution.csv")
print("- eda_amount_by_class.csv")
print("- eda_fraud_rate_over_time.csv")
print("- eda_feature_class_separation.csv")