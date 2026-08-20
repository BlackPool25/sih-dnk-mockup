"""Quote lifecycle 5-round flow + guard tests — uses in-memory SQLite (quote tables only)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.main import app
from app.models import QuoteState, QuoteVersion
from app.routers.quotes import get_db

SECRET = "test-jwt-secret-that-is-at-least-32-chars-long!!!"
ALGO = "HS256"


def _token(sub: str, role: str, email: str) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": sub,
        "role": role,
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=15),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)


@pytest.mark.asyncio
async def test_5_round_flow_and_guards(monkeypatch):
    monkeypatch.setenv("JWT_SECRET_KEY", SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", ALGO)
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(
            lambda c: c.execute
        )  # no-op to ensure connection
        # Create only quote tables (avoid JSONB compilation on sqlite)
        await conn.run_sync(
            lambda sync_conn: QuoteState.metadata.create_all(
                sync_conn, tables=[QuoteState.__table__, QuoteVersion.__table__]
            )
        )
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    seller_id = uuid.uuid4()
    buyer_id = uuid.uuid4()
    seller_tok = _token(str(seller_id), "seller", "seller@test.com")
    buyer_tok = _token(str(buyer_id), "buyer", "buyer@test.com")
    order_id = uuid.uuid4()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as tc:
        resp = await tc.post(
            "/quotes",
            json={"order_id": str(order_id), "price_minor": 10000, "qty": 2, "shipping_minor": 500},
            headers={"Authorization": f"Bearer {seller_tok}", "X-Buyer-Id": str(buyer_id)},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["current"]["state"] == "sent"
        assert data["current"]["current_version"] == 1
        quote_id = data["current"]["quote_id"]

        resp = await tc.get(f"/quotes/{quote_id}", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp.status_code == 200
        assert len(resp.json()["versions"]) == 1

        resp = await tc.post(
            f"/quotes/{quote_id}/revise",
            json={"price_minor": 9000, "qty": 2, "shipping_minor": 500},
            headers={"Authorization": f"Bearer {buyer_tok}"},
        )
        assert resp.status_code == 403

        resp = await tc.post(f"/quotes/{quote_id}/approve", headers={"Authorization": f"Bearer {seller_tok}"})
        assert resp.status_code == 403

        resp = await tc.post(
            f"/quotes/{quote_id}/reject",
            json={"reason": "too expensive"},
            headers={"Authorization": f"Bearer {buyer_tok}"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["current"]["state"] == "counter"
        assert resp.json()["current"]["current_version"] == 2
        assert resp.json()["versions"][1]["reason"] == "too expensive"

        resp = await tc.post(
            f"/quotes/{quote_id}/revise",
            json={"price_minor": 8000, "qty": 2, "shipping_minor": 400},
            headers={"Authorization": f"Bearer {seller_tok}"},
        )
        assert resp.status_code == 200, resp.text
        assert resp.json()["current"]["state"] == "sent"
        assert resp.json()["current"]["current_version"] == 3

        resp = await tc.post(
            f"/quotes/{quote_id}/reject",
            json={"reason": "still high"},
            headers={"Authorization": f"Bearer {buyer_tok}"},
        )
        assert resp.status_code == 200
        assert resp.json()["current"]["state"] == "counter"
        assert resp.json()["current"]["current_version"] == 4

        resp = await tc.post(
            f"/quotes/{quote_id}/revise",
            json={"price_minor": 7500, "qty": 2, "shipping_minor": 400},
            headers={"Authorization": f"Bearer {seller_tok}"},
        )
        assert resp.status_code == 200
        assert resp.json()["current"]["current_version"] == 5

        resp = await tc.post(f"/quotes/{quote_id}/approve", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["current"]["state"] == "approved"
        assert resp.json()["mocked"] is True
        assert "payment_link" in resp.json()
        assert resp.json()["payment_link"] == f"/payment/mock/{quote_id}"
        assert "https://pay.mock" not in resp.json()["payment_link"]

        resp = await tc.post(f"/quotes/{quote_id}/mock-pay", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp.status_code == 200, resp.text
        assert resp.json()["current"]["state"] == "paid_held"
        assert resp.json()["current"]["current_version"] == 7

        resp = await tc.post(f"/quotes/{quote_id}/approve", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp.status_code == 422
        resp = await tc.post(
            f"/quotes/{quote_id}/revise",
            json={"price_minor": 7000, "qty": 2, "shipping_minor": 300},
            headers={"Authorization": f"Bearer {seller_tok}"},
        )
        assert resp.status_code == 422
        resp = await tc.post(
            f"/quotes/{quote_id}/reject",
            json={"reason": "no"},
            headers={"Authorization": f"Bearer {buyer_tok}"},
        )
        assert resp.status_code == 422
        resp = await tc.post(f"/quotes/{quote_id}/mock-pay", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp.status_code == 422

        resp = await tc.get(f"/quotes/{quote_id}", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp.status_code == 200
        versions = resp.json()["versions"]
        assert len(versions) == 7
        assert [v["version"] for v in versions] == [1, 2, 3, 4, 5, 6, 7]
        assert [v["status"] for v in versions] == ["sent", "counter", "sent", "counter", "sent", "approved", "paid_held"]

        resp = await tc.get(f"/quotes/by-order/{order_id}", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        outsider_tok = _token(str(uuid.uuid4()), "buyer", "outsider@test.com")
        resp = await tc.get(f"/quotes/{quote_id}", headers={"Authorization": f"Bearer {outsider_tok}"})
        assert resp.status_code == 403

        order2 = uuid.uuid4()
        resp = await tc.post(
            "/quotes",
            json={"order_id": str(order2), "price_minor": 5000, "qty": 1, "shipping_minor": 0},
            headers={"Authorization": f"Bearer {seller_tok}", "X-Buyer-Id": str(buyer_id)},
        )
        assert resp.status_code == 201
        q2 = resp.json()["current"]["quote_id"]
        resp = await tc.post(f"/quotes/{q2}/approve", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp.status_code == 200
        resp = await tc.post(f"/quotes/{q2}/webhook", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp.status_code == 200
        assert resp.json()["current"]["state"] == "paid_held"

    app.dependency_overrides.clear()
    await engine.dispose()


def test_state_machine_exhaustive():
    from app.services.quote_state import QuoteStateError, next_state

    assert next_state("draft", "send") == "sent"
    assert next_state("sent", "reject") == "counter"
    assert next_state("counter", "revise") == "sent"
    assert next_state("sent", "approve") == "approved"
    assert next_state("counter", "approve") == "approved"
    assert next_state("approved", "pay") == "paid_held"
    with pytest.raises(QuoteStateError):
        next_state("paid_held", "approve")
    with pytest.raises(QuoteStateError):
        next_state("paid_held", "revise")
    with pytest.raises(QuoteStateError):
        next_state("draft", "approve")
    with pytest.raises(QuoteStateError):
        next_state("approved", "revise")
