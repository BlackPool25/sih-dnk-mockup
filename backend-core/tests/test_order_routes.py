"""Tests for order routes — thin proxy over the validation-engine orders API.

Covers:
- POST /orders → 201 with profile auto-fill (unified OrderResponse)
- Profile missing → 400; unauthenticated → 401; buyer role → 403
- GET /orders → role-scoped proxy call (seller filter, sahayak no filter)
- GET /orders/{id} → 200 unified; 403 for another seller; 404 from engine
- GET /orders/{id}/pdf → streams application/pdf (auto-generates docs first)
"""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient

from tests.fake_val_client import FakeValClient

# ---------------------------------------------------------------------------
# Test data — profile state "Maharashtra" must derive state_code "MH"
# ---------------------------------------------------------------------------

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


async def _create_profile(client: AsyncClient, token: str) -> None:
    resp = await client.post(
        "/profile",
        json=SELLER_PROFILE_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"Profile creation failed: {resp.text}"


async def _create_order(client: AsyncClient, token: str) -> dict[str, object]:
    resp = await client.post(
        "/orders",
        json=ORDER_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"Order creation failed: {resp.text}"
    return resp.json()


async def _create_second_seller(email: str) -> dict[str, str]:
    """Create a second seller user (outside the standard fixture)."""
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


# ---------------------------------------------------------------------------
# PDF streaming — mock the engine's httpx.AsyncClient
# ---------------------------------------------------------------------------


class _FakePdfResponse:
    def __init__(self, content: bytes = b"%PDF-1.4 fake invoice") -> None:
        self.status_code = 200
        self.content = content

    async def aiter_bytes(self):
        yield self.content


def _patch_pdf_engine(
    monkeypatch: pytest.MonkeyPatch, content: bytes = b"%PDF-1.4 fake invoice"
) -> AsyncMock:
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    mock_client.get = AsyncMock(return_value=_FakePdfResponse(content=content))
    monkeypatch.setattr(
        "app.routers.orders.httpx.AsyncClient", MagicMock(return_value=mock_client)
    )
    return mock_client


# ---------------------------------------------------------------------------
# POST /orders — create (proxy)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_order_profile_auto_fill(
    test_seller: dict[str, str], val_fake: FakeValClient
) -> None:
    """Create order with profile → 201, unified fields, profile-derived state."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])

        response = await client.post(
            "/orders",
            json=ORDER_PAYLOAD,
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert response.status_code == 201, response.text
    data = response.json()

    # Proxied through the fake val_client
    assert val_fake.calls.count("create_order") == 1
    assert val_fake.calls.count("get_order") == 1
    assert val_fake.last_payload["seller_id"] == test_seller["user_id"]

    # Unified order fields
    assert data["seller_id"] == test_seller["user_id"]
    assert data["status"] == "created"
    assert data["destination_country"] == "US"
    assert data["value_minor"] == 50000
    assert data["currency"] == "INR"
    assert data["consignee"] == "Acme Corp, New York"
    assert data["net_weight_g"] == 1000
    assert data["gross_weight_g"] == 1200
    assert data["article_id"] == "cotton-tshirts"

    # Profile-derived fields (decrypted in the payload)
    assert data["iec"] == "1234567890"
    assert data["bank_name"] == "State Bank of India"
    assert data["ifsc"] == "SBIN0001234"
    assert data["bank_account"] == "12345678901"
    assert data["ad_code"] == "9876543"
    assert data["exporter_name"] == "Test Exports Ltd"
    assert "Mumbai" in data["exporter_address"]
    assert data["state_code"] == "MH"  # Maharashtra → 2-char code

    # Line items mapped to the new shape
    item = data["line_items"][0]
    assert item["category_slug"] == "cotton-apparel"
    assert item["quantity"] == 100
    assert item["weight_g"] == 1000
    assert item["hs_code"] == "61091000"
    assert item["value_minor"] == 50000

    # Validation report present with the created order_id
    assert data["validation_report"] is not None
    assert data["validation_report"]["order_id"] == data["id"]


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
async def test_create_order_unauthorized() -> None:
    """No auth → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/orders", json=ORDER_PAYLOAD)

    assert response.status_code == 401


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


# ---------------------------------------------------------------------------
# GET /orders — list (proxy, role-scoped)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_seller_lists_own_orders(
    test_seller: dict[str, str], val_fake: FakeValClient
) -> None:
    """Seller list → proxy called with seller_id=user_id; response shape."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        created = await _create_order(client, test_seller["token"])

        list_resp = await client.get(
            "/orders",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert list_resp.status_code == 200
    data = list_resp.json()

    # Role-scoped proxy call
    assert val_fake.last_list_kwargs["seller_id"] == test_seller["user_id"]
    assert val_fake.last_list_kwargs["buyer_id"] is None

    # Response shape {orders, total, limit, offset}
    assert set(data) == {"orders", "total", "limit", "offset"}
    assert data["total"] >= 1
    assert data["limit"] == 50
    assert data["offset"] == 0
    order_ids = {o["id"] for o in data["orders"]}
    assert created["id"] in order_ids


@pytest.mark.asyncio
async def test_sahayak_list_has_no_seller_filter(
    test_seller: dict[str, str],
    test_sahayak: dict[str, str],
    val_fake: FakeValClient,
) -> None:
    """Sahayak list → proxy called with no seller_id / buyer_id filter."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        created = await _create_order(client, test_seller["token"])

        list_resp = await client.get(
            "/orders",
            headers={"Authorization": f"Bearer {test_sahayak['token']}"},
        )

    assert list_resp.status_code == 200
    assert val_fake.last_list_kwargs["seller_id"] is None
    assert val_fake.last_list_kwargs["buyer_id"] is None
    order_ids = {o["id"] for o in list_resp.json()["orders"]}
    assert created["id"] in order_ids


# ---------------------------------------------------------------------------
# GET /orders/{order_id} — get one (proxy)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_own_order(test_seller: dict[str, str]) -> None:
    """Seller can GET their own order → 200 unified response."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        created = await _create_order(client, test_seller["token"])

        get_resp = await client.get(
            f"/orders/{created['id']}",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == created["id"]
    assert data["seller_id"] == test_seller["user_id"]
    assert data["gstin"] == "22AAAAA0000A1Z5"


@pytest.mark.asyncio
async def test_get_order_other_seller_forbidden(test_seller: dict[str, str]) -> None:
    """A different seller cannot GET the order → 403."""
    second_email = f"order_other_{uuid.uuid4().hex[:8]}@test.com"
    second_seller = await _create_second_seller(second_email)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _create_profile(client, test_seller["token"])
            created = await _create_order(client, test_seller["token"])

            get_resp = await client.get(
                f"/orders/{created['id']}",
                headers={"Authorization": f"Bearer {second_seller['token']}"},
            )
    finally:
        from auth.models import User
        from sqlalchemy import delete
        from storage.db import get_session

        async with get_session()() as session:
            await session.execute(delete(User).where(User.email == second_email))
            await session.commit()

    assert get_resp.status_code == 403


@pytest.mark.asyncio
async def test_get_order_not_found(
    test_seller: dict[str, str], val_fake: FakeValClient
) -> None:
    """Engine NotFoundError → 404."""
    val_fake.not_found.add("00000000-0000-0000-0000-000000000000")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/orders/00000000-0000-0000-0000-000000000000",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert response.status_code == 404
    assert response.json()["detail"] == "Order not found"


# ---------------------------------------------------------------------------
# GET /orders/{order_id}/pdf — stream INVOICE PDF
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_order_pdf_streams_existing_docs(
    test_seller: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    val_fake: FakeValClient,
) -> None:
    """Docs exist → stream the PDF without regenerating."""
    _patch_pdf_engine(monkeypatch)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        created = await _create_order(client, test_seller["token"])

        pdf_resp = await client.get(
            f"/orders/{created['id']}/pdf",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert pdf_resp.content.startswith(b"%PDF-1.4")
    assert "generate_docs_all" not in val_fake.calls


@pytest.mark.asyncio
async def test_get_order_pdf_auto_generates_docs(
    test_seller: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
    val_fake: FakeValClient,
) -> None:
    """No documents yet → generate-docs-all runs, then the PDF is streamed."""
    _patch_pdf_engine(monkeypatch)
    val_fake.documents_payload = {"order_id": "x", "documents": []}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        created = await _create_order(client, test_seller["token"])

        pdf_resp = await client.get(
            f"/orders/{created['id']}/pdf",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert pdf_resp.status_code == 200
    assert pdf_resp.headers["content-type"] == "application/pdf"
    assert "generate_docs_all" in val_fake.calls


# ---------------------------------------------------------------------------
# Translation hook — Devanagari free-text becomes Latin at the boundary
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_order_transliterates_devanagari_consignee(
    test_seller: dict[str, str],
    val_fake: FakeValClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Consignee in Devanagari is transliterated to Latin before the payload
    leaves backend-core (so engine DB + rendered docs are English)."""
    from unittest.mock import AsyncMock

    translated = {"consignee": "Shikha Sharma"}
    monkeypatch.setattr(
        "app.routers.orders.ensure_english_free_text",
        AsyncMock(return_value=translated),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        payload = dict(ORDER_PAYLOAD)
        payload["consignee"] = "शिखा शर्मा"
        response = await client.post(
            "/orders",
            json=payload,
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert response.status_code == 201, response.text
    assert val_fake.last_payload["consignee"] == "Shikha Sharma"


@pytest.mark.asyncio
async def test_create_order_passes_latin_consignee_through(
    test_seller: dict[str, str],
    val_fake: FakeValClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Latin consignee passes through unchanged — the English invariant is
    preserved and the engine receives the exact value sent."""
    from unittest.mock import AsyncMock

    monkeypatch.setattr(
        "app.routers.orders.ensure_english_free_text",
        AsyncMock(return_value={"consignee": "Acme Corp, New York"}),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        response = await client.post(
            "/orders",
            json=ORDER_PAYLOAD,  # consignee 'Acme Corp, New York' (Latin)
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert response.status_code == 201, response.text
    assert val_fake.last_payload["consignee"] == "Acme Corp, New York"


@pytest.mark.asyncio
async def test_create_order_wires_redis_into_translation(
    test_seller: dict[str, str],
    val_fake: FakeValClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The route passes the shared Redis client into the translation call so
    the i18n:{kind}:{text} write-through cache (30d TTL) is populated and
    repeated consignees skip the mayura call."""
    from unittest.mock import AsyncMock

    captured: dict[str, object] = {}
    fake_redis = object()

    async def _fake_ensure(
        items: list[tuple[str, str]],
        *,
        redis: object | None = None,
        client: object | None = None,
    ) -> dict[str, str]:
        captured["redis"] = redis
        return {"consignee": "Shikha Sharma"}

    monkeypatch.setattr("app.routers.orders.ensure_english_free_text", _fake_ensure)
    monkeypatch.setattr("app.routers.orders.get_redis", lambda: fake_redis)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        payload = dict(ORDER_PAYLOAD)
        payload["consignee"] = "शिखा शर्मा"
        response = await client.post(
            "/orders",
            json=payload,
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert response.status_code == 201, response.text
    assert captured["redis"] is fake_redis
    assert val_fake.last_payload["consignee"] == "Shikha Sharma"


@pytest.mark.asyncio
async def test_create_order_survives_redis_unavailable(
    test_seller: dict[str, str],
    val_fake: FakeValClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cache failure (REDIS_URL unset / pool error) must never block order
    creation — translation still runs, engine still gets Latin."""
    from unittest.mock import AsyncMock

    def _raise_unset() -> object:
        raise ValueError("REDIS_URL is not set")

    monkeypatch.setattr("app.routers.orders.get_redis", _raise_unset)
    monkeypatch.setattr(
        "app.routers.orders.ensure_english_free_text",
        AsyncMock(return_value={"consignee": "Shikha Sharma"}),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        payload = dict(ORDER_PAYLOAD)
        payload["consignee"] = "शिखा शर्मा"
        response = await client.post(
            "/orders",
            json=payload,
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert response.status_code == 201, response.text
    assert val_fake.last_payload["consignee"] == "Shikha Sharma"
