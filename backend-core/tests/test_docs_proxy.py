"""Docs glue proxy & explicit PDF guard — validated vs generated split."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient

from tests.fake_val_client import FakeValClient

SELLER_PROFILE: dict[str, str] = {
    "firm_name": "Test Exports Ltd",
    "owner_name": "John Doe",
    "pan": "ABCDE1234F",
    "bank_name": "State Bank of India",
    "bank_account": "12345678901",
    "ifsc": "SBIN0001234",
    "bank_branch": "Mumbai Main",
    "iec": "1234567890",
    "ad_code": "12345678901234",
    "gstin": "22AAAAA0000A1Z5",
    "address_line1": "123 Shipping Lane",
    "address_line2": "Andheri East",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400069",
    "phone": "9876543210",
}

ORDER_PAYLOAD: dict[str, object] = {
    "destination_country": "US",
    "value_minor": 50000,
    "currency": "INR",
    "consignee": "Acme Corp, New York",
    "net_weight_g": 1000,
    "gross_weight_g": 1200,
    "article_id": "cotton-tshirts",
    "line_items": [
        {"category_slug": "cotton-apparel", "quantity": 100, "weight_g": 1000, "hs_code": "61091000", "value_minor": 50000}
    ],
}


async def _create_profile(client: AsyncClient, token: str) -> None:
    resp = await client.post("/profile", json=SELLER_PROFILE, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201, resp.text


async def _create_order(client: AsyncClient, token: str) -> str:
    resp = await client.post("/orders", json=ORDER_PAYLOAD, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


class _FakePdfResponse:
    def __init__(self, content: bytes = b"%PDF-1.4 fake") -> None:
        self.status_code = 200
        self.content = content

    async def aiter_bytes(self):
        yield self.content


@pytest.mark.asyncio
async def test_pdf_requires_doc_type(test_seller: dict[str, str], val_fake: FakeValClient) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        oid = await _create_order(client, test_seller["token"])
        resp = await client.get(f"/orders/{oid}/pdf", headers={"Authorization": f"Bearer {test_seller['token']}"})
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_pdf_422_if_not_ready(test_seller: dict[str, str], val_fake: FakeValClient) -> None:
    val_fake.documents_payload = {"order_id": "x", "documents": []}
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        oid = await _create_order(client, test_seller["token"])
        resp = await client.get(f"/orders/{oid}/pdf?doc_type=INVOICE", headers={"Authorization": f"Bearer {test_seller['token']}"})
    assert resp.status_code == 422
    body = resp.json()
    detail = body.get("detail", body)
    assert detail.get("code") == "DOC_NOT_READY"
    assert detail.get("doc_type") == "INVOICE"


@pytest.mark.asyncio
async def test_pdf_422_pbe_iii_guard(test_seller: dict[str, str], val_fake: FakeValClient) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        oid = await _create_order(client, test_seller["token"])
        resp = await client.get(f"/orders/{oid}/pdf?doc_type=PBE_III", headers={"Authorization": f"Bearer {test_seller['token']}"})
    assert resp.status_code == 422
    detail = resp.json().get("detail", resp.json())
    assert detail.get("code") == "DOC_NOT_READY"


@pytest.mark.asyncio
async def test_pdf_success_when_ready(test_seller: dict[str, str], val_fake: FakeValClient, monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    # make order validated/ready so pdf guard passes
    # patch val_client.get_order to return ready state
    # easiest: override val_fake.order after creation to have ready state
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=_FakePdfResponse())
    monkeypatch.setattr("app.routers.orders.httpx.AsyncClient", MagicMock(return_value=mock_client))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        oid = await _create_order(client, test_seller["token"])
        # force ready state
        if isinstance(val_fake.order, dict) and isinstance(val_fake.order.get("order"), dict):
            val_fake.order["order"]["validation_state"] = "ready"
            val_fake.order["order"]["last_report"] = {"validation_state": "ready"}
        resp = await client.get(f"/orders/{oid}/pdf?doc_type=INVOICE", headers={"Authorization": f"Bearer {test_seller['token']}"})
    assert resp.status_code == 200, resp.text
    assert resp.headers["content-type"] == "application/pdf"
    assert "generate_docs_all" not in val_fake.calls


@pytest.mark.asyncio
async def test_documents_proxied(test_seller: dict[str, str], val_fake: FakeValClient) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        oid = await _create_order(client, test_seller["token"])
        resp = await client.get(f"/orders/{oid}/documents", headers={"Authorization": f"Bearer {test_seller['token']}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["order_id"] == oid
    assert "last_report" in data
    assert "validated" in data
    assert "documents" in data
    assert "generated" in data or "docs" in data
    # mapped documents contain commercial_invoice
    assert "commercial_invoice" in data["documents"]
    assert data["documents"]["commercial_invoice"]["doc_type"] == "INVOICE"


@pytest.mark.asyncio
async def test_translated_consignee(test_seller: dict[str, str], val_fake: FakeValClient, monkeypatch: pytest.MonkeyPatch) -> None:
    translated = {"consignee": "Shikha Sharma"}
    mock_ensure = AsyncMock(return_value=translated)
    monkeypatch.setattr("app.routers.docs.ensure_english_free_text", mock_ensure)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        oid = await _create_order(client, test_seller["token"])
        # inject non-latin consignee into fake order
        if isinstance(val_fake.order, dict) and isinstance(val_fake.order.get("order"), dict):
            val_fake.order["order"]["consignee"] = "शिखा शर्मा"
        resp = await client.get(f"/orders/{oid}/documents", headers={"Authorization": f"Bearer {test_seller['token']}"})
    assert resp.status_code == 200
    assert mock_ensure.called
    data = resp.json()
    assert data.get("consignee") == "Shikha Sharma"
    assert data.get("consignee_translated") is True
