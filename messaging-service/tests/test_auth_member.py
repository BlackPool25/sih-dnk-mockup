"""Tests for app.services.auth — JWT + member-check + sahayak observer."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest
from fastapi import HTTPException, Request

from app.models import MessagingThread
from app.services.auth import AuthUser, get_current_user, require_member, require_member_for_write

SECRET = "test-jwt-secret-that-is-at-least-32-chars-long!!!"
ALGO = "HS256"


def _make_token(sub: str, role: str, email: str) -> str:
    from datetime import UTC, datetime, timedelta

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


def _request_with_token(token: str | None, use_header: bool = True, use_query: bool = False) -> Request:
    headers: list[tuple[bytes, bytes]] = []
    if token is not None and use_header:
        headers.append((b"authorization", f"Bearer {token}".encode()))
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/messaging/threads/123/messages",
        "headers": headers,
        "query_string": f"token={token}".encode() if (use_query and token) else b"",
        "server": ("testserver", 80),
        "scheme": "http",
        "root_path": "",
    }
    req = Request(scope)
    # also set query_params via scope; Request parses query_string automatically
    return req


def test_get_current_user_401_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", ALGO)
    req = _request_with_token(None, use_header=False, use_query=False)
    import asyncio

    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_current_user(req))
    assert exc.value.status_code == 401


def test_get_current_user_401_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", ALGO)
    req = _request_with_token("invalid.token.here", use_header=True)
    import asyncio

    with pytest.raises(HTTPException) as exc:
        asyncio.run(get_current_user(req))
    assert exc.value.status_code == 401


def test_get_current_user_ok_via_header(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", ALGO)
    seller_id = str(uuid.uuid4())
    token = _make_token(seller_id, "seller", "seller@test.com")
    req = _request_with_token(token, use_header=True, use_query=False)
    import asyncio

    user = asyncio.run(get_current_user(req))
    assert user["user_id"] == seller_id
    assert user["role"] == "seller"


def test_get_current_user_ok_via_query_param(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", SECRET)
    monkeypatch.setenv("JWT_ALGORITHM", ALGO)
    buyer_id = str(uuid.uuid4())
    token = _make_token(buyer_id, "buyer", "buyer@test.com")
    # No header, token in ?token=
    req = _request_with_token(token, use_header=False, use_query=True)
    import asyncio

    user = asyncio.run(get_current_user(req))
    assert user["user_id"] == buyer_id
    assert user["role"] == "buyer"


def _mock_session_with_thread(thread: MessagingThread | None) -> AsyncMock:
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = thread
    mock_session = AsyncMock()
    mock_session.execute.return_value = mock_result
    return mock_session


def _make_thread(seller_id: uuid.UUID, buyer_id: uuid.UUID) -> MessagingThread:
    # Construct without DB roundtrip
    t = MessagingThread(
        id=uuid.uuid4(),
        order_id=uuid.uuid4(),
        seller_id=seller_id,
        buyer_id=buyer_id,
    )
    return t


@pytest.mark.asyncio
async def test_require_member_seller_allowed() -> None:
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    thread = _make_thread(seller, buyer)
    session = _mock_session_with_thread(thread)
    user: AuthUser = {"user_id": str(seller), "role": "seller", "email": "s@test.com"}
    out = await require_member(str(thread.id), user, session)  # type: ignore[arg-type]
    assert out.id == thread.id


@pytest.mark.asyncio
async def test_require_member_buyer_allowed() -> None:
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    thread = _make_thread(seller, buyer)
    session = _mock_session_with_thread(thread)
    user: AuthUser = {"user_id": str(buyer), "role": "buyer", "email": "b@test.com"}
    out = await require_member(str(thread.id), user, session)  # type: ignore[arg-type]
    assert out.id == thread.id


@pytest.mark.asyncio
async def test_require_member_sahayak_allowed_read() -> None:
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    thread = _make_thread(seller, buyer)
    session = _mock_session_with_thread(thread)
    user: AuthUser = {"user_id": str(uuid.uuid4()), "role": "sahayak", "email": "sahayak@test.com"}
    out = await require_member(str(thread.id), user, session)  # type: ignore[arg-type]
    assert out.id == thread.id


@pytest.mark.asyncio
async def test_require_member_403_non_member() -> None:
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    thread = _make_thread(seller, buyer)
    session = _mock_session_with_thread(thread)
    outsider: AuthUser = {"user_id": str(uuid.uuid4()), "role": "buyer", "email": "outsider@test.com"}
    with pytest.raises(HTTPException) as exc:
        await require_member(str(thread.id), outsider, session)  # type: ignore[arg-type]
    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_require_member_404_not_found() -> None:
    session = _mock_session_with_thread(None)
    user: AuthUser = {"user_id": str(uuid.uuid4()), "role": "seller", "email": "s@test.com"}
    with pytest.raises(HTTPException) as exc:
        await require_member(str(uuid.uuid4()), user, session)  # type: ignore[arg-type]
    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_sahayak_post_403_observer() -> None:
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    thread = _make_thread(seller, buyer)
    session = _mock_session_with_thread(thread)
    sahayak: AuthUser = {"user_id": str(uuid.uuid4()), "role": "sahayak", "email": "sahayak@test.com"}
    # read allowed
    await require_member(str(thread.id), sahayak, session)  # type: ignore[arg-type]
    # write denied
    with pytest.raises(HTTPException) as exc:
        await require_member_for_write(str(thread.id), sahayak, session)  # type: ignore[arg-type]
    assert exc.value.status_code == 403
    assert "Sahayak" in exc.value.detail


@pytest.mark.asyncio
async def test_seller_write_allowed() -> None:
    seller = uuid.uuid4()
    buyer = uuid.uuid4()
    thread = _make_thread(seller, buyer)
    session = _mock_session_with_thread(thread)
    user: AuthUser = {"user_id": str(seller), "role": "seller", "email": "s@test.com"}
    out = await require_member_for_write(str(thread.id), user, session)  # type: ignore[arg-type]
    assert out.id == thread.id
