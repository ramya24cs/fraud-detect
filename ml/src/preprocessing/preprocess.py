import pandas as pd
import joblib

from pathlib import Path
from sklearn.preprocessing import StandardScaler


# ============================================================
# PROJECT PATHS
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parents[3]

TRAIN_PATH = PROJECT_ROOT / "ml" / "data" / "train.csv"
VALIDATION_PATH = PROJECT_ROOT / "ml" / "data" / "validation.csv"
TEST_PATH = PROJECT_ROOT / "ml" / "data" / "test.csv"

OUTPUT_DIR = PROJECT_ROOT / "ml" / "data"

PREPROCESSOR_PATH = (
    PROJECT_ROOT / "ml" / "models" / "preprocessor.joblib"
)


# ============================================================
# TARGET AND FEATURES
# ============================================================

TARGET_COLUMN = "Class"

FEATURE_COLUMNS = [
    "Time",
    "V1",
    "V2",
    "V3",
    "V4",
    "V5",
    "V6",
    "V7",
    "V8",
    "V9",
    "V10",
    "V11",
    "V12",
    "V13",
    "V14",
    "V15",
    "V16",
    "V17",
    "V18",
    "V19",
    "V20",
    "V21",
    "V22",
    "V23",
    "V24",
    "V25",
    "V26",
    "V27",
    "V28",
    "Amount",
]


# ============================================================
# LOAD DATA
# ============================================================

print("=" * 70)
print("COST-SENSITIVE FRAUD DETECTION")
print("LEAKAGE-SAFE PREPROCESSING")
print("=" * 70)

train_df = pd.read_csv(TRAIN_PATH)
validation_df = pd.read_csv(VALIDATION_PATH)
test_df = pd.read_csv(TEST_PATH)

print("\nLoaded datasets:")
print(f"Train      : {train_df.shape}")
print(f"Validation : {validation_df.shape}")
print(f"Test       : {test_df.shape}")


# ============================================================
# SEPARATE FEATURES AND TARGET
# ============================================================

X_train = train_df[FEATURE_COLUMNS]
y_train = train_df[TARGET_COLUMN]

X_validation = validation_df[FEATURE_COLUMNS]
y_validation = validation_df[TARGET_COLUMN]

X_test = test_df[FEATURE_COLUMNS]
y_test = test_df[TARGET_COLUMN]


# ============================================================
# VALIDATE COLUMNS
# ============================================================

print("\nChecking feature columns...")

for column in FEATURE_COLUMNS:
    if column not in train_df.columns:
        raise ValueError(f"Missing feature in train data: {column}")

    if column not in validation_df.columns:
        raise ValueError(f"Missing feature in validation data: {column}")

    if column not in test_df.columns:
        raise ValueError(f"Missing feature in test data: {column}")

if TARGET_COLUMN not in train_df.columns:
    raise ValueError("Target column 'Class' missing from train data.")

if TARGET_COLUMN not in validation_df.columns:
    raise ValueError("Target column 'Class' missing from validation data.")

if TARGET_COLUMN not in test_df.columns:
    raise ValueError("Target column 'Class' missing from test data.")

print("✓ Feature and target columns are valid.")


# ============================================================
# CHECK MISSING VALUES
# ============================================================

print("\nChecking missing values...")

if X_train.isnull().sum().sum() != 0:
    raise ValueError("Missing values found in training features.")

if X_validation.isnull().sum().sum() != 0:
    raise ValueError("Missing values found in validation features.")

if X_test.isnull().sum().sum() != 0:
    raise ValueError("Missing values found in test features.")

print("✓ No missing values found.")


# ============================================================
# CREATE PREPROCESSOR
# ============================================================

scaler = StandardScaler()


# ============================================================
# FIT ONLY ON TRAINING DATA
# ============================================================

print("\nFitting StandardScaler...")
print("IMPORTANT: scaler is fitted ONLY on training data.")

X_train_scaled = scaler.fit_transform(X_train)


# ============================================================
# TRANSFORM VALIDATION AND TEST
# ============================================================

print("Transforming validation data...")
X_validation_scaled = scaler.transform(X_validation)

print("Transforming test data...")
X_test_scaled = scaler.transform(X_test)


# ============================================================
# SAVE PREPROCESSOR
# ============================================================

joblib.dump(scaler, PREPROCESSOR_PATH)

print(f"\nPreprocessor saved to:")
print(PREPROCESSOR_PATH)


# ============================================================
# SAVE PROCESSED DATA
# ============================================================

X_train_scaled_df = pd.DataFrame(
    X_train_scaled,
    columns=FEATURE_COLUMNS
)

X_validation_scaled_df = pd.DataFrame(
    X_validation_scaled,
    columns=FEATURE_COLUMNS
)

X_test_scaled_df = pd.DataFrame(
    X_test_scaled,
    columns=FEATURE_COLUMNS
)


# Add target column back
X_train_scaled_df[TARGET_COLUMN] = y_train.to_numpy()

X_validation_scaled_df[TARGET_COLUMN] = y_validation.to_numpy()

X_test_scaled_df[TARGET_COLUMN] = y_test.to_numpy()


# Save processed datasets
TRAIN_PROCESSED_PATH = OUTPUT_DIR / "train_processed.csv"
VALIDATION_PROCESSED_PATH = OUTPUT_DIR / "validation_processed.csv"
TEST_PROCESSED_PATH = OUTPUT_DIR / "test_processed.csv"

X_train_scaled_df.to_csv(TRAIN_PROCESSED_PATH, index=False)
X_validation_scaled_df.to_csv(
    VALIDATION_PROCESSED_PATH,
    index=False
)
X_test_scaled_df.to_csv(TEST_PROCESSED_PATH, index=False)


# ============================================================
# VALIDATION
# ============================================================

print("\n" + "=" * 70)
print("PREPROCESSING VALIDATION")
print("=" * 70)

print("\nProcessed shapes:")
print(f"Train      : {X_train_scaled_df.shape}")
print(f"Validation : {X_validation_scaled_df.shape}")
print(f"Test       : {X_test_scaled_df.shape}")

print("\nTarget distribution:")

print("\nTrain:")
print(y_train.value_counts())

print("\nValidation:")
print(y_validation.value_counts())

print("\nTest:")
print(y_test.value_counts())


# ============================================================
# BASIC SCALING CHECK
# ============================================================

print("\nTraining feature statistics after scaling:")

print(
    pd.DataFrame(
        X_train_scaled,
        columns=FEATURE_COLUMNS
    ).describe().loc[["mean", "std"]]
)


# ============================================================
# FINAL MESSAGE
# ============================================================

print("\nSaved processed datasets:")
print(TRAIN_PROCESSED_PATH)
print(VALIDATION_PROCESSED_PATH)
print(TEST_PROCESSED_PATH)

print("\n✓ Leakage-safe preprocessing completed successfully.")
print("✓ Scaler fitted only on training data.")
print("✓ Validation data was transformed only.")
print("✓ Test data was transformed only.")