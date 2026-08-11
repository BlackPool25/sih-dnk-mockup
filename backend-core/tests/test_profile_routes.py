from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

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


@pytest.mark.asyncio
async def test_create_profile(test_seller: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/profile",
            json=SELLER_PROFILE_PAYLOAD,
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert response.status_code == 201
    data = response.json()
    assert data["firm_name"] == "Test Exports Ltd"
    assert data["pan"] == "ABCDE1234F"
    assert data["bank_account"] == "12345678901"
    assert data["ad_code"] == "9876543"
    assert data["gstin"] == "22AAAAA0000A1Z5"
    assert data["profile_version"] == 1
    assert "id" in data
    assert "user_id" in data


@pytest.mark.asyncio
async def test_create_profile_buyer_forbidden(test_buyer: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/profile",
            json=SELLER_PROFILE_PAYLOAD,
            headers={"Authorization": f"Bearer {test_buyer['token']}"},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_get_profile(test_seller: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/profile",
            json=SELLER_PROFILE_PAYLOAD,
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
        assert create_resp.status_code == 201

        get_resp = await client.get(
            "/profile",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["pan"] == "ABCDE1234F"
    assert data["bank_account"] == "12345678901"
    assert data["ad_code"] == "9876543"
    assert data["gstin"] == "22AAAAA0000A1Z5"
    assert data["firm_name"] == "Test Exports Ltd"


@pytest.mark.asyncio
async def test_get_profile_not_found(test_seller: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/profile",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Profile not found"


@pytest.mark.asyncio
async def test_update_profile(test_seller: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        create_resp = await client.post(
            "/profile",
            json=SELLER_PROFILE_PAYLOAD,
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
        assert create_resp.status_code == 201

        update_resp = await client.put(
            "/profile",
            json={"firm_name": "Updated Exports Ltd", "pan": "XYZAB5678C"},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert update_resp.status_code == 200
    data = update_resp.json()
    assert data["firm_name"] == "Updated Exports Ltd"
    assert data["pan"] == "XYZAB5678C"
    assert data["profile_version"] == 2
    assert data["bank_account"] == "12345678901"


@pytest.mark.asyncio
async def test_update_profile_unauthorized() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.put(
            "/profile",
            json={"firm_name": "Ha"},
        )

    assert response.status_code == 401
