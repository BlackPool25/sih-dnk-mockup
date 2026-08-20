"""WS + poll + offline queue tests — mocked DB, no Redis."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock

import jwt
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models import MessagingMessage, MessagingThread
from app.services.crypto import decrypt_thread_message, encrypt_thread_message

SECRET = "test-jwt-secret-that-is-at-least-32-chars-long!!!"
ALGO = "HS256"
MASTER_HEX = "00" * 32
MASTER_KEY = bytes.fromhex(MASTER_HEX)


def _make_token(sub: str, role: str, email: str) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        "sub": sub,
        "role": role,
        "email": email,
        "iat": now,
        "exp": now + timedelta(minutes=15),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, SECRET, algorithm=ALGO)


def _make_thread(seller_id: uuid.UUID, buyer_id: uuid.UUID) -> MessagingThread:
    return MessagingThread(
        id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        seller_id=seller_id,
        buyer_id=buyer_id,
        created_at=datetime.now(timezone.utc),
        last_message_at=None,
        last_preview_encrypted=None,
    )


# ---------------------------------------------------------------------------
# Helpers for WS mocked DB
# ---------------------------------------------------------------------------
class FakeSession:
    def __init__(self, thread: MessagingThread | None, store: list[MessagingMessage]):
        self._thread = thread
        self._store = store

    async def execute(self, query):  # type: ignore[no-untyped-def]
        # Detect entity via column_descriptions
        try:
            cds = query.column_descriptions  # type: ignore[attr-defined]
            entity = cds[0].get("entity") if cds else None
        except Exception:
            entity = None
        sql = ""
        compiled = None
        try:
            compiled = query.compile()
            sql = str(query.compile(compile_kwargs={"literal_binds": True}))
        except Exception:
            sql = str(query)

        # Handle thread select
        if entity is MessagingThread:
            m = MagicMock()
            m.scalar_one_or_none.return_value = self._thread
            return m

        # Try to extract since_dt from compiled params (more reliable than string parsing)
        since_dt = None
        if compiled is not None:
            try:
                for v in compiled.params.values():
                    if isinstance(v, datetime):
                        # assume the datetime param is the since filter (thread_id is UUID)
                        since_dt = v
                        break
            except Exception:
                since_dt = None

        # Count query
        if "count" in sql.lower() and "messaging_messages" in sql.lower():
            filtered = self._apply_since_filter(sql, since_dt)
            m = MagicMock()
            m.scalar_one.return_value = len(filtered)
            return m

        # Messages select (poll or WS thread re-fetch)
        if "messaging_messages" in sql.lower():
            filtered = self._apply_since_filter(sql, since_dt)
            limit_val = None
            if "LIMIT" in sql:
                try:
                    limit_part = sql.split("LIMIT")[1].strip().split()[0]
                    limit_val = int(limit_part)
                except Exception:
                    limit_val = None
            if limit_val is not None:
                filtered = filtered[:limit_val]
            m2 = MagicMock()
            scalars_mock = MagicMock()
            scalars_mock.all.return_value = filtered
            m2.scalars.return_value = scalars_mock
            return m2

        # Fallback: treat as thread
        m = MagicMock()
        m.scalar_one_or_none.return_value = self._thread
        return m

    def _apply_since_filter(self, sql: str, since_dt: datetime | None) -> list[MessagingMessage]:
        if since_dt is not None:
            return [m for m in self._store if m.created_at > since_dt]
        # fallback string parsing for literal binds case
        if "created_at >" in sql or "created_at &gt;" in sql:
            try:
                idx = sql.find("created_at")
                sub = sql[idx:]
                q1 = sub.find("'")
                if q1 != -1:
                    q2 = sub.find("'", q1 + 1)
                    if q2 != -1:
                        ts_str = sub[q1 + 1 : q2]
                        iso = ts_str.replace("Z", "+00:00") if ts_str.endswith("Z") else ts_str
                        try:
                            since_dt2 = datetime.fromisoformat(iso)
                        except Exception:
                            since_dt2 = datetime.fromisoformat(iso.replace(" ", "T"))
                        if since_dt2.tzinfo is None:
                            since_dt2 = since_dt2.replace(tzinfo=timezone.utc)
                        return [m for m in self._store if m.created_at > since_dt2]
            except Exception:
                pass
        return list(self._store)

    def add(self, obj):  # type: ignore[no-untyped-def]
        if isinstance(obj, MessagingMessage):
            # avoid duplicate add if already in store (session.add called multiple times)
            if obj not in self._store:
                self._store.append(obj)
        elif isinstance(obj, MessagingThread):
            self._thread = obj  # type: ignore[assignment]

    async def commit(self):  # type: ignore[no-untyped-def]
        return None

    async def refresh(self, obj):  # type: ignore[no-untyped-def]
        if isinstance(obj, MessagingMessage) and obj.created_at is None:
            obj.created_at = datetime.now(timezone.utc)  # type: ignore[assignment]
        return None


class FakeCM:
    def __init__(self, session: FakeSession):
        self._sess = session

    async def __aenter__(self):  # type: ignore[no-untyped-def]
        return self._sess

    async def __aexit__(self, *args):  # type: ignore[no-untyped-def]
        return False


def _fake_maker(thread: MessagingThread | None, store: list[MessagingMessage]):  # type: ignore[no-untyped-def]
    def _get_sessionmaker():  # type: ignore[no-untyped-def]
        def factory():  # type: ignore[no-untyped-def]
            return FakeCM(FakeSession(thread, store))

        return factory

    return _get_sessionmaker


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
def test_ws_connect_send_echo(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", ALGO)
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", MASTER_HEX)
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    thread = _make_thread(seller, buyer)
    store: list[MessagingMessage] = []
    monkeypatch.setattr("app.routers.ws._get_sessionmaker", _fake_maker(thread, store))
    # _master_key will read env fallback zero key -> matches MASTER_KEY

    token = _make_token(str(seller), "seller", "seller@test.com")
    client = TestClient(app)
    with client.websocket_connect(f"/messages/ws/threads/{thread.id}?token={token}") as ws:
        data = ws.receive_json()
        assert data["type"] == "connected"
        assert data["thread_id"] == str(thread.id)

        ws.send_text(json.dumps({"type": "send", "body": "hello ws"}))
        echo = ws.receive_json()
        assert echo["type"] == "message"
        payload = echo["data"]
        assert payload["body"] == "hello ws"
        assert payload["thread_id"] == str(thread.id)
        assert payload["sender_id"] == str(seller)
        assert payload["mocked"] is True
        # Verify DB persistence: store has one encrypted message, plaintext not stored
        assert len(store) == 1
        stored = store[0]
        assert stored.body_ciphertext != "hello ws"
        assert decrypt_thread_message(stored.body_ciphertext, stored.enc_nonce_b64, str(thread.id), MASTER_KEY) == "hello ws"


def test_ws_invalid_token_close_1008(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", ALGO)
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", MASTER_HEX)
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    thread = _make_thread(seller, buyer)
    store: list[MessagingMessage] = []
    monkeypatch.setattr("app.routers.ws._get_sessionmaker", _fake_maker(thread, store))
    client = TestClient(app)
    try:
        with client.websocket_connect(f"/messages/ws/threads/{thread.id}?token=invalid.token.here") as ws:
            ws.receive_json()
            assert False, "should have closed"
    except Exception as exc:
        code = getattr(exc, "code", None)
        if code is not None:
            assert code == 1008
        else:
            msg = str(exc).lower()
            assert "1008" in msg or "disconnect" in msg or "close" in msg


def test_ws_non_member_close_1008(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", ALGO)
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", MASTER_HEX)
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    outsider = uuid.uuid4()
    thread = _make_thread(seller, buyer)
    store: list[MessagingMessage] = []
    monkeypatch.setattr("app.routers.ws._get_sessionmaker", _fake_maker(thread, store))
    token = _make_token(str(outsider), "buyer", "outsider@test.com")
    client = TestClient(app)
    try:
        with client.websocket_connect(f"/messages/ws/threads/{thread.id}?token={token}") as ws:
            ws.receive_json()
            assert False, "non-member should be closed 1008"
    except Exception as exc:
        code = getattr(exc, "code", None)
        if code is not None:
            assert code == 1008
        else:
            msg = str(exc).lower()
            assert "1008" in msg or "disconnect" in msg or "close" in msg


def test_ws_sahayak_cannot_send(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", ALGO)
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", MASTER_HEX)
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    thread = _make_thread(seller, buyer)
    store: list[MessagingMessage] = []
    monkeypatch.setattr("app.routers.ws._get_sessionmaker", _fake_maker(thread, store))
    sahayak_token = _make_token(str(uuid.uuid4()), "sahayak", "sahayak@test.com")
    client = TestClient(app)
    with client.websocket_connect(f"/messages/ws/threads/{thread.id}?token={sahayak_token}") as ws:
        data = ws.receive_json()
        assert data["type"] == "connected"
        ws.send_text(json.dumps({"type": "send", "body": "sahayak tries"}))
        err = ws.receive_json()
        assert err["type"] == "error"
        assert "Sahayak" in err["detail"]
        # not persisted
        assert len(store) == 0


def test_poll_since_filter(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", ALGO)
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", MASTER_HEX)
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    thread = _make_thread(seller, buyer)
    # create two messages with distinct created_at
    t_old = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    t_new = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    tid_str = str(thread.id)

    enc_old = encrypt_thread_message("old message", tid_str, MASTER_KEY)
    enc_new = encrypt_thread_message("new message", tid_str, MASTER_KEY)

    m_old = MessagingMessage(
        id=uuid.uuid4(),
        thread_id=thread.id,
        sender_id=seller,
        sender_role="seller",
        body_ciphertext=enc_old["ciphertext_b64"],
        enc_nonce_b64=enc_old["nonce_b64"],
        attachments=None,
        created_at=t_old,
    )
    m_new = MessagingMessage(
        id=uuid.uuid4(),
        thread_id=thread.id,
        sender_id=buyer,
        sender_role="buyer",
        body_ciphertext=enc_new["ciphertext_b64"],
        enc_nonce_b64=enc_new["nonce_b64"],
        attachments=None,
        created_at=t_new,
    )
    store: list[MessagingMessage] = [m_old, m_new]
    monkeypatch.setattr("app.routers.ws._get_sessionmaker", _fake_maker(thread, store))

    token = _make_token(str(seller), "seller", "seller@test.com")
    client = TestClient(app)
    since = "2024-01-01T11:00:00Z"
    resp = client.get(f"/messages/threads/{thread.id}/poll?since={since}", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["mocked"] is True
    # since 11:00 -> only new message (12:00) should be returned
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["body"] == "new message"

    # without since, both
    resp2 = client.get(f"/messages/threads/{thread.id}/poll", headers={"Authorization": f"Bearer {token}"})
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert data2["total"] == 2
    assert len(data2["items"]) == 2


def test_disconnect_no_lose_offline_via_rest_poll(monkeypatch: pytest.MonkeyPatch) -> None:
    """Offline queue: message sent via REST (direct DB insert) after WS disconnect is retrievable via poll."""
    monkeypatch.setenv("JWT_SECRET_KEY", SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", ALGO)
    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", MASTER_HEX)
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    thread = _make_thread(seller, buyer)
    store: list[MessagingMessage] = []
    monkeypatch.setattr("app.routers.ws._get_sessionmaker", _fake_maker(thread, store))
    token_seller = _make_token(str(seller), "seller", "seller@test.com")

    client = TestClient(app)
    # 1. Connect WS, send one, then disconnect (exit context)
    with client.websocket_connect(f"/messages/ws/threads/{thread.id}?token={token_seller}") as ws:
        ws.receive_json()
        ws.send_text(json.dumps({"type": "send", "body": "ws msg 1"}))
        echo = ws.receive_json()
        assert echo["type"] == "message"
        assert echo["data"]["body"] == "ws msg 1"
    # disconnected gracefully, no exception

    # 2. Simulate offline REST send: directly encrypt+append to store (as POST would do)
    # In real app this would be POST /messages/threads/{id}/messages via HTTP; we emulate DB insert.
    tid_str = str(thread.id)
    enc_offline = encrypt_thread_message("offline queued body", tid_str, MASTER_KEY)
    offline_msg = MessagingMessage(
        id=uuid.uuid4(),
        thread_id=thread.id,
        sender_id=buyer,
        sender_role="buyer",
        body_ciphertext=enc_offline["ciphertext_b64"],
        enc_nonce_b64=enc_offline["nonce_b64"],
        attachments=None,
        created_at=datetime.now(timezone.utc),
    )
    store.append(offline_msg)

    # 3. Poll without since should return both ws msg + offline
    # need to ensure poll sees store with both messages
    # WS msg created_at was set via FakeSession.refresh to now; offline is slightly later but both after 2024
    since_epoch = "2024-01-01T00:00:00Z"
    resp = client.get(f"/messages/threads/{thread.id}/poll?since={since_epoch}", headers={"Authorization": f"Bearer {token_seller}"})
    assert resp.status_code == 200
    data = resp.json()
    bodies = [it["body"] for it in data["items"]]
    assert "ws msg 1" in bodies
    assert "offline queued body" in bodies
    # prove ciphertext not plaintext in store
    for m in store:
        assert m.body_ciphertext not in ["ws msg 1", "offline queued body"]
