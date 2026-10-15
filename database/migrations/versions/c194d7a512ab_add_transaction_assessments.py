"""Add account-history transaction assessments."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "c194d7a512ab"
down_revision: Union[str, Sequence[str], None] = "dea02de918e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "transaction_assessments",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "transaction_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("transactions.id"),
            nullable=False,
        ),
        sa.Column("anomaly_score", sa.Integer(), nullable=True),
        sa.Column("risk_level", sa.String(length=30), nullable=False),
        sa.Column("reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("history_count", sa.Integer(), nullable=False),
        sa.Column("review_required", sa.Boolean(), nullable=False),
        sa.Column("alert_created", sa.Boolean(), nullable=False),
        sa.Column("policy_version", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index(
        "ix_transaction_assessments_transaction_id",
        "transaction_assessments",
        ["transaction_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_transaction_assessments_transaction_id",
        table_name="transaction_assessments",
    )
    op.drop_table("transaction_assessments")
