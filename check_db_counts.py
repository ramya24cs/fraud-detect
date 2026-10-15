from sqlalchemy import text

from backend.app.db.session import engine

tables = [
    "users",
    "transactions",
    "predictions",
    "operator_feedback",
    "model_registry",
    "audit_logs",
]

with engine.connect() as connection:
    print("Database row counts:")

    for table in tables:
        result = connection.execute(
            text(f"SELECT COUNT(*) FROM {table}")
        )
        print(f"{table}: {result.scalar()} rows")