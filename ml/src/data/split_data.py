import pandas as pd
from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

DATA_PATH = PROJECT_ROOT / "ml" / "data" / "creditcard.csv"

OUTPUT_DIR = PROJECT_ROOT / "ml" / "data"

TRAIN_PATH = OUTPUT_DIR / "train.csv"
VALIDATION_PATH = OUTPUT_DIR / "validation.csv"
TEST_PATH = OUTPUT_DIR / "test.csv"


# ============================================================
# SPLIT CONFIGURATION
# ============================================================

TRAIN_RATIO = 0.70
VALIDATION_RATIO = 0.15
TEST_RATIO = 0.15


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("COST-SENSITIVE FRAUD DETECTION")
print("CHRONOLOGICAL TRAIN / VALIDATION / TEST SPLIT")
print("=" * 70)

df = pd.read_csv(DATA_PATH)

print("\nOriginal dataset:")
print(f"Rows    : {len(df)}")
print(f"Columns : {len(df.columns)}")


# ============================================================
# SORT BY TIME
# ============================================================

df = df.sort_values("Time").reset_index(drop=True)


# ============================================================
# CALCULATE TIME CUTOFFS
# ============================================================

train_cutoff = df["Time"].quantile(TRAIN_RATIO)
validation_cutoff = df["Time"].quantile(TRAIN_RATIO + VALIDATION_RATIO)


# ============================================================
# CREATE CHRONOLOGICAL SPLITS
# ============================================================

train_df = df[df["Time"] <= train_cutoff].copy()

validation_df = df[
    (df["Time"] > train_cutoff)
    & (df["Time"] <= validation_cutoff)
].copy()

test_df = df[df["Time"] > validation_cutoff].copy()


# ============================================================
# SAVE SPLITS
# ============================================================

train_df.to_csv(TRAIN_PATH, index=False)
validation_df.to_csv(VALIDATION_PATH, index=False)
test_df.to_csv(TEST_PATH, index=False)


# ============================================================
# VALIDATION FUNCTION
# ============================================================

def print_split_statistics(name, data):
    total = len(data)
    legitimate = (data["Class"] == 0).sum()
    fraud = (data["Class"] == 1).sum()
    fraud_rate = (fraud / total) * 100

    print(f"\n{name}")
    print("-" * 70)
    print(f"Rows            : {total}")
    print(f"Legitimate      : {legitimate}")
    print(f"Fraud           : {fraud}")
    print(f"Fraud rate      : {fraud_rate:.4f}%")
    print(f"Minimum Time    : {data['Time'].min()}")
    print(f"Maximum Time    : {data['Time'].max()}")


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\nTIME CUTOFFS")
print("-" * 70)
print(f"Train cutoff      : {train_cutoff}")
print(f"Validation cutoff : {validation_cutoff}")

print_split_statistics("TRAIN SET", train_df)
print_split_statistics("VALIDATION SET", validation_df)
print_split_statistics("TEST SET", test_df)


# ============================================================
# FINAL VALIDATION
# ============================================================

print("\nFINAL VALIDATION")
print("-" * 70)

total_split_rows = (
    len(train_df)
    + len(validation_df)
    + len(test_df)
)

print(f"Original rows : {len(df)}")
print(f"Split rows    : {total_split_rows}")

if total_split_rows == len(df):
    print("✓ All rows are accounted for.")
else:
    print("✗ ERROR: Some rows are missing.")

print(
    f"Train + Validation + Test = "
    f"{len(train_df)} + {len(validation_df)} + {len(test_df)}"
)

print("\nFraud counts:")
print(f"Train      : {(train_df['Class'] == 1).sum()}")
print(f"Validation : {(validation_df['Class'] == 1).sum()}")
print(f"Test       : {(test_df['Class'] == 1).sum()}")

print("\nSaved files:")
print(f"Train      : {TRAIN_PATH}")
print(f"Validation : {VALIDATION_PATH}")
print(f"Test       : {TEST_PATH}")

print("\nChronological split completed successfully.")