"""Tests for document-generation routes — thin proxy over the engine's docs API.

The old doc_generator module was deleted: backend-core now proxies document
generation to validation-engine via ``val_client.generate_docs_all``.

Covers:
- POST /orders/{id}/generate-docs → 201 with the 4 documents under named keys
- Re-generation is allowed (second call → 201)
- Non-owner seller → 403; unauthenticated → 401
"""

from __future__ import annotations

import uuid

import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient

from tests.fake_val_client import FakeValClient

SELLER_PROFILE_PAYLOAD: dict[str, str] = {
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
        {
            "category_slug": "cotton-apparel",
            "quantity": 100,
            "weight_g": 1000,
            "hs_code": "61091000",
            "value_minor": 50000,
        },
    ],
}


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
        "dev-secret-key-that-is-at-least-32-characters-long!!!",
        "HS256",
        60,
    )
    return {"user_id": user_id, "email": email, "role": "seller", "token": token}


@pytest.mark.asyncio
async def test_generate_docs_maps_four_named_documents(
    test_seller: dict[str, str], val_fake: FakeValClient
) -> None:
    """POST generate-docs → 201; engine docs mapped to named keys."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"])

        resp = await client.post(
            f"/orders/{order_id}/generate-docs",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp.status_code == 201, resp.text
    assert val_fake.calls.count("generate_docs_all") == 1

    data = resp.json()
    assert data["order_id"] == order_id
    assert data["status"] == "complete"
    assert data["validation_state"] == "validated"
    assert data["generated_at"] == "2026-01-01T00:00:00Z"

    docs = data["documents"]
    assert set(docs) == {
        "commercial_invoice",
        "packing_list",
        "customs_declaration",
        "postal_bill_of_export",
    }
    assert docs["commercial_invoice"]["doc_type"] == "INVOICE"
    assert docs["packing_list"]["doc_type"] == "PACKING_LIST"
    assert docs["customs_declaration"]["doc_type"] == "CN22"
    assert docs["postal_bill_of_export"]["doc_type"] == "PBE_IV"


@pytest.mark.asyncio
async def test_generate_docs_regeneration_allowed(
    test_seller: dict[str, str], val_fake: FakeValClient
) -> None:
    """Documents are versioned — regenerating is allowed (201 again)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"])

        resp1 = await client.post(
            f"/orders/{order_id}/generate-docs",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
        resp2 = await client.post(
            f"/orders/{order_id}/generate-docs",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp1.status_code == 201
    assert resp2.status_code == 201, resp2.text
    assert val_fake.calls.count("generate_docs_all") == 2


@pytest.mark.asyncio
async def test_generate_docs_non_owner_forbidden(test_seller: dict[str, str]) -> None:
    """A different seller cannot generate docs for the order → 403."""
    second_email = f"docs_other_{uuid.uuid4().hex[:8]}@test.com"
    second_seller = await _create_second_seller(second_email)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _create_profile(client, test_seller["token"])
            order_id = await _create_order(client, test_seller["token"])

            resp = await client.post(
                f"/orders/{order_id}/generate-docs",
                headers={"Authorization": f"Bearer {second_seller['token']}"},
            )
    finally:
        from auth.models import User
        from sqlalchemy import delete
        from storage.db import get_session

        async with get_session()() as session:
            await session.execute(delete(User).where(User.email == second_email))
            await session.commit()

    assert resp.status_code == 403
    assert resp.json()["detail"] == "Only the order owner can generate documents"


@pytest.mark.asyncio
async def test_generate_docs_unauthorized() -> None:
    """No auth token → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/orders/550e8400-e29b-41d4-a716-446655440000/generate-docs",
        )
    assert resp.status_code == 401
