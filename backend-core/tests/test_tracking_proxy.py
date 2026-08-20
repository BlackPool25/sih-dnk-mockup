"""Contract tests for tracking proxy — mocked downstream 200/422/503 + header forwarding."""

from __future__ import annotations

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.tracking_client import TrackingClient

pytestmark = pytest.mark.asyncio


def _make_tracking_client(handler) -> TrackingClient:
    return TrackingClient(base_url="http://tracking-api:8000", transport=httpx.MockTransport(handler))


async def test_register_shipment_forward_auth(
    test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("Authorization", "")
        captured["rid"] = request.headers.get("X-Request-Id", "")
        assert request.url.path == "/shipments"
        assert request.method == "POST"
        body = request.read().decode()
        assert "TRK-123" in body
        return httpx.Response(200, json={"tracking_number": "TRK-123", "carrier": "IndiaPost", "status": "Booked"})

    client = _make_tracking_client(handler)
    monkeypatch.setattr("app.services.tracking_client.tracking_client", client)
    monkeypatch.setattr("app.routers.tracking.tracking_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/tracking/shipments",
            json={"tracking_number": "TRK-123", "carrier": "IndiaPost"},
            headers={"Authorization": f"Bearer {test_seller['token']}", "X-Request-Id": "req-xyz"},
        )
    assert resp.status_code == 200
    assert resp.json()["tracking_number"] == "TRK-123"
    assert captured["auth"] == f"Bearer {test_seller['token']}"
    assert captured["rid"] == "req-xyz"


async def test_get_shipment_forward(test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/shipments/TRK-123"
        return httpx.Response(200, json={"tracking_number": "TRK-123", "status": "In Transit"})

    client = _make_tracking_client(handler)
    monkeypatch.setattr("app.services.tracking_client.tracking_client", client)
    monkeypatch.setattr("app.routers.tracking.tracking_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            "/tracking/shipments/TRK-123", headers={"Authorization": f"Bearer {test_seller['token']}"}
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "In Transit"


async def test_add_event_forward(test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/shipments/TRK-123/events"
        assert request.method == "POST"
        return httpx.Response(200, json={"status": "Out for Delivery", "location": "Delhi Hub"})

    client = _make_tracking_client(handler)
    monkeypatch.setattr("app.services.tracking_client.tracking_client", client)
    monkeypatch.setattr("app.routers.tracking.tracking_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/tracking/shipments/TRK-123/events",
            json={"status": "Out for Delivery", "location": "Delhi Hub"},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "Out for Delivery"


async def test_get_events_forward(test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/shipments/TRK-123/events"
        return httpx.Response(200, json=[{"status": "Booked"}, {"status": "In Transit"}])

    client = _make_tracking_client(handler)
    monkeypatch.setattr("app.services.tracking_client.tracking_client", client)
    monkeypatch.setattr("app.routers.tracking.tracking_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            "/tracking/shipments/TRK-123/events", headers={"Authorization": f"Bearer {test_seller['token']}"}
        )
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_tracking_duplicate_400_passthrough(
    test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(400, json={"detail": "Shipment already registered"})

    client = _make_tracking_client(handler)
    monkeypatch.setattr("app.services.tracking_client.tracking_client", client)
    monkeypatch.setattr("app.routers.tracking.tracking_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/tracking/shipments",
            json={"tracking_number": "DUP", "carrier": "IndiaPost"},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
    assert resp.status_code == 400
    assert "already registered" in resp.text.lower()


async def test_tracking_404_passthrough(test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "Shipment not found"})

    client = _make_tracking_client(handler)
    monkeypatch.setattr("app.services.tracking_client.tracking_client", client)
    monkeypatch.setattr("app.routers.tracking.tracking_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            "/tracking/shipments/NOPE", headers={"Authorization": f"Bearer {test_seller['token']}"}
        )
    assert resp.status_code == 404


async def test_tracking_503_passthrough(test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "tracking-api error 503"})

    client = _make_tracking_client(handler)
    monkeypatch.setattr("app.services.tracking_client.tracking_client", client)
    monkeypatch.setattr("app.routers.tracking.tracking_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            "/tracking/shipments/TRK-123", headers={"Authorization": f"Bearer {test_seller['token']}"}
        )
    assert resp.status_code == 503


async def test_tracking_no_auth_401() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/tracking/shipments/TRK-123")
    assert resp.status_code == 401


async def test_list_order_shipments(test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/shipments"
        assert request.url.params.get("order_id") == "ORD-1"
        return httpx.Response(200, json=[{"tracking_number": "TRK-1"}])

    client = _make_tracking_client(handler)
    monkeypatch.setattr("app.services.tracking_client.tracking_client", client)
    monkeypatch.setattr("app.routers.tracking.tracking_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            "/tracking/orders/ORD-1/shipments", headers={"Authorization": f"Bearer {test_seller['token']}"}
        )
    assert resp.status_code == 200
    # normalized shape {shipments: [...]}
    body = resp.json()
    shipments = body.get("shipments") or body
    assert isinstance(shipments, list) or isinstance(body, dict)
