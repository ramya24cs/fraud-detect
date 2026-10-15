"""Add human review decisions to transaction assessments."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "e42c91f0b675"
down_revision: Union[str, Sequence[str], None] = "c194d7a512ab"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "transaction_assessments",
        sa.Column("review_decision", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "transaction_assessments",
        sa.Column("review_comment", sa.Text(), nullable=True),
    )
    op.add_column(
        "transaction_assessments",
        sa.Column(
            "reviewed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
    )
    op.add_column(
        "transaction_assessments",
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("transaction_assessments", "reviewed_at")
    op.drop_column("transaction_assessments", "reviewed_by")
    op.drop_column("transaction_assessments", "review_comment")
    op.drop_column("transaction_assessments", "review_decision")
