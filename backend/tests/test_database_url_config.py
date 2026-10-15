from backend.app.core.config import Settings


def test_postgresql_url_uses_installed_psycopg_v3_driver():
    settings = Settings(DATABASE_URL="postgresql://db-user:secret@db.example/app")

    assert settings.DATABASE_URL.startswith("postgresql+psycopg://")


def test_render_postgres_url_uses_installed_psycopg_v3_driver():
    settings = Settings(DATABASE_URL="postgres://db-user:secret@db.example/app")

    assert settings.DATABASE_URL.startswith("postgresql+psycopg://")


def test_direct_migration_url_is_normalized_too():
    settings = Settings(
        DATABASE_URL="postgresql://db-user:secret@db.example/app",
        NEON_DIRECT_URL="postgresql+psycopg2://db-user:secret@db.example/app",
    )

    assert settings.NEON_DIRECT_URL.startswith("postgresql+psycopg://")
