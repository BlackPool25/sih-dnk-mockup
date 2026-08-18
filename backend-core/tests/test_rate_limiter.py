"""Tests for the Redis sliding-window rate limiter middleware."""

from __future__ import annotations

import math
import time as _stdlib_time
from collections.abc import Iterator
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient

_RATE_LIMIT_MOD = "app.middleware.rate_limiter"


# ---------------------------------------------------------------------------
# Fake Redis client
# ---------------------------------------------------------------------------


class _FakeRateLimitRedis:
    def __init__(self) -> None:
        self._entries: dict[str, list[float]] = {}

    async def script_load(self, _script: str) -> str:
        return "fake-sha"

    async def evalsha(
        self,
        _sha: str,
        _numkeys: int,
        key: str,
        now_ms: int,
        window_s: int,
        limit: int,
    ) -> list[int]:
        cutoff = now_ms - window_s * 1000
        timestamps = [t for t in self._entries.get(key, []) if t >= cutoff]
        if len(timestamps) >= limit:
            wait = window_s
            if timestamps:
                oldest_ms = min(timestamps)
                wait = math.ceil((oldest_ms - cutoff) / 1000)
            self._entries[key] = timestamps
            return [len(timestamps), wait]
        timestamps.append(float(now_ms))
        self._entries[key] = timestamps
        return [len(timestamps), 0]


# ---------------------------------------------------------------------------
# time.time factory — returns a class whose ``.time()`` matches the real API
# ---------------------------------------------------------------------------


def _patch_frozen_time(monkeypatch: pytest.MonkeyPatch, offset_s: float = 0.0) -> float:
    """Replace ``time`` in the rate-limiter module with a frozen clock."""
    frozen_s = _stdlib_time.time() + offset_s

    class _Frozen:
        @staticmethod
        def time() -> float:
            return frozen_s

    monkeypatch.setattr(f"{_RATE_LIMIT_MOD}.time", _Frozen)
    return frozen_s


def _patch_advancing_time(monkeypatch: pytest.MonkeyPatch, base_s: float) -> type:
    """Replace ``time`` with a class whose ``.offset_s`` allows advancing."""

    class _Advancing:
        offset_s: float = 0.0

        @staticmethod
        def time() -> float:
            return base_s + _Advancing.offset_s

    monkeypatch.setattr(f"{_RATE_LIMIT_MOD}.time", _Advancing)
    return _Advancing


def _patch_live_time(monkeypatch: pytest.MonkeyPatch) -> None:
    class _Live:
        @staticmethod
        def time() -> float:
            return _stdlib_time.time()

    monkeypatch.setattr(f"{_RATE_LIMIT_MOD}.time", _Live)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def _freeze_time(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    _patch_frozen_time(monkeypatch)
    yield


@pytest.fixture
def fake_redis() -> _FakeRateLimitRedis:
    return _FakeRateLimitRedis()


@pytest.fixture
def _patch_rate_limit_redis(
    monkeypatch: pytest.MonkeyPatch, fake_redis: _FakeRateLimitRedis
) -> None:
    monkeypatch.setattr(f"{_RATE_LIMIT_MOD}.get_redis", lambda: fake_redis)


class _FakeDBSession:
    def __init__(self) -> None:
        sess = MagicMock()
        sess.execute = AsyncMock(
            return_value=MagicMock(scalar_one_or_none=MagicMock(return_value=None))
        )
        sess.add = MagicMock()
        sess.commit = AsyncMock()
        sess.refresh = AsyncMock()
        sess.flush = AsyncMock()
        self._session = sess

    async def __aenter__(self) -> MagicMock:
        return self._session

    async def __aexit__(self, *_: object) -> None:
        pass

    def __call__(self) -> _FakeDBSession:
        return _FakeDBSession()


@pytest.fixture
def _mock_login_db(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("auth.routes.get_session", _FakeDBSession())


# ===========================================================================
# Tests
# ===========================================================================


@pytest.mark.asyncio
async def test_login_rate_limited_after_five(
    _freeze_time: None, _patch_rate_limit_redis: None
) -> None:
    """6 rapid /auth/login → 5 succeed, 6th 429 with Retry-After."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for i in range(1, 6):
            resp = await client.post("/auth/login", json={"email": "a@b.com", "password": "pw"})
            assert resp.status_code != 429, f"Request {i} was unexpectedly rate-limited"

        resp6 = await client.post("/auth/login", json={"email": "a@b.com", "password": "pw"})
        assert resp6.status_code == 429
        assert resp6.headers.get("Retry-After") is not None
        assert int(resp6.headers["Retry-After"]) > 0


@pytest.mark.asyncio
async def test_429_response_has_rate_limit_headers(
    _freeze_time: None, _patch_rate_limit_redis: None
) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(5):
            await client.post("/auth/login", json={"email": "a@b.com", "password": "pw"})
        resp = await client.post("/auth/login", json={"email": "a@b.com", "password": "pw"})
        assert resp.status_code == 429
        assert resp.json()["detail"] == "Rate limit exceeded. Try again later."
        assert "Retry-After" in resp.headers
        assert resp.headers["X-RateLimit-Limit"] == "5"
        assert resp.headers["X-RateLimit-Remaining"] == "0"


@pytest.mark.asyncio
async def test_successful_requests_have_rate_limit_headers(
    _freeze_time: None, _patch_rate_limit_redis: None, _mock_login_db: None
) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/auth/login", json={"email": "a@b.com", "password": "pw"})
        assert resp.status_code != 429
        assert resp.headers.get("X-RateLimit-Limit") == "5"
        remaining = int(resp.headers["X-RateLimit-Remaining"])
        assert remaining > 0


@pytest.mark.asyncio
async def test_register_uses_its_own_limit(
    _freeze_time: None, _patch_rate_limit_redis: None
) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for i in range(1, 4):
            resp = await client.post(
                "/auth/register", json={"email": f"u{i}@test.com", "password": "pw123456"}
            )
            assert resp.status_code != 429, f"Register request {i} unexpectedly rate-limited"
        resp4 = await client.post(
            "/auth/register", json={"email": "u4@test.com", "password": "pw123456"}
        )
        assert resp4.status_code == 429
        assert "Retry-After" in resp4.headers


# ---------------------------------------------------------------------------
# Independent IPs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_independent_ips_get_independent_limits(
    _freeze_time: None, _patch_rate_limit_redis: None
) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(5):
            await client.post(
                "/auth/login",
                json={"email": "a@b.com", "password": "pw"},
                headers={"X-Forwarded-For": "1.2.3.4"},
            )
        blocked = await client.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "pw"},
            headers={"X-Forwarded-For": "1.2.3.4"},
        )
        assert blocked.status_code == 429

        ok = await client.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "pw"},
            headers={"X-Forwarded-For": "5.6.7.8"},
        )
        assert ok.status_code != 429


@pytest.mark.asyncio
async def test_x_real_ip_header_used_for_ip(
    _freeze_time: None, _patch_rate_limit_redis: None
) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(5):
            await client.post(
                "/auth/login",
                json={"email": "a@b.com", "password": "pw"},
                headers={"X-Real-IP": "10.0.0.1"},
            )
        blocked = await client.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "pw"},
            headers={"X-Real-IP": "10.0.0.1"},
        )
        assert blocked.status_code == 429
        ok = await client.post(
            "/auth/login",
            json={"email": "a@b.com", "password": "pw"},
            headers={"X-Real-IP": "10.0.0.2"},
        )
        assert ok.status_code != 429


# ---------------------------------------------------------------------------
# Window reset
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_window_reset_allows_requests_again(
    monkeypatch: pytest.MonkeyPatch, fake_redis: _FakeRateLimitRedis
) -> None:
    monkeypatch.setattr(f"{_RATE_LIMIT_MOD}.get_redis", lambda: fake_redis)

    base_s = _stdlib_time.time()
    Advancing = _patch_advancing_time(monkeypatch, base_s)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(5):
            resp = await client.post("/auth/login", json={"email": "a@b.com", "password": "pw"})
            assert resp.status_code != 429

        resp6 = await client.post("/auth/login", json={"email": "a@b.com", "password": "pw"})
        assert resp6.status_code == 429

        Advancing.offset_s = 61.0
        resp_after = await client.post("/auth/login", json={"email": "a@b.com", "password": "pw"})
        assert resp_after.status_code != 429


# ---------------------------------------------------------------------------
# Redis down → fail-open
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_redis_unavailable_fail_open(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_frozen_time(monkeypatch)
    monkeypatch.setattr(
        f"{_RATE_LIMIT_MOD}.get_redis",
        MagicMock(side_effect=OSError("Connection refused")),
    )
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(10):
            resp = await client.post("/auth/login", json={"email": "a@b.com", "password": "pw"})
            assert resp.status_code != 429


@pytest.mark.asyncio
async def test_redis_operation_error_fail_open(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_frozen_time(monkeypatch)
    broken = AsyncMock()
    broken.script_load = AsyncMock(return_value="err-sha")
    broken.evalsha = AsyncMock(side_effect=OSError("timeout"))
    monkeypatch.setattr(f"{_RATE_LIMIT_MOD}.get_redis", lambda: broken)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/auth/login", json={"email": "a@b.com", "password": "pw"})
        assert resp.status_code != 429


# ---------------------------------------------------------------------------
# Default route
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_non_auth_endpoint_uses_default_limit(
    monkeypatch: pytest.MonkeyPatch, fake_redis: _FakeRateLimitRedis
) -> None:
    monkeypatch.setattr(f"{_RATE_LIMIT_MOD}.get_redis", lambda: fake_redis)
    _patch_live_time(monkeypatch)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for _ in range(50):
            resp = await client.get("/health")
            assert resp.status_code == 200
