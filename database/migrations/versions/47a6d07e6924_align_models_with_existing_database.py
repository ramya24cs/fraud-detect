"""Align indexes with the current SQLAlchemy models."""

from typing import Sequence, Union

from alembic import op


revision: str = "47a6d07e6924"
down_revision: Union[str, Sequence[str], None] = "bf60d7e50241"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Align indexes with the current schema."""

    op.drop_index("idx_audit_logs_user_id", table_name="audit_logs")
    op.create_index(
        "ix_audit_logs_user_id",
        "audit_logs",
        ["user_id"],
        unique=False,
    )

    op.drop_index("idx_model_registry_active", table_name="model_registry")
    op.create_index(
        "ix_model_registry_active",
        "model_registry",
        ["active"],
        unique=False,
    )

    op.drop_index(
        "idx_operator_feedback_transaction_id",
        table_name="operator_feedback",
    )
    op.drop_index(
        "idx_operator_feedback_user_id",
        table_name="operator_feedback",
    )
    op.create_index(
        "ix_operator_feedback_transaction_id",
        "operator_feedback",
        ["transaction_id"],
        unique=False,
    )
    op.create_index(
        "ix_operator_feedback_user_id",
        "operator_feedback",
        ["user_id"],
        unique=False,
    )

    op.drop_index(
        "idx_predictions_transaction_id",
        table_name="predictions",
    )
    op.create_index(
        "ix_predictions_transaction_id",
        "predictions",
        ["transaction_id"],
        unique=False,
    )

    # The initial migration already creates the composite
    # unique constraint for user_id and external_id.
    # Keep it and align only the external ID index.
    op.drop_index(
        "idx_transactions_external_id",
        table_name="transactions",
    )
    op.create_index(
        "ix_transactions_external_id",
        "transactions",
        ["external_id"],
        unique=False,
    )

    op.drop_constraint(
        "users_email_key",
        "users",
        type_="unique",
    )
    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )


def downgrade() -> None:
    """Restore the original index names."""

    op.drop_index("ix_users_email", table_name="users")
    op.create_unique_constraint(
        "users_email_key",
        "users",
        ["email"],
    )

    op.drop_index(
        "ix_transactions_external_id",
        table_name="transactions",
    )
    op.create_index(
        "idx_transactions_external_id",
        "transactions",
        ["external_id"],
        unique=False,
    )

    op.drop_index(
        "ix_predictions_transaction_id",
        table_name="predictions",
    )
    op.create_index(
        "idx_predictions_transaction_id",
        "predictions",
        ["transaction_id"],
        unique=False,
    )

    op.drop_index(
        "ix_operator_feedback_user_id",
        table_name="operator_feedback",
    )
    op.drop_index(
        "ix_operator_feedback_transaction_id",
        table_name="operator_feedback",
    )
    op.create_index(
        "idx_operator_feedback_user_id",
        "operator_feedback",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "idx_operator_feedback_transaction_id",
        "operator_feedback",
        ["transaction_id"],
        unique=False,
    )

    op.drop_index(
        "ix_model_registry_active",
        table_name="model_registry",
    )
    op.create_index(
        "idx_model_registry_active",
        "model_registry",
        ["active"],
        unique=False,
    )

    op.drop_index(
        "ix_audit_logs_user_id",
        table_name="audit_logs",
    )
    op.create_index(
        "idx_audit_logs_user_id",
        "audit_logs",
        ["user_id"],
        unique=False,
    )

