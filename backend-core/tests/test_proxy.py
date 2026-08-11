"""Tests for proxy routes — forwarding, 503, 401, and 504.

Covers:
- GET /api/validate → forwarded response from downstream
- GET /api/pricing → 503 when downstream unavailable
- No auth → 401
- Timeout → 504
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _mock_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    """Mock Redis so rate limiter passes through."""
    dummy = AsyncMock()
    monkeypatch.setattr("storage.redis.get_redis", lambda: dummy)


class _FakeDownstreamResponse:
    """Simulates an httpx.Response for the happy-path forward test."""

    def __init__(
        self,
        status_code: int = 200,
        content: bytes = b'{"result": "ok"}',
        headers: dict[str, str] | None = None,
    ) -> None:
        self.status_code = status_code
        self._content = content
        self.headers = httpx.Headers(headers or {"content-type": "application/json"})

    async def aiter_bytes(self):
        yield self._content


def _make_mock_httpx_client(
    monkeypatch: pytest.MonkeyPatch,
    side_effect: object | None = None,
    return_value: object | None = None,
) -> AsyncMock:
    """Patch httpx.AsyncClient to yield a controlled async context manager."""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)

    if return_value is not None:
        mock_client.request = AsyncMock(return_value=return_value)
    elif side_effect is not None:
        mock_client.request = AsyncMock(side_effect=side_effect)
    else:
        mock_client.request = AsyncMock()

    mock_cls = MagicMock(return_value=mock_client)
    monkeypatch.setattr("app.routers.proxy.httpx.AsyncClient", mock_cls)
    return mock_client


# ---------------------------------------------------------------------------
# Test: validation-engine forward → response
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_validate_forward(
    test_seller: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /api/validate should forward and return the downstream response."""
    fake_resp = _FakeDownstreamResponse(
        status_code=200,
        content=b'{"status": "valid"}',
    )
    _make_mock_httpx_client(monkeypatch, return_value=fake_resp)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/validate/test-endpoint",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp.status_code == 200
    assert resp.json() == {"status": "valid"}


@pytest.mark.asyncio
async def test_validate_forward_with_query_params(
    test_seller: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Query parameters should be forwarded to the downstream service."""
    fake_resp = _FakeDownstreamResponse(
        status_code=200,
        content=b'{"echo": "hello"}',
    )
    _make_mock_httpx_client(monkeypatch, return_value=fake_resp)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/validate/search?q=hello",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# Test: pricing-engine → 503 "unavailable"
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_pricing_unavailable(
    test_seller: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /api/pricing → 503 when the downstream engine is unreachable."""
    _make_mock_httpx_client(
        monkeypatch,
        side_effect=httpx.ConnectError("Connection refused"),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/pricing/quotes",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp.status_code == 503
    data = resp.json()
    assert "unavailable" in data["detail"].lower()
    assert "pricing" in data["detail"].lower()


# ---------------------------------------------------------------------------
# Test: no auth → 401
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_proxy_no_auth() -> None:
    """GET /api/validate without auth token → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/validate/anything")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_proxy_malformed_auth() -> None:
    """GET /api/pricing with malformed auth → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/pricing/anything",
            headers={"Authorization": "NotBearer token"},
        )

    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Test: timeout → 504
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_proxy_timeout(
    test_seller: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Downstream timeout → 504 Gateway Timeout."""
    _make_mock_httpx_client(
        monkeypatch,
        side_effect=httpx.TimeoutException("Request timed out"),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/tracking/status",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp.status_code == 504
    data = resp.json()
    assert "timed out" in data["detail"].lower()


# ---------------------------------------------------------------------------
# Test: POST forwarding (non-GET method)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_proxy_post_forward(
    test_seller: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /api/voice should forward the request body to the downstream."""
    fake_resp = _FakeDownstreamResponse(
        status_code=201,
        content=b'{"accepted": true}',
    )
    _make_mock_httpx_client(monkeypatch, return_value=fake_resp)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/voice/transcribe",
            json={"audio": "base64data"},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp.status_code == 201
    assert resp.json() == {"accepted": True}


# ---------------------------------------------------------------------------
# Test: all proxy paths work
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_proxy_all_paths_tracking(
    test_seller: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /api/tracking should forward to the tracking API."""
    fake_resp = _FakeDownstreamResponse(
        status_code=200,
        content=b'{"tracking_id": "TRK123"}',
    )
    _make_mock_httpx_client(monkeypatch, return_value=fake_resp)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/tracking/TRK123",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp.status_code == 200
    assert resp.json() == {"tracking_id": "TRK123"}
