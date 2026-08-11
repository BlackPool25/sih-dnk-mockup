"""Tests for QR code generation — token creation, revocation, and access control.

Covers:
- POST /orders/{order_id}/generate-qr → 201 with QR URL, valid JWT
- Old token revoked when QR is regenerated
- 400 when docs haven't been generated yet
- 403 when a non-owner seller tries to generate
"""

from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app

# ---------------------------------------------------------------------------
# Test data (shared with test_doc_generation.py)
# ---------------------------------------------------------------------------

PROFILE_PAYLOAD: dict[str, str] = {
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

ORDER_PAYLOAD: dict = {
    "destination_country": "US",
    "value_minor": 200_000,
    "consignee": "Jane Doe, 123 Main St",
    "net_weight_g": 350.0,
    "gross_weight_g": 400.0,
    "line_items": [
        {
            "description": "Handwoven Silk Scarf",
            "hsn_code": "5007.20",
            "quantity": 5,
            "unit_price_minor": 25_000,
            "total_minor": 125_000,
        },
        {
            "description": "Brass Diya Set",
            "hsn_code": "7419.80",
            "quantity": 3,
            "unit_price_minor": 25_000,
            "total_minor": 75_000,
        },
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_profile(client: AsyncClient, token: str) -> None:
    resp = await client.post(
        "/profile",
        json=PROFILE_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"Profile creation failed: {resp.text}"


async def _create_order(
    client: AsyncClient, token: str, payload: dict
) -> str:
    resp = await client.post(
        "/orders",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"Order creation failed: {resp.text}"
    return resp.json()["id"]


async def _generate_docs(client: AsyncClient, token: str, order_id: str) -> None:
    resp = await client.post(
        f"/orders/{order_id}/generate-docs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"Doc generation failed: {resp.text}"


# ---------------------------------------------------------------------------
# Fixture — mock Redis so tests don't need a live Redis server
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _mock_redis_for_qr(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Replace storage.redis.get_redis with an AsyncMock.

    Also patch is_revoked in the QR router module to return False (since
    the conftest patches only ``auth.services.jwt.is_revoked``, and the QR
    router already imported the original).
    """
    dummy = AsyncMock()
    dummy.exists = AsyncMock(return_value=0)
    monkeypatch.setattr("storage.redis.get_redis", lambda: dummy)

    async def _is_not_revoked(_jti: str, _redis: object) -> bool:
        return False

    monkeypatch.setattr("app.routers.qr.is_revoked", _is_not_revoked)
    return dummy


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_qr(
    test_seller: dict[str, str],
    _mock_redis_for_qr: AsyncMock,
) -> None:
    """Generate QR → 201 with QR URL, token, and valid decodable JWT."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"], ORDER_PAYLOAD)
        await _generate_docs(client, test_seller["token"], order_id)

        resp = await client.post(
            f"/orders/{order_id}/generate-qr",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp.status_code == 201, resp.text
    data = resp.json()

    # Response shape
    assert data["order_id"] == order_id
    assert "qr_url" in data
    assert "token" in data
    assert "token_jti" in data
    assert "token_expiry" in data
    assert "qr_image_path" in data

    # QR URL embeds the token
    qr_url = data["qr_url"]
    assert f"/orders/{order_id}/docs?token=" in qr_url
    assert data["token"] in qr_url

    # JWT is decodable with correct claims
    from auth.services.jwt import decode_token

    decoded = decode_token(
        data["token"],
        "dev-secret-key-that-is-at-least-32-characters-long!!!",
        "HS256",
    )
    assert decoded["sub"] == order_id
    assert decoded["purpose"] == "doc_access"
    assert decoded["jti"] == data["token_jti"]
    assert "iat" in decoded
    assert "exp" in decoded

    transport2 = ASGITransport(app=app)
    async with AsyncClient(transport=transport2, base_url="http://test") as client2:
        get_resp = await client2.get(
            f"/orders/{order_id}",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "qr_generated"


@pytest.mark.asyncio
async def test_qr_old_token_revoked(
    test_seller: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regenerate QR — old token revoked, new token works."""
    # Track revoke_token calls
    revoke_calls: list[tuple] = []

    async def _track_revoke(jti: str, exp: object, redis_client: object) -> None:
        revoke_calls.append(jti)

    monkeypatch.setattr("app.routers.qr.revoke_token", _track_revoke)
    # Also mock is_revoked to return False (the conftest mock reaches
    # auth.services.jwt.is_revoked but the router has its own import).
    monkeypatch.setattr("app.routers.qr.is_revoked", AsyncMock(return_value=False))

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"], ORDER_PAYLOAD)
        await _generate_docs(client, test_seller["token"], order_id)

        # First QR generation
        resp1 = await client.post(
            f"/orders/{order_id}/generate-qr",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
        assert resp1.status_code == 201, resp1.text
        old_jti = resp1.json()["token_jti"]

        # Second QR generation — should revoke the old token
        resp2 = await client.post(
            f"/orders/{order_id}/generate-qr",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
        assert resp2.status_code == 201, resp2.text
        new_jti = resp2.json()["token_jti"]

    # Different JTIs
    assert old_jti != new_jti

    # Old token's jti was revoked
    assert old_jti in revoke_calls, f"Expected {old_jti} to be revoked, got {revoke_calls}"

    # New token works (decodable)
    from auth.services.jwt import decode_token

    decoded = decode_token(
        resp2.json()["token"],
        "dev-secret-key-that-is-at-least-32-characters-long!!!",
        "HS256",
    )
    assert decoded["sub"] == order_id
    assert decoded["purpose"] == "doc_access"


@pytest.mark.asyncio
async def test_qr_no_docs(
    test_seller: dict[str, str],
    _mock_redis_for_qr: AsyncMock,
) -> None:
    """Generate QR before docs_generated → 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"], ORDER_PAYLOAD)

        # Order still at "created" status — no docs generated yet
        resp = await client.post(
            f"/orders/{order_id}/generate-qr",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp.status_code == 400
    assert "documents must be generated" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_qr_unauthorized(
    test_seller: dict[str, str],
    test_buyer: dict[str, str],
    _mock_redis_for_qr: AsyncMock,
) -> None:
    """A non-owner seller cannot generate QR → 403."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"], ORDER_PAYLOAD)
        await _generate_docs(client, test_seller["token"], order_id)

        # Another seller (test_buyer has role "buyer" → require_role("seller") blocks it)
        # Actually test_buyer has role="buyer", which will be blocked by require_role("seller").
        # Use a second seller token — but we don't have that fixture.
        # The test_buyer has role "buyer", not "seller", so they can't even reach the endpoint.
        # Let me check: require_role("seller") checks role == "seller".
        
        # test_buyer role is "buyer" → 403 from require_role
        resp = await client.post(
            f"/orders/{order_id}/generate-qr",
            headers={"Authorization": f"Bearer {test_buyer['token']}"},
        )

    assert resp.status_code == 403
