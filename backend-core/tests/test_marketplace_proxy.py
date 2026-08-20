"""Proxy tests for /api/marketplace/* — feed, metrics, ranking/preview, products."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def _mock_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    dummy = AsyncMock()
    monkeypatch.setattr("storage.redis.get_redis", lambda: dummy)
    # also ensure rate limiter fails open alternative not needed since we mock
    try:
        monkeypatch.setattr("app.middleware.rate_limiter.get_redis", lambda: (_ for _ in ()).throw(ConnectionError("mock")))
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _mock_auth(monkeypatch: pytest.MonkeyPatch) -> None:
    # bypass JWT — set request.state.user via middleware patch: simplest is to patch get_current_user not used? proxy uses no Depends?
    # marketplace_proxy currently has no Depends(get_current_user) — it is open for demo; so no auth needed
    pass


class _FakeResp:
    def __init__(self, status_code: int = 200, json_data: dict | None = None) -> None:
        self.status_code = status_code
        self._json = json_data or {"hits": [], "mocked": True, "total": 0}
        self.headers = httpx.Headers({"content-type": "application/json"})
        self.text = str(self._json)

    def json(self) -> dict:
        return self._json


def _make_async_client_mock(return_value: _FakeResp | None = None, side_effect: Exception | None = None) -> MagicMock:
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    if side_effect is not None:
        mock_client.get = AsyncMock(side_effect=side_effect)
        mock_client.post = AsyncMock(side_effect=side_effect)
    else:
        rv = return_value or _FakeResp()
        mock_client.get = AsyncMock(return_value=rv)
        mock_client.post = AsyncMock(return_value=rv)
    return mock_client


def test_feed_proxied_with_x_proxied(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeResp(200, {"hits": [{"id": "1", "seller_id": "s1"}], "mocked": True, "total": 1})
    mock_client = _make_async_client_mock(return_value=fake)
    with patch("httpx.AsyncClient", return_value=mock_client):
        with TestClient(app) as c:
            resp = c.get("/api/marketplace/feed?limit=5&category=handicrafts")
    assert resp.status_code == 200
    assert resp.headers.get("X-Proxied") == "marketplace"
    data = resp.json()
    assert data["mocked"] is True
    # verify query params forwarded
    called_kwargs = mock_client.get.call_args
    assert called_kwargs is not None
    params = called_kwargs.kwargs.get("params") or called_kwargs.args[1] if len(called_kwargs.args) > 1 else {}
    # params should contain limit and category
    assert "limit" in str(called_kwargs) or "limit" in str(params)


def test_metrics_gini_drop(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeResp(200, {"mocked": True, "verification_mode": "mock", "fairness": {"gini_drop_pct": 12.5, "gini_drop_ge_10pct": True}, "ndcg_delta": 0.03})
    mock_client = _make_async_client_mock(return_value=fake)
    with patch("httpx.AsyncClient", return_value=mock_client):
        with TestClient(app) as c:
            resp = c.get("/api/marketplace/metrics")
    assert resp.status_code == 200
    assert resp.headers.get("X-Proxied") == "marketplace"
    data = resp.json()
    # either top-level or fairness
    drop = data.get("fairness", {}).get("gini_drop_pct") if isinstance(data.get("fairness"), dict) else data.get("gini_drop_pct")
    assert drop is not None
    assert float(drop) >= 10.0


def test_ranking_preview_proxied(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeResp(200, {"final_score": 0.7, "mocked": True, "fair": True})
    mock_client = _make_async_client_mock(return_value=fake)
    with patch("httpx.AsyncClient", return_value=mock_client):
        with TestClient(app) as c:
            resp = c.get("/api/marketplace/ranking/preview?relevance=0.8&sales_count=2&days=5")
    assert resp.status_code == 200
    assert resp.headers.get("X-Proxied") == "marketplace"


def test_products_proxied_with_x_seller_id(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeResp(201, {"product": {"id": "p1", "seller_id": "s1"}, "mocked": True})
    mock_client = _make_async_client_mock(return_value=fake)
    with patch("httpx.AsyncClient", return_value=mock_client):
        with TestClient(app) as c:
            resp = c.post("/api/marketplace/products", json={"title": "Test", "seller_id": "00000000-0000-4000-a000-000000000001", "category_slug": "handicrafts"}, headers={"X-Seller-Id": "seller-123"})
    assert resp.status_code == 201
    assert resp.headers.get("X-Proxied") == "marketplace"


def test_502_on_down(monkeypatch: pytest.MonkeyPatch) -> None:
    mock_client = _make_async_client_mock(side_effect=httpx.ConnectError("down"))
    with patch("httpx.AsyncClient", return_value=mock_client):
        with TestClient(app) as c:
            resp = c.get("/api/marketplace/feed?limit=2")
    assert resp.status_code == 502
    assert resp.headers.get("X-Proxied") == "marketplace"
    assert "unavailable" in resp.json().get("detail", "").lower()


def test_forward_authorization_header(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = _FakeResp(200, {"hits": [], "mocked": True})
    mock_client = _make_async_client_mock(return_value=fake)
    with patch("httpx.AsyncClient", return_value=mock_client):
        with TestClient(app) as c:
            resp = c.get("/api/marketplace/feed", headers={"Authorization": "Bearer tok123"})
    assert resp.status_code == 200
    called = mock_client.get.call_args
    assert called is not None
    hdrs = called.kwargs.get("headers", {})
    assert hdrs.get("Authorization") == "Bearer tok123"
