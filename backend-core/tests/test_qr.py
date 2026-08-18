"""Tests for QR code generation and document access — thin proxy.

Covers:
- POST /orders/{id}/generate-qr → 201 with QR URL, valid doc-access JWT, and a
  persisted QR token JTI (``val_client.set_qr_token``)
- Regeneration revokes the previous token JTI
- 400 when documents haven't been generated yet
- 403 for a non-owner seller

- GET /orders/{id}/docs?token=X → 200 with plaintext order data (gstin present,
  pan dropped) + documents for the owner seller and sahayak
- 403 for a different seller
- 401 for missing / expired / revoked token and missing Authorization
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path
from unittest.mock import AsyncMock

import jwt
import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient

from tests.fake_val_client import FakeValClient

JWT_SECRET = "dev-secret-key-that-is-at-least-32-characters-long!!!"

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
    "currency": "INR",
    "consignee": "Acme Corp, New York",
    "net_weight_g": 1000,
    "gross_weight_g": 1200,
    "article_id": "cotton-tshirts",
    "line_items": [
        {
            "category_slug": "cotton-apparel",
            "quantity": 100,
            "weight_g": 1000,
            "hs_code": "61091000",
            "value_minor": 50000,
        },
    ],
}


@pytest.fixture(autouse=True)
def _mock_redis_for_qr(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    """Replace storage.redis.get_redis and the qr router's is_revoked/revoke."""
    dummy = AsyncMock()
    dummy.exists = AsyncMock(return_value=0)
    monkeypatch.setattr("storage.redis.get_redis", lambda: dummy)

    async def _is_not_revoked(_jti: str, _redis: object) -> bool:
        return False

    monkeypatch.setattr("app.routers.qr.is_revoked", _is_not_revoked)
    return dummy


async def _create_profile(client: AsyncClient, token: str) -> None:
    resp = await client.post(
        "/profile",
        json=SELLER_PROFILE_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"Profile creation failed: {resp.text}"


async def _create_order(client: AsyncClient, token: str) -> str:
    resp = await client.post(
        "/orders",
        json=ORDER_PAYLOAD,
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


async def _generate_qr(client: AsyncClient, token: str, order_id: str) -> dict[str, str]:
    resp = await client.post(
        f"/orders/{order_id}/generate-qr",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"QR generation failed: {resp.text}"
    return resp.json()


async def _create_second_seller(email: str) -> dict[str, str]:
    from auth.models import User, UserRole
    from auth.services.jwt import create_access_token
    from auth.services.password import hash_password
    from storage.db import get_session

    async with get_session()() as session:
        user = User(
            email=email,
            password_hash=hash_password("testpass"),
            role=UserRole("seller"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    user_id = str(user.id)
    token = create_access_token(
        {"sub": user_id, "role": "seller", "email": email},
        JWT_SECRET,
        "HS256",
        60,
    )
    return {"user_id": user_id, "email": email, "role": "seller", "token": token}


async def _cleanup_user(email: str) -> None:
    from auth.models import User
    from sqlalchemy import delete
    from storage.db import get_session

    async with get_session()() as session:
        await session.execute(delete(User).where(User.email == email))
        await session.commit()


# ---------------------------------------------------------------------------
# POST /orders/{order_id}/generate-qr
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_qr_creates_jwt_and_persists_token(
    test_seller: dict[str, str], val_fake: FakeValClient
) -> None:
    """Generate QR → 201; doc-access JWT created and JTI persisted."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"])
        await _generate_docs(client, test_seller["token"], order_id)

        resp = await client.post(
            f"/orders/{order_id}/generate-qr",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert data["order_id"] == order_id
    assert data["qr_url"] == (
        f"http://localhost:8000/orders/{order_id}/docs?token={data['token']}"
    )
    assert "token_expiry" in data
    assert Path(data["qr_image_path"]).is_file()

    decoded = jwt.decode(data["token"], JWT_SECRET, algorithms=["HS256"])
    assert decoded["sub"] == order_id
    assert decoded["purpose"] == "doc_access"
    assert decoded["jti"] == data["token_jti"]

    # JTI was persisted in validation-engine via the fake
    assert "set_qr_token" in val_fake.calls
    assert val_fake.qr_jti == data["token_jti"]


@pytest.mark.asyncio
async def test_generate_qr_docs_missing_400(
    test_seller: dict[str, str], val_fake: FakeValClient
) -> None:
    """No generated documents → 400 'Generate documents first'."""
    val_fake.documents_payload = {"order_id": "x", "documents": []}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"])

        resp = await client.post(
            f"/orders/{order_id}/generate-qr",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp.status_code == 400
    assert resp.json()["detail"] == "Generate documents first"


@pytest.mark.asyncio
async def test_generate_qr_non_owner_403(test_seller: dict[str, str]) -> None:
    """A different seller cannot generate QR → 403."""
    second_email = f"qr_other_{uuid.uuid4().hex[:8]}@test.com"
    second_seller = await _create_second_seller(second_email)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _create_profile(client, test_seller["token"])
            order_id = await _create_order(client, test_seller["token"])
            await _generate_docs(client, test_seller["token"], order_id)

            resp = await client.post(
                f"/orders/{order_id}/generate-qr",
                headers={"Authorization": f"Bearer {second_seller['token']}"},
            )
    finally:
        await _cleanup_user(second_email)

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Only the order owner can generate QR"


@pytest.mark.asyncio
async def test_generate_qr_revokes_old_token(
    test_seller: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    val_fake: FakeValClient,
) -> None:
    """Regenerating a QR revokes the previous token's JTI."""
    revoke_calls: list[str] = []

    async def _track_revoke(jti: str, exp: object, redis_client: object) -> None:
        revoke_calls.append(jti)

    monkeypatch.setattr("app.routers.qr.revoke_token", _track_revoke)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"])
        await _generate_docs(client, test_seller["token"], order_id)

        first = await _generate_qr(client, test_seller["token"], order_id)
        second = await _generate_qr(client, test_seller["token"], order_id)

    assert first["token_jti"] != second["token_jti"]
    # The old JTI was revoked on regeneration
    assert first["token_jti"] in revoke_calls
    assert second["token_jti"] not in revoke_calls
    assert val_fake.qr_jti == second["token_jti"]


# ---------------------------------------------------------------------------
# GET /orders/{order_id}/docs?token=X — document access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_docs_access_seller_200(
    test_seller: dict[str, str], val_fake: FakeValClient
) -> None:
    """Owning seller with valid token → 200; gstin present, pan dropped."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"])
        await _generate_docs(client, test_seller["token"], order_id)
        qr = await _generate_qr(client, test_seller["token"], order_id)

        resp = await client.get(
            f"/orders/{order_id}/docs",
            params={"token": qr["token"]},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["order_id"] == order_id
    assert data["gstin"] == "22AAAAA0000A1Z5"
    assert data["iec"] == "1234567890"
    assert data["bank_account"] == "12345678901"
    assert data["ad_code"] == "9876543"
    assert "pan" not in data
    assert isinstance(data["documents"], list)
    assert len(data["documents"]) == 4
    assert len(data["line_items"]) == 1


@pytest.mark.asyncio
async def test_docs_access_sahayak_200(
    test_seller: dict[str, str],
    test_sahayak: dict[str, str],
) -> None:
    """Sahayak with valid token → 200 with the order's plaintext data."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"])
        await _generate_docs(client, test_seller["token"], order_id)
        qr = await _generate_qr(client, test_seller["token"], order_id)

        resp = await client.get(
            f"/orders/{order_id}/docs",
            params={"token": qr["token"]},
            headers={"Authorization": f"Bearer {test_sahayak['token']}"},
        )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["order_id"] == order_id
    assert data["gstin"] == "22AAAAA0000A1Z5"
    assert "pan" not in data
    assert len(data["documents"]) == 4


@pytest.mark.asyncio
async def test_docs_access_wrong_seller_403(test_seller: dict[str, str]) -> None:
    """A different seller with a valid token → 403."""
    second_email = f"qr_access_{uuid.uuid4().hex[:8]}@test.com"
    second_seller = await _create_second_seller(second_email)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _create_profile(client, test_seller["token"])
            order_id = await _create_order(client, test_seller["token"])
            await _generate_docs(client, test_seller["token"], order_id)
            qr = await _generate_qr(client, test_seller["token"], order_id)

            resp = await client.get(
                f"/orders/{order_id}/docs",
                params={"token": qr["token"]},
                headers={"Authorization": f"Bearer {second_seller['token']}"},
            )
    finally:
        await _cleanup_user(second_email)

    assert resp.status_code == 403, resp.text
    assert resp.json()["detail"] == "Access denied to this order"


@pytest.mark.asyncio
async def test_docs_access_missing_token_401(
    test_seller: dict[str, str],
) -> None:
    """No token query param → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"])

        resp = await client.get(
            f"/orders/{order_id}/docs",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp.status_code == 401
    assert resp.json()["detail"] == "Missing document access token"


@pytest.mark.asyncio
async def test_docs_access_no_auth_401(test_seller: dict[str, str]) -> None:
    """No Authorization header → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"])
        await _generate_docs(client, test_seller["token"], order_id)
        qr = await _generate_qr(client, test_seller["token"], order_id)

        resp = await client.get(
            f"/orders/{order_id}/docs",
            params={"token": qr["token"]},
        )

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_docs_access_expired_token_401(test_seller: dict[str, str]) -> None:
    """Expired doc-access JWT → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"])

    now = datetime.now(UTC)
    expired = jwt.encode(
        {
            "sub": order_id,
            "purpose": "doc_access",
            "iat": now - timedelta(days=60),
            "exp": now - timedelta(days=30),
            "jti": str(uuid.uuid4()),
        },
        JWT_SECRET,
        algorithm="HS256",
    )

    transport2 = ASGITransport(app=app)
    async with AsyncClient(transport=transport2, base_url="http://test") as client2:
        resp = await client2.get(
            f"/orders/{order_id}/docs",
            params={"token": expired},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp.status_code == 401
    assert "expired" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_docs_access_revoked_token_401(
    test_seller: dict[str, str], monkeypatch: pytest.MonkeyPatch
) -> None:
    """Revoked doc-access JWT → 401."""
    revoked_jtis: set[str] = set()

    async def _track_revoke(jti: str, exp: object, redis_client: object) -> None:
        revoked_jtis.add(jti)

    async def _check_revoked(jti: str, _redis: object) -> bool:
        return jti in revoked_jtis

    monkeypatch.setattr("app.routers.qr.revoke_token", _track_revoke)
    monkeypatch.setattr("app.routers.qr.is_revoked", _check_revoked)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"])
        await _generate_docs(client, test_seller["token"], order_id)

        first = await _generate_qr(client, test_seller["token"], order_id)
        await _generate_qr(client, test_seller["token"], order_id)

        resp = await client.get(
            f"/orders/{order_id}/docs",
            params={"token": first["token"]},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp.status_code == 401
    assert "revoked" in resp.json()["detail"].lower()
