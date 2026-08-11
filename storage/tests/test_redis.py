import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from storage.redis import get_redis


@pytest.fixture(autouse=True)
def _reset_module_state() -> None:
    """Reset the module-level `_redis_client` before and after every test."""
    import storage.redis as mod

    mod._redis_client = None
    try:
        del os.environ["REDIS_URL"]
    except KeyError:
        pass
    yield
    mod._redis_client = None
    try:
        del os.environ["REDIS_URL"]
    except KeyError:
        pass


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


def test_get_redis_returns_redis_instance() -> None:
    """get_redis() returns a `redis.asyncio.Redis` when REDIS_URL is set."""
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"

    with patch("redis.asyncio.ConnectionPool.from_url") as mock_pool, patch(
        "redis.asyncio.Redis"
    ) as mock_redis:
        mock_redis.return_value = MagicMock(name="redis_client")
        mock_pool.return_value = MagicMock(name="pool")

        client = get_redis()

        assert client is mock_redis.return_value
        mock_pool.assert_called_once_with("redis://localhost:6379/0")
        mock_redis.assert_called_once_with(connection_pool=mock_pool.return_value)


def test_get_redis_reuses_same_instance() -> None:
    """Subsequent calls return the cached singleton client."""
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"

    with patch("redis.asyncio.ConnectionPool.from_url"), patch(
        "redis.asyncio.Redis"
    ) as mock_redis:
        mock_redis.return_value = MagicMock(name="redis_client")

        first = get_redis()
        second = get_redis()

        assert first is second
        # ConnectionPool.from_url and Redis should each be called exactly once
        mock_redis.assert_called_once()


def test_get_redis_ping_returns_true() -> None:
    """``await get_redis().ping()`` returns ``True``."""
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"

    with patch("redis.asyncio.ConnectionPool.from_url"), patch(
        "redis.asyncio.Redis"
    ) as mock_redis:
        mock_client = MagicMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_redis.return_value = mock_client

        client = get_redis()
        result = asyncio.run(client.ping())

        assert result is True
        mock_client.ping.assert_awaited_once()


# ---------------------------------------------------------------------------
# Error-path tests
# ---------------------------------------------------------------------------


def test_get_redis_missing_redis_url_raises_valueerror() -> None:
    """Unset ``REDIS_URL`` raises ``ValueError``."""
    # _reset_module_state already cleared REDIS_URL
    with pytest.raises(ValueError, match="REDIS_URL environment variable is not set"):
        get_redis()


def test_get_redis_connection_failure_raises_connectionerror() -> None:
    """A connection failure raises ``ConnectionError`` with the URL in the message."""
    url = "redis://unreachable:6379/0"
    os.environ["REDIS_URL"] = url

    with (
        patch(
            "redis.asyncio.ConnectionPool.from_url",
            side_effect=OSError("Connection refused"),
        ),
        pytest.raises(ConnectionError, match=f"Redis connection failed at {url}"),
    ):
        get_redis()


def test_get_redis_malformed_url_raises_connectionerror() -> None:
    """A malformed URL that causes pool creation to fail raises ``ConnectionError``."""
    url = "not-a-valid-url"
    os.environ["REDIS_URL"] = url

    with (
        patch(
            "redis.asyncio.ConnectionPool.from_url",
            side_effect=ValueError("Invalid URL"),
        ),
        pytest.raises(ConnectionError, match=f"Redis connection failed at {url}"),
    ):
        get_redis()


def test_get_redis_redis_constructor_error_raises_connectionerror() -> None:
    """If the ``Redis()`` constructor itself fails, wrap in ``ConnectionError``."""
    url = "redis://localhost:6379/0"
    os.environ["REDIS_URL"] = url

    with (
        patch("redis.asyncio.ConnectionPool.from_url"),
        patch(
            "redis.asyncio.Redis",
            side_effect=RuntimeError("Unexpected failure"),
        ),
        pytest.raises(ConnectionError, match=f"Redis connection failed at {url}"),
    ):
        get_redis()
