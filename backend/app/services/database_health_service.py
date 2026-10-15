
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from backend.app.db.session import engine


def check_database_connection() -> dict[str, str]:
    """Check whether PostgreSQL is reachable."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected",
        }

    except SQLAlchemyError:
        return {
            "status": "error",
            "database": "unavailable",
        }
