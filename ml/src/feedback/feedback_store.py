
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from ml.src.feedback.feedback_labels import FeedbackLabel
from ml.src.feedback.feedback_validator import validate_feedback


SCHEMA = """
CREATE TABLE IF NOT EXISTS operator_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id TEXT NOT NULL,
    operator_id TEXT NOT NULL,
    label TEXT NOT NULL,
    submitted_at TEXT NOT NULL,
    features_json TEXT NOT NULL
);
"""


class FeedbackStore:
    def __init__(self, database_path: str | Path):
        self.database_path = str(database_path)
        self._initialize_database()

    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_database(self):
        with self._connect() as connection:
            connection.execute(SCHEMA)

    def save_feedback(
        self,
        transaction_id: str,
        operator_id: str,
        label: FeedbackLabel | str,
        features: dict,
    ) -> int:
        transaction_id = str(transaction_id).strip()
        operator_id = str(operator_id).strip()

        if not transaction_id:
            raise ValueError("transaction_id must not be empty")

        if not operator_id:
            raise ValueError("operator_id must not be empty")

        try:
            feedback_label = FeedbackLabel(label)
        except (ValueError, TypeError) as exc:
            raise ValueError("Unsupported feedback label") from exc

        validation = validate_feedback(feedback_label)
        if not validation.valid:
            raise ValueError(validation.reason)

        if not isinstance(features, dict):
            raise ValueError("features must be a dictionary")

        try:
            features_json = json.dumps(
                features,
                allow_nan=False,
                sort_keys=True,
            )
        except (TypeError, ValueError) as exc:
            raise ValueError(
                "features must contain JSON-compatible finite values"
            ) from exc

        submitted_at = datetime.now(timezone.utc).isoformat()

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO operator_feedback (
                    transaction_id,
                    operator_id,
                    label,
                    submitted_at,
                    features_json
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    transaction_id,
                    operator_id,
                    feedback_label.value,
                    submitted_at,
                    features_json,
                ),
            )
            return int(cursor.lastrowid)

    def get_feedback(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT transaction_id, operator_id, label,
                       submitted_at, features_json
                FROM operator_feedback
                ORDER BY id
                """
            ).fetchall()

        return [
            {
                "transaction_id": row["transaction_id"],
                "operator_id": row["operator_id"],
                "label": row["label"],
                "submitted_at": row["submitted_at"],
                "features": json.loads(row["features_json"]),
            }
            for row in rows
        ]

    def get_feedback_for_transaction(
        self,
        transaction_id: str,
    ) -> list[dict]:
        normalized_id = str(transaction_id).strip()

        if not normalized_id:
            raise ValueError("transaction_id must not be empty")

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT transaction_id, operator_id, label,
                       submitted_at, features_json
                FROM operator_feedback
                WHERE transaction_id = ?
                ORDER BY id
                """,
                (normalized_id,),
            ).fetchall()

        return [
            {
                "transaction_id": row["transaction_id"],
                "operator_id": row["operator_id"],
                "label": row["label"],
                "submitted_at": row["submitted_at"],
                "features": json.loads(row["features_json"]),
            }
            for row in rows
        ]
