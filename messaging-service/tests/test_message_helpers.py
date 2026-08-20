"""Helpers coverage — decrypt preview, attachments, master key, before parsing."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

import pytest

from app.routers.messages import (
    _attachment_to_meta,
    _attachments_from_jsonb,
    _decrypt_preview,
    _encrypt_preview,
    _master_key,
)
from app.services.crypto import encrypt_thread_message


def test_encrypt_decrypt_preview_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", "00" * 32)
    mk = _master_key()
    tid = str(uuid.uuid4())
    enc = _encrypt_preview(tid, "hello preview", mk)
    # stored is json
    dec = _decrypt_preview(tid, enc, mk)
    assert dec == "hello preview"


def test_decrypt_preview_none_and_legacy() -> None:
    mk = bytes.fromhex("00" * 32)
    assert _decrypt_preview("tid", None, mk) is None
    # legacy colon form
    tid = str(uuid.uuid4())
    enc = encrypt_thread_message("legacy hello", tid, mk)
    legacy = f"{enc['ciphertext_b64']}:{enc['nonce_b64']}"
    assert _decrypt_preview(tid, legacy, mk) == "legacy hello"
    # corrupt
    assert _decrypt_preview(tid, "not-a-json-or-colon", mk) is None
    assert _decrypt_preview(tid, json.dumps({"ciphertext_b64": "bad", "nonce_b64": "bad"}), mk) is None


def test_attachments_helpers() -> None:
    assert _attachments_from_jsonb(None) is None
    assert _attachments_from_jsonb([]) is None
    assert _attachments_from_jsonb("bad") is None  # type: ignore[arg-type]
    meta = _attachment_to_meta({"filename": "a.txt", "content_type": "text/plain", "size_bytes": 10})
    assert meta is not None
    assert meta.filename == "a.txt"
    assert _attachment_to_meta({"filename": "a"}) is None
    assert _attachment_to_meta("not dict") is None  # type: ignore[arg-type]
    raw = [{"filename": "a.txt", "content_type": "text/plain", "size_bytes": 10}, {"bad": 1}]
    out = _attachments_from_jsonb(raw)
    assert out is not None
    assert len(out) == 1


def test_master_key_variants(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", "aa" * 32)
    mk = _master_key()
    assert len(mk) == 32
    assert mk == bytes.fromhex("aa" * 32)


def test_before_invalid_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    import asyncio

    from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
    from httpx import ASGITransport, AsyncClient
    import jwt
    from app.main import app
    from app.routers.messages import get_session as messages_get_session
    from app.routers.ws import get_session as ws_get_session

    SECRET = "test-jwt-secret-that-is-at-least-32-chars-long!!!"
    monkeypatch.setenv("JWT_SECRET_KEY", SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", "HS256")
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", "00" * 32)

    from sqlalchemy import text as sa_text

    def _create_sync(sync_conn):  # type: ignore[no-untyped-def]
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

    async def _run() -> None:
        engine = create_async_engine("sqlite+aiosqlite:///:memory:")
        async with engine.begin() as conn:
            await conn.run_sync(_create_sync)
        factory = async_sessionmaker(engine, expire_on_commit=False)

        async def override():  # type: ignore[no-untyped-def]
            async with factory() as s:
                yield s

        app.dependency_overrides[messages_get_session] = override
        app.dependency_overrides[ws_get_session] = override

        # create a thread directly then try invalid before via HTTP
        import uuid as _uuid

        tid = _uuid.uuid4()
        now = datetime.now(timezone.utc)
        from app.models import MessagingThread as MT

        async with factory() as s:
            s.add(MT(id=tid, order_id=_uuid.uuid4(), seller_id=_uuid.uuid4(), buyer_id=_uuid.uuid4(), created_at=now))
            await s.commit()

        # use a real seller that is not member will 403, so create token for that seller
        # instead insert thread with known seller/buyer
        seller = _uuid.uuid4()
        buyer = _uuid.uuid4()
        tid2 = _uuid.uuid4()
        async with factory() as s:
            s.add(MT(id=tid2, order_id=_uuid.uuid4(), seller_id=seller, buyer_id=buyer, created_at=now))
            await s.commit()

        def _tok(sub: str, role: str) -> str:
            import datetime as dt

            n = dt.datetime.now(dt.timezone.utc)
            return jwt.encode(
                {"sub": sub, "role": role, "email": "x@test.com", "iat": n, "exp": n + dt.timedelta(hours=1), "jti": str(_uuid.uuid4())},
                SECRET,
                algorithm="HS256",
            )

        tok = _tok(str(seller), "seller")
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as tc:
            r = await tc.get(f"/messages/threads/{tid2}/messages?before=not-a-date", headers={"Authorization": f"Bearer {tok}"})
            assert r.status_code == 422
            r2 = await tc.get(f"/messages/threads/{tid2}/poll?since=bad-date", headers={"Authorization": f"Bearer {tok}"})
            assert r2.status_code == 422
        app.dependency_overrides.clear()
        await engine.dispose()

    asyncio.run(_run())
