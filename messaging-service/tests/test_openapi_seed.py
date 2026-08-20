"""OpenAPI/docs and seed_demo idempotency checks."""

from __future__ import annotations

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.main import app
from app.models import MessagingMessage, MessagingThread, QuoteState


def test_openapi_contains_required_paths() -> None:
    client = TestClient(app)
    resp = client.get("/openapi.json")
    assert resp.status_code == 200, resp.text
    data: object = resp.json()
    assert isinstance(data, dict)
    paths: object = data.get("paths", {})
    assert isinstance(paths, dict)
    keys: list[str] = list(paths.keys())  # type: ignore[assignment]
    flat = " ".join(keys)
    for sub in ["inbox", "threads", "quotes", "ws"]:
        assert sub in flat, f"openapi paths missing '{sub}': {keys}"


def test_docs_200() -> None:
    client = TestClient(app)
    resp = client.get("/docs")
    assert resp.status_code == 200
    assert "swagger" in resp.text.lower() or "openapi" in resp.text.lower()


def test_health_has_mocked() -> None:
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    j = resp.json()
    assert j["mocked"] is True
    assert j["service"] == "messaging-service"


@pytest.mark.asyncio
async def test_seed_demo_constants_and_flow() -> None:
    """Validate seed_demo deterministic ids and quote version invariants without touching Postgres."""
    from scripts.seed_demo import BUYER_ID, DEMO_ORDER_ID, SELLER_ID, SAHAYAK_ID, V1_PRICE

    assert str(SELLER_ID) == "11111111-1111-1111-1111-111111111111"
    assert str(BUYER_ID) == "22222222-2222-2222-2222-222222222222"
    assert str(SAHAYAK_ID) == "33333333-3333-3333-3333-333333333333"
    # deterministic
    assert DEMO_ORDER_ID == uuid.uuid5(uuid.NAMESPACE_DNS, "sih-dnk-demo-order-v1")
    assert V1_PRICE == 10000


@pytest.mark.asyncio
async def test_seed_idempotent_in_memory() -> None:
    import scripts.seed_demo as seed
    from sqlalchemy import text as sa_text

    def _create_all_sqlite(sync_conn):  # type: ignore[no-untyped-def]
        sync_conn.execute(
            sa_text(
                "CREATE TABLE IF NOT EXISTS messaging_threads (id VARCHAR PRIMARY KEY, order_id VARCHAR NOT NULL UNIQUE, seller_id VARCHAR NOT NULL, buyer_id VARCHAR NOT NULL, created_at DATETIME NOT NULL, last_message_at DATETIME, last_preview_encrypted TEXT)"
            )
        )
        sync_conn.execute(
            sa_text(
                "CREATE TABLE IF NOT EXISTS messaging_messages (id VARCHAR PRIMARY KEY, thread_id VARCHAR NOT NULL, sender_id VARCHAR NOT NULL, sender_role VARCHAR(16) NOT NULL, body_ciphertext TEXT NOT NULL, enc_nonce_b64 VARCHAR(64) NOT NULL, attachments JSON, created_at DATETIME NOT NULL)"
            )
        )
        sync_conn.execute(
            sa_text(
                "CREATE TABLE IF NOT EXISTS quote_states (quote_id VARCHAR PRIMARY KEY, order_id VARCHAR NOT NULL UNIQUE, thread_id VARCHAR, seller_id VARCHAR NOT NULL, buyer_id VARCHAR NOT NULL, current_version INTEGER NOT NULL, state VARCHAR(16) NOT NULL, amount_minor INTEGER NOT NULL, currency VARCHAR(3) NOT NULL, qty INTEGER, shipping_minor INTEGER NOT NULL, created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL)"
            )
        )
        sync_conn.execute(
            sa_text(
                "CREATE TABLE IF NOT EXISTS quote_versions (quote_id VARCHAR NOT NULL, version INTEGER NOT NULL, price_minor INTEGER NOT NULL, qty INTEGER, shipping_minor INTEGER NOT NULL, status VARCHAR(16) NOT NULL, created_by VARCHAR NOT NULL, reason TEXT, created_at DATETIME NOT NULL, PRIMARY KEY (quote_id, version))"
            )
        )

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(_create_all_sqlite)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    master = bytes.fromhex("00" * 32)

    async with factory() as s:
        t1 = await seed._ensure_thread(s)  # type: ignore[attr-defined]
        _ = await seed._ensure_messages(s, t1, master)  # type: ignore[attr-defined]
        q1 = await seed._ensure_quote(s, t1.order_id)  # type: ignore[attr-defined]
        await s.commit()
        tid1 = t1.id
        qid1 = q1.quote_id

    async with factory() as s:
        t2 = await seed._ensure_thread(s)  # type: ignore[attr-defined]
        msgs2 = await seed._ensure_messages(s, t2, master)  # type: ignore[attr-defined]
        q2 = await seed._ensure_quote(s, t2.order_id)  # type: ignore[attr-defined]
        await s.commit()
        assert t2.id == tid1
        assert q2.quote_id == qid1
        assert len(msgs2) == 2
        from sqlalchemy import select

        cnt_t = (await s.execute(select(MessagingThread))).scalars().all()
        assert len(cnt_t) == 1
        cnt_m = (await s.execute(select(MessagingMessage))).scalars().all()
        assert len(cnt_m) == 2
        cnt_q = (await s.execute(select(QuoteState))).scalars().all()
        assert len(cnt_q) == 1

    await engine.dispose()
