"""TDD for internal /payment/mock/:id — replaces https://pay.mock/quote/{id}.

Covers:
- approve returns internal payment_link == "/payment/mock/{quote_id}"
- system message with link visible in GET /messages/threads/{id}/messages
- POST /payment/mock/generate 201 with short_url
- GET /payment/mock/{id} returns initiated/paid_held + fees fields
- POST /payment/mock/{id}/pay transitions to paid_held + verified system message
- generic flow without quote
- old pay.mock substring absent
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.main import app
from app.models import QuoteState, QuoteVersion
from app.routers.messages import get_session as messages_get_session
from app.routers.quotes import get_db as quotes_get_db
from app.routers.ws import get_session as ws_get_session

try:
    from app.routers.payment_mock import get_session as pm_get_session  # type: ignore
except Exception:  # noqa: BLE001
    pm_get_session = None  # type: ignore[assignment]

SECRET = "test-jwt-secret-that-is-at-least-32-chars-long!!!"
ALGO = "HS256"
MASTER_HEX = "00" * 32


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


def _create_all_tables(sync_conn):  # type: ignore[no-untyped-def]
    sync_conn.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS messaging_threads (
            id VARCHAR PRIMARY KEY,
            order_id VARCHAR NOT NULL UNIQUE,
            seller_id VARCHAR NOT NULL,
            buyer_id VARCHAR NOT NULL,
            created_at DATETIME NOT NULL,
            last_message_at DATETIME,
            last_preview_encrypted TEXT
        )
        """
        )
    )
    sync_conn.execute(text("CREATE INDEX IF NOT EXISTS ix_messaging_threads_order_id ON messaging_threads (order_id)"))
    sync_conn.execute(text("CREATE INDEX IF NOT EXISTS ix_messaging_threads_seller_id ON messaging_threads (seller_id)"))
    sync_conn.execute(text("CREATE INDEX IF NOT EXISTS ix_messaging_threads_buyer_id ON messaging_threads (buyer_id)"))
    sync_conn.execute(
        text(
            """
        CREATE TABLE IF NOT EXISTS messaging_messages (
            id VARCHAR PRIMARY KEY,
            thread_id VARCHAR NOT NULL REFERENCES messaging_threads(id) ON DELETE CASCADE,
            sender_id VARCHAR NOT NULL,
            sender_role VARCHAR(16) NOT NULL,
            body_ciphertext TEXT NOT NULL,
            enc_nonce_b64 VARCHAR(64) NOT NULL,
            attachments JSON,
            created_at DATETIME NOT NULL
        )
        """
        )
    )
    sync_conn.execute(text("CREATE INDEX IF NOT EXISTS ix_messaging_messages_thread_id ON messaging_messages (thread_id)"))
    sync_conn.execute(text("CREATE INDEX IF NOT EXISTS ix_messaging_messages_sender_id ON messaging_messages (sender_id)"))
    # quote tables via metadata
    QuoteState.metadata.create_all(sync_conn, tables=[QuoteState.__table__, QuoteVersion.__table__])
    # payment_mock table if model exists
    try:
        from app.models import PaymentMock  # type: ignore

        PaymentMock.metadata.create_all(sync_conn, tables=[PaymentMock.__table__])  # type: ignore[attr-defined]
    except Exception:
        # fallback raw create for TDD red phase — create minimal table so generate/pay can be tested after impl
        sync_conn.execute(
            text(
                """
            CREATE TABLE IF NOT EXISTS payment_mocks (
                id VARCHAR PRIMARY KEY,
                quote_id VARCHAR,
                order_id VARCHAR,
                thread_id VARCHAR,
                amount_minor INTEGER NOT NULL,
                status VARCHAR(16) NOT NULL,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL
            )
            """
            )
        )


async def _make_app(monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    monkeypatch.setenv("JWT_SECRET_KEY", SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", ALGO)
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", MASTER_HEX)
    monkeypatch.setenv("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(_create_all_tables)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override():  # type: ignore[no-untyped-def]
        async with factory() as session:
            yield session

    app.dependency_overrides[messages_get_session] = override
    app.dependency_overrides[ws_get_session] = override
    app.dependency_overrides[quotes_get_db] = override
    if pm_get_session is not None:
        app.dependency_overrides[pm_get_session] = override  # type: ignore[arg-type]
    return engine, factory


@pytest.mark.asyncio
async def test_approve_returns_internal_link_and_system_message(monkeypatch):  # type: ignore[no-untyped-def]
    engine, _ = await _make_app(monkeypatch)
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    seller_tok = _token(str(seller), "seller", "seller@test.com")
    buyer_tok = _token(str(buyer), "buyer", "buyer@test.com")
    order_id = uuid.uuid4()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as tc:
        # create thread for this order
        resp = await tc.post(
            "/messages/threads",
            json={"order_id": str(order_id), "seller_id": str(seller), "buyer_id": str(buyer)},
            headers={"Authorization": f"Bearer {seller_tok}"},
        )
        assert resp.status_code == 201, resp.text
        thread_id = resp.json()["id"]

        # create quote
        resp = await tc.post(
            "/quotes",
            json={"order_id": str(order_id), "price_minor": 10000, "qty": 2, "shipping_minor": 500},
            headers={"Authorization": f"Bearer {seller_tok}", "X-Buyer-Id": str(buyer)},
        )
        assert resp.status_code == 201, resp.text
        quote_id = resp.json()["current"]["quote_id"]

        # approve as buyer (task says seller but buyer is correct role)
        resp = await tc.post(f"/quotes/{quote_id}/approve", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp.status_code == 200, resp.text
        body = resp.json()
        # payment_link must be internal
        link = body.get("payment_link") or body.get("payment", {}).get("payment_link", "")
        assert link == f"/payment/mock/{quote_id}", f"expected internal link, got {link}"
        # also check payment object if present
        if "payment" in body:
            assert body["payment"]["payment_link"] == f"/payment/mock/{quote_id}"
        assert "https://pay.mock" not in str(body)
        assert "pay.mock" not in str(body)

        # GET messages as buyer contains system message with link
        resp = await tc.get(f"/messages/threads/{thread_id}/messages?limit=50&offset=0", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp.status_code == 200, resp.text
        items = resp.json()["items"]
        assert len(items) >= 1, "expected system message after approve"
        bodies = [m["body"] for m in items]
        assert any("/payment/mock/" in b for b in bodies), f"no payment link in messages: {bodies}"
        assert not any("pay.mock" in b for b in bodies)

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_payment_mock_generate_and_get_and_pay_quote(monkeypatch):  # type: ignore[no-untyped-def]
    engine, _ = await _make_app(monkeypatch)
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    seller_tok = _token(str(seller), "seller", "seller@test.com")
    buyer_tok = _token(str(buyer), "buyer", "buyer@test.com")
    order_id = uuid.uuid4()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as tc:
        resp = await tc.post(
            "/messages/threads",
            json={"order_id": str(order_id), "seller_id": str(seller), "buyer_id": str(buyer)},
            headers={"Authorization": f"Bearer {seller_tok}"},
        )
        assert resp.status_code == 201, resp.text
        thread_id = resp.json()["id"]

        resp = await tc.post(
            "/quotes",
            json={"order_id": str(order_id), "price_minor": 12000, "qty": 1, "shipping_minor": 300},
            headers={"Authorization": f"Bearer {seller_tok}", "X-Buyer-Id": str(buyer)},
        )
        assert resp.status_code == 201, resp.text
        quote_id = resp.json()["current"]["quote_id"]

        # approve to get payment link
        resp = await tc.post(f"/quotes/{quote_id}/approve", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp.status_code == 200, resp.text

        # GET /payment/mock/{quote_id}
        resp = await tc.get(f"/payment/mock/{quote_id}", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp.status_code == 200, resp.text
        detail = resp.json()
        # check required fields
        assert detail["status"] in ("initiated", "approved", "paid_held") or detail["status"] == "initiated"
        assert "amount" in detail or "amount_minor" in detail
        assert "dnk_fees" in detail
        assert "customs_excluded" in detail
        # amount should equal quote total
        amt = detail.get("amount", detail.get("amount_minor"))
        assert amt == 12300

        # POST pay
        resp = await tc.post(f"/payment/mock/{quote_id}/pay", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp.status_code == 200, resp.text
        # check quote state is paid_held after pay
        resp_q = await tc.get(f"/quotes/{quote_id}", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp_q.status_code == 200
        assert resp_q.json()["current"]["state"] == "paid_held"

        # GET after pay shows paid_held
        resp = await tc.get(f"/payment/mock/{quote_id}", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "paid_held"

        # system message verified
        resp = await tc.get(f"/messages/threads/{thread_id}/messages?limit=50&offset=0", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp.status_code == 200
        bodies = [m["body"] for m in resp.json()["items"]]
        assert any("Payment verified" in b for b in bodies), f"missing Payment verified ✓ in {bodies}"
        # also ensure ✓ appears
        assert any("✓" in b for b in bodies)

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_generic_generate_and_pay(monkeypatch):  # type: ignore[no-untyped-def]
    engine, _ = await _make_app(monkeypatch)
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    seller_tok = _token(str(seller), "seller", "seller@test.com")
    order_id = uuid.uuid4()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as tc:
        # create thread for order so system messages have place (optional but needed for later checks)
        resp = await tc.post(
            "/messages/threads",
            json={"order_id": str(order_id), "seller_id": str(seller), "buyer_id": str(buyer)},
            headers={"Authorization": f"Bearer {seller_tok}"},
        )
        assert resp.status_code == 201, resp.text

        # POST /payment/mock/generate generic
        resp = await tc.post(
            "/payment/mock/generate",
            json={"amount_minor": 9999, "order_id": str(order_id)},
            headers={"Authorization": f"Bearer {seller_tok}"},
        )
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert "payment_link_id" in data
        assert "short_url" in data
        assert data["short_url"].startswith("/payment/mock/")
        assert data["amount"] == 9999 or data.get("amount_minor") == 9999
        assert data["status"] in ("initiated", "pending", "created")

        pid = data["payment_link_id"]
        # GET it
        resp = await tc.get(f"/payment/mock/{pid}", headers={"Authorization": f"Bearer {seller_tok}"})
        assert resp.status_code == 200, resp.text
        d2 = resp.json()
        assert d2["status"] == "initiated" or d2["status"] in ("initiated", "pending", "created")
        assert d2["amount"] == 9999 or d2.get("amount_minor") == 9999

        # PAY generic
        resp = await tc.post(f"/payment/mock/{pid}/pay", headers={"Authorization": f"Bearer {seller_tok}"})
        assert resp.status_code == 200, resp.text

        resp = await tc.get(f"/payment/mock/{pid}", headers={"Authorization": f"Bearer {seller_tok}"})
        assert resp.status_code == 200
        assert resp.json()["status"] == "paid_held"

        # no pay.mock anywhere
        assert "pay.mock" not in str(data)
        assert "https://pay.mock" not in str(resp.json())

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_old_pay_mock_not_present(monkeypatch):  # type: ignore[no-untyped-def]
    engine, _ = await _make_app(monkeypatch)
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    seller_tok = _token(str(seller), "seller", "seller@test.com")
    buyer_tok = _token(str(buyer), "buyer", "buyer@test.com")
    order_id = uuid.uuid4()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as tc:
        resp = await tc.post(
            "/messages/threads",
            json={"order_id": str(order_id), "seller_id": str(seller), "buyer_id": str(buyer)},
            headers={"Authorization": f"Bearer {seller_tok}"},
        )
        assert resp.status_code == 201
        resp = await tc.post(
            "/quotes",
            json={"order_id": str(order_id), "price_minor": 5000, "qty": 1, "shipping_minor": 100},
            headers={"Authorization": f"Bearer {seller_tok}", "X-Buyer-Id": str(buyer)},
        )
        assert resp.status_code == 201
        qid = resp.json()["current"]["quote_id"]
        resp = await tc.post(f"/quotes/{qid}/approve", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp.status_code == 200
        assert "pay.mock" not in resp.text
        assert "https://pay.mock" not in resp.text
        # also GET payment detail
        resp = await tc.get(f"/payment/mock/{qid}", headers={"Authorization": f"Bearer {buyer_tok}"})
        assert resp.status_code == 200
        assert "pay.mock" not in resp.text

    app.dependency_overrides.clear()
    await engine.dispose()
