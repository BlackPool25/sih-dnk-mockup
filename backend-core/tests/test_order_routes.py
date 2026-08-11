"""Tests for order routes — create, list, get with access control."""

from __future__ import annotations

import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient

SELLER_PROFILE_PAYLOAD: dict[str, str] = {
    "firm_name": "Test Exports Ltd",
    "owner_name": "John Doe",
    "pan": "ABCDE1234F",
    "bank_name": "State Bank of India",
    "bank_account": "12345678901",
    "ifsc": "SBIN0001234",
    "bank_branch": "Mumbai Main",
    "iec": "1234567890",
    "ad_code": "9876543",
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
    "consignee": "Acme Corp, New York",
    "net_weight_g": 1000.0,
    "gross_weight_g": 1200.0,
    "line_items": [
        {
            "description": "Cotton T-Shirts",
            "hsn_code": "61091000",
            "quantity": 100,
            "unit_price_minor": 500,
            "total_minor": 50000,
        },
    ],
    "currency": "INR",
}


async def _create_profile(client: AsyncClient, token: str) -> dict:
    resp = await client.post(
        "/profile",
        json=SELLER_PROFILE_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"Profile creation failed: {resp.text}"
    return resp.json()


# ---------------------------------------------------------------------------
# POST /orders — create
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_order_auto_filled(test_seller: dict[str, str]) -> None:
    """Create order with profile → 201, IEC and exporter auto-filled."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])

        response = await client.post(
            "/orders",
            json=ORDER_PAYLOAD,
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert response.status_code == 201
    data = response.json()

    # Auto-filled from profile
    assert data["iec"] == "1234567890"
    assert data["bank_name"] == "State Bank of India"
    assert data["ifsc"] == "SBIN0001234"
    assert data["bank_account"] == "12345678901"
    assert data["ad_code"] == "9876543"
    assert data["exporter_name"] == "Test Exports Ltd"
    assert "Mumbai" in data["exporter_address"]
    assert data["state_code"] == "Maharashtr"  # String(10) column — truncated
    # User-submitted fields
    assert data["destination_country"] == "US"
    assert data["value_minor"] == 50000
    assert data["status"] == "created"
    assert data["seller_id"] == test_seller["user_id"]
    # Line items
    assert data["line_items"][0]["description"] == "Cotton T-Shirts"


@pytest.mark.asyncio
async def test_create_order_no_profile(test_seller: dict[str, str]) -> None:
    """Create order without profile → 400 'Complete profile first'."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/orders",
            json=ORDER_PAYLOAD,
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Complete profile first"


@pytest.mark.asyncio
async def test_create_order_buyer_forbidden(test_buyer: dict[str, str]) -> None:
    """Buyer cannot create orders — requires seller role."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/orders",
            json=ORDER_PAYLOAD,
            headers={"Authorization": f"Bearer {test_buyer['token']}"},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_create_order_unauthorized() -> None:
    """No auth → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/orders", json=ORDER_PAYLOAD)

    assert response.status_code == 401


# ---------------------------------------------------------------------------
# GET /orders — list
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_seller_lists_own_orders(test_seller: dict[str, str]) -> None:
    """Seller creates and then lists own orders."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])

        create_resp = await client.post(
            "/orders",
            json=ORDER_PAYLOAD,
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
        assert create_resp.status_code == 201

        list_resp = await client.get(
            "/orders",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] >= 1
    assert len(data["orders"]) >= 1
    order_ids = {o["id"] for o in data["orders"]}
    assert create_resp.json()["id"] in order_ids


@pytest.mark.asyncio
async def test_buyer_sees_only_own_orders(
    test_seller: dict[str, str],
    test_buyer: dict[str, str],
) -> None:
    """Buyer listing should not include seller-created orders."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        seller_resp = await client.post(
            "/orders",
            json=ORDER_PAYLOAD,
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
        assert seller_resp.status_code == 201
        seller_order_id = seller_resp.json()["id"]

        buyer_list = await client.get(
            "/orders",
            headers={"Authorization": f"Bearer {test_buyer['token']}"},
        )

    assert buyer_list.status_code == 200
    buyer_order_ids = {o["id"] for o in buyer_list.json()["orders"]}
    assert seller_order_id not in buyer_order_ids


@pytest.mark.asyncio
async def test_sahayak_sees_all_orders(
    test_seller: dict[str, str],
    test_sahayak: dict[str, str],
) -> None:
    """Sahayak can list all orders across sellers and buyers."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        seller_resp = await client.post(
            "/orders",
            json=ORDER_PAYLOAD,
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
        assert seller_resp.status_code == 201
        seller_order_id = seller_resp.json()["id"]

        sahayak_list = await client.get(
            "/orders",
            headers={"Authorization": f"Bearer {test_sahayak['token']}"},
        )

    assert sahayak_list.status_code == 200
    order_ids = {o["id"] for o in sahayak_list.json()["orders"]}
    assert seller_order_id in order_ids


# ---------------------------------------------------------------------------
# GET /orders/{order_id} — get one
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_own_order(test_seller: dict[str, str]) -> None:
    """Seller can GET their own order with decrypted fields."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        create_resp = await client.post(
            "/orders",
            json=ORDER_PAYLOAD,
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
        assert create_resp.status_code == 201
        order_id = create_resp.json()["id"]

        get_resp = await client.get(
            f"/orders/{order_id}",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == order_id
    # Seller sees decrypted ad_code and bank_account
    assert data["ad_code"] == "9876543"
    assert data["bank_account"] == "12345678901"


@pytest.mark.asyncio
async def test_buyer_cannot_get_seller_order(
    test_seller: dict[str, str],
    test_buyer: dict[str, str],
) -> None:
    """Buyer gets 403 when trying to access a seller's order."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        create_resp = await client.post(
            "/orders",
            json=ORDER_PAYLOAD,
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
        assert create_resp.status_code == 201
        order_id = create_resp.json()["id"]

        buyer_resp = await client.get(
            f"/orders/{order_id}",
            headers={"Authorization": f"Bearer {test_buyer['token']}"},
        )

    assert buyer_resp.status_code == 403


@pytest.mark.asyncio
async def test_sahayak_can_get_any_order(
    test_seller: dict[str, str],
    test_sahayak: dict[str, str],
) -> None:
    """Sahayak can GET any order but encrypted fields are not decrypted."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        create_resp = await client.post(
            "/orders",
            json=ORDER_PAYLOAD,
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
        assert create_resp.status_code == 201
        order_id = create_resp.json()["id"]

        sahayak_resp = await client.get(
            f"/orders/{order_id}",
            headers={"Authorization": f"Bearer {test_sahayak['token']}"},
        )

    assert sahayak_resp.status_code == 200
    data = sahayak_resp.json()
    assert data["id"] == order_id
    # Sahayak should NOT see decrypted seller fields
    assert data["ad_code"] is None
    assert data["bank_account"] is None
    # But plaintext fields are visible
    assert data["iec"] == "1234567890"
    assert data["destination_country"] == "US"


@pytest.mark.asyncio
async def test_get_order_not_found(test_seller: dict[str, str]) -> None:
    """Requesting a non-existent order returns 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/orders/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_list_orders_with_status_filter(test_seller: dict[str, str]) -> None:
    """Status filter returns only matching orders."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        await client.post(
            "/orders",
            json=ORDER_PAYLOAD,
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

        response = await client.get(
            "/orders?status=created",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    for order in data["orders"]:
        assert order["status"] == "created"
