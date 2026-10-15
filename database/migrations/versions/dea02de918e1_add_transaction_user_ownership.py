"""Add transaction ownership for account isolation."""

from typing import Sequence, Union

from alembic import op


revision: str = "dea02de918e1"
down_revision: Union[str, Sequence[str], None] = "47a6d07e6924"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Align transaction indexes with the current schema."""

    # The initial migration already creates:
    # - transactions.user_id
    # - the foreign key to users.id
    # - uq_transactions_user_external_id

    # Remove the old index if it exists, then create the
    # non-unique external ID index used by the current model.
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


def downgrade() -> None:
    """Restore the previous transaction index."""

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

