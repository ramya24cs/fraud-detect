"""Create the initial application schema."""

from typing import Union, Sequence
from alembic import op
from sqlalchemy.engine import Connection

revision: str = "bf60d7e50241"
down_revision: Union[str, Sequence[str], None] = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    from backend.app.db.session import Base
    import backend.app.models

    bind: Connection = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    from backend.app.db.session import Base
    import backend.app.models

    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
