"""Contract tests for pricing proxy — mocked downstream 200/422/503 + auth forwarding."""

from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.pricing_client import PricingClient
from app.services.val_client import ServiceUnavailable as ValUnavailable

pytestmark = pytest.mark.asyncio


ORDER_ID = "123e4567-e89b-12d3-a456-426614174000"


def _order_dict(seller_id: str) -> dict[str, object]:
    return {
        "order": {
            "id": ORDER_ID,
            "seller_id": seller_id,
            "buyer_id": seller_id,
            "status": "created",
            "validation_state": "validated",
        },
        "last_report": {},
        "line_items": [],
    }


def _patch_val_get(monkeypatch, seller_id: str):
    """Make val_client.get_order return the seller's order."""
    from unittest.mock import AsyncMock

    mock = AsyncMock(return_value=_order_dict(seller_id))
    monkeypatch.setattr("app.routers.pricing.val_client.get_order", mock)
    # also patch the service singleton for any direct imports
    monkeypatch.setattr("app.services.val_client.val_client.get_order", mock)
    return mock


def _make_pricing_client(handler) -> PricingClient:
    transport = httpx.MockTransport(handler)
    return PricingClient(base_url="http://pricing-engine:8000", validation_url="http://validation-engine:8000", transport=transport)


async def test_get_pricing_forwards_auth_and_request_id(
    test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """GET /orders/{id}/pricing → forwards Authorization + X-Request-Id, returns 200."""
    _patch_val_get(monkeypatch, test_seller["user_id"])

    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("Authorization", "")
        captured["rid"] = request.headers.get("X-Request-Id", "")
        assert request.url.path == f"/orders/{ORDER_ID}/pricing"
        assert request.method == "GET"
        return httpx.Response(200, json={"order_id": ORDER_ID, "quote": {"total_minor": 12345}})

    client = _make_pricing_client(handler)
    monkeypatch.setattr("app.services.pricing_client.pricing_client", client)
    monkeypatch.setattr("app.routers.pricing.pricing_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            f"/orders/{ORDER_ID}/pricing",
            headers={"Authorization": f"Bearer {test_seller['token']}", "X-Request-Id": "req-111"},
        )

    assert resp.status_code == 200
    assert resp.json() == {"order_id": ORDER_ID, "quote": {"total_minor": 12345}}
    assert captured["auth"] == f"Bearer {test_seller['token']}"
    assert captured["rid"] == "req-111"


async def test_trigger_pricing_seller_success(
    test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_val_get(monkeypatch, test_seller["user_id"])

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.method == "POST"
        assert request.url.path == f"/orders/{ORDER_ID}/pricing"
        assert request.headers.get("Authorization") == f"Bearer {test_seller['token']}"
        return httpx.Response(200, json={"order_id": ORDER_ID, "status": "priced"})

    client = _make_pricing_client(handler)
    monkeypatch.setattr("app.services.pricing_client.pricing_client", client)
    monkeypatch.setattr("app.routers.pricing.pricing_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            f"/orders/{ORDER_ID}/pricing",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "priced"


async def test_calculate_ad_hoc_quote_forward(
    test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("Authorization", "")
        assert request.url.path == "/pricing"
        assert request.method == "POST"
        return httpx.Response(200, json={"status": "ok", "cost": {"total": 999}})

    client = _make_pricing_client(handler)
    monkeypatch.setattr("app.services.pricing_client.pricing_client", client)
    monkeypatch.setattr("app.routers.pricing.pricing_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/pricing/calculate",
            json={"items": [], "landed_cost": {}},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
    assert resp.status_code == 200
    assert resp.json()["cost"]["total"] == 999
    assert captured["auth"] == f"Bearer {test_seller['token']}"


async def test_pricing_422_passthrough(test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_val_get(monkeypatch, test_seller["user_id"])

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"detail": "invalid config"})

    client = _make_pricing_client(handler)
    monkeypatch.setattr("app.services.pricing_client.pricing_client", client)
    monkeypatch.setattr("app.routers.pricing.pricing_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            f"/orders/{ORDER_ID}/pricing", headers={"Authorization": f"Bearer {test_seller['token']}"}
        )
    assert resp.status_code == 422
    assert "invalid config" in resp.text


async def test_pricing_503_passthrough(test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_val_get(monkeypatch, test_seller["user_id"])

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "downstream error"})

    client = _make_pricing_client(handler)
    monkeypatch.setattr("app.services.pricing_client.pricing_client", client)
    monkeypatch.setattr("app.routers.pricing.pricing_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            f"/orders/{ORDER_ID}/pricing", headers={"Authorization": f"Bearer {test_seller['token']}"}
        )
    assert resp.status_code == 503


async def test_pricing_404_passthrough(test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_val_get(monkeypatch, test_seller["user_id"])

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "order not found"})

    client = _make_pricing_client(handler)
    monkeypatch.setattr("app.services.pricing_client.pricing_client", client)
    monkeypatch.setattr("app.routers.pricing.pricing_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            f"/orders/{ORDER_ID}/pricing", headers={"Authorization": f"Bearer {test_seller['token']}"}
        )
    assert resp.status_code == 404


async def test_pricing_no_auth_401() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(f"/orders/{ORDER_ID}/pricing")
    assert resp.status_code == 401


async def test_pricing_access_denied_403(
    test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Another seller's order → 403."""
    # Order belongs to a different seller
    _patch_val_get(monkeypatch, "00000000-0000-0000-0000-000000000999")

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"ok": True})

    client = _make_pricing_client(handler)
    monkeypatch.setattr("app.services.pricing_client.pricing_client", client)
    monkeypatch.setattr("app.routers.pricing.pricing_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            f"/orders/{ORDER_ID}/pricing", headers={"Authorization": f"Bearer {test_seller['token']}"}
        )
    assert resp.status_code == 403
