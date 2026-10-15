from logging.config import fileConfig
from pathlib import Path
import sys

from alembic import context
from sqlalchemy import engine_from_config, pool

# Add the project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.app.core.config import settings
from backend.app.db.session import Base
import backend.app.models  # noqa: F401


# Alembic configuration.
config = context.config

# Set up logging from alembic.ini when available.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Importing backend.app.models registers the models with Base.metadata.
target_metadata = Base.metadata


def get_database_url() -> str:
    """Prefer the direct connection URL for migrations when configured."""
    return settings.NEON_DIRECT_URL or settings.DATABASE_URL


def run_migrations_offline() -> None:
    """Run migrations without creating a database connection."""
    url = get_database_url()

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a live database connection."""
    # Escape percent signs for ConfigParser interpolation.
    database_url = get_database_url().replace("%", "%%")
    config.set_main_option("sqlalchemy.url", database_url)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()