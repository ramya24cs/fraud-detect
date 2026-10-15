import pandas as pd

from ml.src.models.inference import predict_fraud


# Load raw validation data
df = pd.read_csv("ml/data/validation_processed.csv")


# Find one legitimate transaction
normal_transaction = df[df["Class"] == 0].iloc[0].drop("Class").to_dict()


# Find one fraud transaction
fraud_transaction = df[df["Class"] == 1].iloc[0].drop("Class").to_dict()


# Predict
normal_probability = predict_fraud(normal_transaction)
fraud_probability = predict_fraud(fraud_transaction)


# Display results
print("Normal transaction probability:")
print(normal_probability)

print()

print("Fraud transaction probability:")
print(fraud_probability)