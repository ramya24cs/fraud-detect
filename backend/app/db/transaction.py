
from contextlib import contextmanager
from collections.abc import Iterator

from sqlalchemy.orm import Session


@contextmanager
def transaction_scope(db: Session) -> Iterator[Session]:
    """
    Commit the current unit of work on success.
    Roll back its changes if an exception occurs.

    Use this helper only when the caller owns the transaction
    and no transaction is already being managed elsewhere.
    """
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
