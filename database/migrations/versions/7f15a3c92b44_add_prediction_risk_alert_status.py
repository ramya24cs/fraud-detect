"""Persist high-risk prediction alert delivery status."""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "7f15a3c92b44"
down_revision: Union[str, Sequence[str], None] = "e42c91f0b675"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "predictions",
        sa.Column(
            "risk_alert_status",
            sa.String(length=20),
            server_default="NOT_REQUIRED",
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("predictions", "risk_alert_status")
