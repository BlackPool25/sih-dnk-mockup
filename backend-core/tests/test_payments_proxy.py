"""Contract tests for payments proxy — mocked downstream 200/422/503 + auth + amount guard + webhook."""

from __future__ import annotations

import json

import httpx
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.payment_client import PaymentClient

pytestmark = pytest.mark.asyncio


def _make_payment_client(handler) -> PaymentClient:
    return PaymentClient(base_url="http://pricing-engine:8000", transport=httpx.MockTransport(handler))


async def test_create_order_forward_auth(test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, str] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["auth"] = request.headers.get("Authorization", "")
        captured["rid"] = request.headers.get("X-Request-Id", "")
        assert request.url.path == "/payment/create-order"
        assert request.method == "POST"
        body = json.loads(request.read().decode())
        assert body["amount_minor"] == 50000
        assert body["currency"] == "INR"
        return httpx.Response(201, json={"key_id": "rzp_test", "order_id": "order_123", "amount": 50000, "currency": "INR", "receipt": "r1", "status": "created"})

    client = _make_payment_client(handler)
    monkeypatch.setattr("app.services.payment_client.payment_client", client)
    monkeypatch.setattr("app.routers.payments.payment_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/payments/order",
            json={"amount_minor": 50000, "currency": "INR", "receipt": "r1", "notes": {}},
            headers={"Authorization": f"Bearer {test_seller['token']}", "X-Request-Id": "pay-req-1"},
        )
    assert resp.status_code == 201
    assert resp.json()["order_id"] == "order_123"
    assert captured["auth"] == f"Bearer {test_seller['token']}"
    assert captured["rid"] == "pay-req-1"


async def test_create_link_forward(test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/payment/create-link"
        body = json.loads(request.read().decode())
        assert body["reference_id"] == "ref-1"
        return httpx.Response(201, json={"payment_link_id": "plink_1", "short_url": "https://rzp.io/i/1", "amount": 50000, "currency": "INR", "reference_id": "ref-1", "status": "created", "destination": "RAZORPAY_MERCHANT_ACCOUNT"})

    client = _make_payment_client(handler)
    monkeypatch.setattr("app.services.payment_client.payment_client", client)
    monkeypatch.setattr("app.routers.payments.payment_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/payments/link",
            json={"amount_minor": 50000, "currency": "INR", "reference_id": "ref-1", "description": "Export payment"},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
    assert resp.status_code == 201
    assert resp.json()["payment_link_id"] == "plink_1"


async def test_get_link_status_forward(test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/payment/link-status/plink_1"
        return httpx.Response(200, json={"payment_link_id": "plink_1", "reference_id": "ref-1", "status": "paid", "amount": 50000, "amount_paid": 50000, "currency": "INR", "payment_id": "pay_1", "destination": "RAZORPAY_MERCHANT_ACCOUNT", "money_location": "RAZORPAY_MERCHANT_BALANCE", "settlement_note": "captured"})

    client = _make_payment_client(handler)
    monkeypatch.setattr("app.services.payment_client.payment_client", client)
    monkeypatch.setattr("app.routers.payments.payment_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get(
            "/payments/link/plink_1", headers={"Authorization": f"Bearer {test_seller['token']}"}
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "paid"


async def test_verify_forward(test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/payment/verify"
        return httpx.Response(200, json={"verified": True, "payment_id": "pay_1", "order_id": "order_1", "payment_status": "captured", "order_status": "paid", "amount": 50000, "currency": "INR"})

    client = _make_payment_client(handler)
    monkeypatch.setattr("app.services.payment_client.payment_client", client)
    monkeypatch.setattr("app.routers.payments.payment_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/payments/verify",
            json={"razorpay_order_id": "order_1", "razorpay_payment_id": "pay_1", "razorpay_signature": "sig"},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
    assert resp.status_code == 200
    assert resp.json()["verified"] is True


async def test_webhook_no_auth_allowed(monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/payment/webhook"
        assert request.headers.get("X-Razorpay-Signature") == "testsig"
        return httpx.Response(200, json={"status": "accepted", "event": "payment.captured"})

    client = _make_payment_client(handler)
    monkeypatch.setattr("app.services.payment_client.payment_client", client)
    monkeypatch.setattr("app.routers.payments.payment_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/payments/webhook",
            content=b'{"event":"payment.captured"}',
            headers={"X-Razorpay-Signature": "testsig", "Content-Type": "application/json"},
        )
    assert resp.status_code == 200
    assert resp.json()["status"] == "accepted"


async def test_payments_422_passthrough(test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"detail": {"error": "INVALID_PAYMENT_CURRENCY", "message": "must be INR"}})

    client = _make_payment_client(handler)
    monkeypatch.setattr("app.services.payment_client.payment_client", client)
    monkeypatch.setattr("app.routers.payments.payment_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/payments/order",
            json={"amount_minor": 50000, "currency": "USD", "receipt": "r1"},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
    assert resp.status_code == 422


async def test_payments_503_passthrough(test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(502, json={"detail": {"error": "RAZORPAY_API_ERROR"}})

    client = _make_payment_client(handler)
    monkeypatch.setattr("app.services.payment_client.payment_client", client)
    monkeypatch.setattr("app.routers.payments.payment_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/payments/order",
            json={"amount_minor": 50000, "currency": "INR", "receipt": "r1"},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
    assert resp.status_code == 503


async def test_payments_no_auth_401() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/payments/order", json={"amount_minor": 100, "currency": "INR", "receipt": "r1"})
    assert resp.status_code == 401


async def test_amount_guard_uses_server_value(test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch) -> None:
    """Client sends wrong amount with order_id → server-side order value wins (guard)."""
    from unittest.mock import AsyncMock

    # val_client.get_order returns server truth: value_minor 99999
    async def fake_get_order(order_id: str):
        return {"order": {"id": order_id, "value_minor": 99999, "seller_id": test_seller["user_id"]}, "line_items": []}

    monkeypatch.setattr("app.routers.payments.val_client.get_order", AsyncMock(side_effect=fake_get_order))
    monkeypatch.setattr("app.services.val_client.val_client.get_order", AsyncMock(side_effect=fake_get_order))

    captured_amount: dict[str, int] = {}

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.read().decode())
        captured_amount["amount"] = body["amount_minor"]
        return httpx.Response(201, json={"key_id": "rzp_test", "order_id": "order_g", "amount": body["amount_minor"], "currency": "INR", "receipt": "r-guard", "status": "created"})

    client = _make_payment_client(handler)
    monkeypatch.setattr("app.services.payment_client.payment_client", client)
    monkeypatch.setattr("app.routers.payments.payment_client", client)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post(
            "/payments/order",
            json={"amount_minor": 1, "currency": "INR", "receipt": "r-guard", "order_id": "order-xyz"},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
    assert resp.status_code == 201
    # guard replaced 1 with 99999
    assert captured_amount["amount"] == 99999
