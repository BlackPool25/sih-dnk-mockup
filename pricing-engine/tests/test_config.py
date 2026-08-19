import pytest
from pydantic import ValidationError

from app.config import Settings, get_settings


def test_settings_allows_missing_urls() -> None:
    settings = Settings()

    assert settings.database_url is None
    assert settings.redis_url is None


def test_settings_accepts_valid_urls() -> None:
    settings = Settings(
        database_url="postgresql+psycopg://user:pass@localhost:5433/sih_dnk",
        redis_url="redis://localhost:6379/0",
    )

    assert settings.database_url.startswith("postgresql")
    assert settings.redis_url.startswith("redis://")


def test_settings_rejects_invalid_database_url() -> None:
    with pytest.raises(ValidationError):
        Settings(database_url="mysql://user:pass@localhost/db")


def test_settings_rejects_invalid_redis_url() -> None:
    with pytest.raises(ValidationError):
        Settings(redis_url="http://localhost:6379")


def test_get_settings_reads_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql+psycopg://user:pass@localhost:5433/sih_dnk",
    )
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")

    settings = get_settings()

    assert settings.database_url == "postgresql+psycopg://user:pass@localhost:5433/sih_dnk"
    assert settings.redis_url == "redis://localhost:6379/0"

    get_settings.cache_clear()