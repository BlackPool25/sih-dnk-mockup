import pytest

from app.config import get_settings
from app.db import get_engine, get_session_factory


def test_db_module_import_does_not_require_database_url() -> None:
    assert callable(get_engine)
    assert callable(get_session_factory)


def test_get_engine_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()

    with pytest.raises(RuntimeError, match="DATABASE_URL is required"):
        get_engine()

    get_settings.cache_clear()
    get_engine.cache_clear()
    get_session_factory.cache_clear()