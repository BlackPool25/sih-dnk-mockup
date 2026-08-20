"""Messages router integration — inbox, threads, send, poll, attachments."""

from __future__ import annotations

import io
import uuid
from datetime import UTC, datetime, timedelta

import jwt
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.main import app
from app.routers.messages import get_session as messages_get_session
from app.routers.ws import get_session as ws_get_session

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


def _create_messaging_tables_sqlite(sync_conn):  # type: ignore[no-untyped-def]
    # JSONB is postgres-only; render attachments as JSON/TEXT for sqlite
    from sqlalchemy import text

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


async def _make_app_with_db(monkeypatch: pytest.MonkeyPatch):  # type: ignore[no-untyped-def]
    monkeypatch.setenv("JWT_SECRET_KEY", SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", ALGO)
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", MASTER_HEX)
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", pool_pre_ping=True)
    async with engine.begin() as conn:
        await conn.run_sync(_create_messaging_tables_sqlite)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def override():  # type: ignore[no-untyped-def]
        async with factory() as session:
            yield session

    app.dependency_overrides[messages_get_session] = override
    app.dependency_overrides[ws_get_session] = override
    return engine, factory


@pytest.mark.asyncio
async def test_thread_create_idempotent_and_inbox_paged(monkeypatch: pytest.MonkeyPatch) -> None:
    engine, _ = await _make_app_with_db(monkeypatch)
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    seller_tok = _token(str(seller), "seller", "seller@test.com")
    buyer_tok = _token(str(buyer), "buyer", "buyer@test.com")
    sahayak_tok = _token(str(uuid.uuid4()), "sahayak", "sahayak@test.com")
    order_id = uuid.uuid4()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as tc:
        # create thread
        resp = await tc.post(
            "/messages/threads",
            json={"order_id": str(order_id), "seller_id": str(seller), "buyer_id": str(buyer)},
            headers={"Authorization": f"Bearer {seller_tok}"},
        )
        assert resp.status_code == 201, resp.text
        tid = resp.json()["id"]

        # idempotent re-create returns same id
        resp2 = await tc.post(
            "/messages/threads",
            json={"order_id": str(order_id), "seller_id": str(seller), "buyer_id": str(buyer)},
            headers={"Authorization": f"Bearer {seller_tok}"},
        )
        assert resp2.status_code == 201
        assert resp2.json()["id"] == tid

        # inbox seller sees 1, buyer sees 1, sahayak sees 1
        for tok in (seller_tok, buyer_tok, sahayak_tok):
            inbox = await tc.get("/messages/inbox?limit=20&offset=0", headers={"Authorization": f"Bearer {tok}"})
            assert inbox.status_code == 200
            assert inbox.json()["total"] == 1
            assert inbox.json()["mocked"] is True

        # paging: limit 1 offset 0 and offset 1
        p1 = await tc.get("/messages/inbox?limit=1&offset=0", headers={"Authorization": f"Bearer {seller_tok}"})
        assert p1.status_code == 200
        assert len(p1.json()["items"]) == 1
        p2 = await tc.get("/messages/inbox?limit=1&offset=1", headers={"Authorization": f"Bearer {seller_tok}"})
        assert p2.status_code == 200
        assert len(p2.json()["items"]) == 0

        # outsider sees 0
        outsider_tok = _token(str(uuid.uuid4()), "buyer", "out@test.com")
        out_inbox = await tc.get("/messages/inbox", headers={"Authorization": f"Bearer {outsider_tok}"})
        assert out_inbox.status_code == 200
        assert out_inbox.json()["total"] == 0

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_post_message_encrypted_and_list(monkeypatch: pytest.MonkeyPatch) -> None:
    engine, _ = await _make_app_with_db(monkeypatch)
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    seller_tok = _token(str(seller), "seller", "seller@test.com")
    buyer_tok = _token(str(buyer), "buyer", "buyer@test.com")
    order_id = uuid.uuid4()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as tc:
        # create thread
        resp = await tc.post(
            "/messages/threads",
            json={"order_id": str(order_id), "seller_id": str(seller), "buyer_id": str(buyer)},
            headers={"Authorization": f"Bearer {seller_tok}"},
        )
        tid = resp.json()["id"]

        # seller hello
        r1 = await tc.post(
            f"/messages/threads/{tid}/messages",
            headers={"Authorization": f"Bearer {seller_tok}"},
            data={"body": "hello from seller"},
        )
        assert r1.status_code == 201, r1.text
        assert r1.json()["body"] == "hello from seller"
        assert r1.json()["mocked"] is True

        # buyer reply with attachment
        r2 = await tc.post(
            f"/messages/threads/{tid}/messages",
            headers={"Authorization": f"Bearer {buyer_tok}"},
            data={"body": "buyer reply"},
            files={"attachments": ("note.txt", io.BytesIO(b"hello attachment"), "text/plain")},
        )
        assert r2.status_code == 201, r2.text
        assert r2.json()["body"] == "buyer reply"
        assert r2.json()["attachments"] is not None

        # list messages paged
        lst = await tc.get(f"/messages/threads/{tid}/messages?limit=20&offset=0", headers={"Authorization": f"Bearer {seller_tok}"})
        assert lst.status_code == 200
        assert lst.json()["total"] == 2
        bodies = [it["body"] for it in lst.json()["items"]]
        assert bodies == ["hello from seller", "buyer reply"]

        # before filter
        lst_before = await tc.get(
            f"/messages/threads/{tid}/messages?limit=20&offset=0&before=2099-01-01T00:00:00Z",
            headers={"Authorization": f"Bearer {seller_tok}"},
        )
        assert lst_before.status_code == 200
        assert lst_before.json()["total"] == 2

        # poll since
        poll_all = await tc.get(f"/messages/threads/{tid}/poll", headers={"Authorization": f"Bearer {seller_tok}"})
        assert poll_all.status_code == 200
        assert poll_all.json()["total"] == 2

        poll_since = await tc.get(
            f"/messages/threads/{tid}/poll?since=2024-01-01T00:00:00Z", headers={"Authorization": f"Bearer {seller_tok}"}
        )
        assert poll_since.status_code == 200
        assert poll_since.json()["total"] == 2

        # sahayak cannot post
        sahayak_tok = _token(str(uuid.uuid4()), "sahayak", "sahayak@test.com")
        r3 = await tc.post(
            f"/messages/threads/{tid}/messages",
            headers={"Authorization": f"Bearer {sahayak_tok}"},
            data={"body": "sahayak tries"},
        )
        assert r3.status_code == 403

        # non-member cannot read
        outsider_tok = _token(str(uuid.uuid4()), "buyer", "out@test.com")
        lst_fail = await tc.get(f"/messages/threads/{tid}/messages", headers={"Authorization": f"Bearer {outsider_tok}"})
        assert lst_fail.status_code == 403

    app.dependency_overrides.clear()
    await engine.dispose()


@pytest.mark.asyncio
async def test_attachment_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    engine, _ = await _make_app_with_db(monkeypatch)
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    seller_tok = _token(str(seller), "seller", "seller@test.com")
    order_id = uuid.uuid4()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as tc:
        resp = await tc.post(
            "/messages/threads",
            json={"order_id": str(order_id), "seller_id": str(seller), "buyer_id": str(buyer)},
            headers={"Authorization": f"Bearer {seller_tok}"},
        )
        tid = resp.json()["id"]

        # disallowed content-type
        r_bad = await tc.post(
            f"/messages/threads/{tid}/messages",
            headers={"Authorization": f"Bearer {seller_tok}"},
            data={"body": "bad type"},
            files={"attachments": ("evil.bin", io.BytesIO(b"x"), "application/octet-stream")},
        )
        assert r_bad.status_code == 422

    app.dependency_overrides.clear()
    await engine.dispose()
