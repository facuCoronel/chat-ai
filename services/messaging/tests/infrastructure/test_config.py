from app.infrastructure.config import DatabaseSettings, normalize_database_url


def test_normalizes_railway_postgres_url_for_async_sqlalchemy():
    url = "postgresql://user:pass@host:5432/db"

    assert normalize_database_url(url) == "postgresql+asyncpg://user:pass@host:5432/db"


def test_normalizes_legacy_postgres_url_for_async_sqlalchemy():
    url = "postgres://user:pass@host:5432/db"

    assert normalize_database_url(url) == "postgresql+asyncpg://user:pass@host:5432/db"


def test_keeps_explicit_async_driver_url_unchanged():
    url = "postgresql+asyncpg://user:pass@host:5432/db"

    assert normalize_database_url(url) == url


def test_database_settings_ignores_unrelated_values():
    settings = DatabaseSettings(
        DATABASE_URL="postgresql://user:pass@host:5432/db",
        LOG_LEVEL="DEBUG",
        WEBHOOK_VERIFY_TOKEN="verify-token",
        APP_SECRET="app-secret",
    )

    assert settings.sqlalchemy_database_url == "postgresql+asyncpg://user:pass@host:5432/db"
    assert settings.LOG_LEVEL == "DEBUG"
