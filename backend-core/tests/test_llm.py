"""Tests for the LLM conversation state router."""

from __future__ import annotations

import asyncio
import uuid

import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient

from auth.models import User, UserRole
from auth.services.jwt import create_access_token
from auth.services.password import hash_password
from storage.config import settings
from storage.db import get_session
from storage.redis import get_redis

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


async def _create_second_seller() -> dict[str, str]:
    """Create an ephemeral second seller for the 403 (other user) test."""
    email = f"seller2_{uuid.uuid4().hex[:8]}@llmtest.com"

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
        settings.JWT_SECRET_KEY,
        settings.JWT_ALGORITHM,
        60,
    )
    return {"user_id": user_id, "email": email, "token": token}


# ---------------------------------------------------------------------------
# POST /api/llm/chat — create new conversation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_chat_201(test_seller: dict[str, str]) -> None:
    """A new chat returns 201 with conv_id, step=init, empty fields."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/llm/chat",
            json={"message": "Hello, I want to create an order", "language": "en"},
            headers=_auth_header(test_seller["token"]),
        )

    assert response.status_code == 201
    data = response.json()
    assert "conversation_id" in data
    assert len(data["conversation_id"]) == 32  # uuid4 hex
    assert data["user_id"] == test_seller["user_id"]
    assert data["language"] == "en"
    assert data["current_step"] == "init"
    assert data["filled_fields"] == {}
    assert data["pending_fields"] == []
    assert len(data["history"]) == 1
    assert data["history"][0]["role"] == "user"
    assert data["history"][0]["content"] == "Hello, I want to create an order"


# ---------------------------------------------------------------------------
# POST /api/llm/chat — continue existing conversation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_continue_chat_state_updates(test_seller: dict[str, str]) -> None:
    """Continuing a chat appends to history and preserves state."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create
        r1 = await client.post(
            "/api/llm/chat",
            json={"message": "Start", "language": "en"},
            headers=_auth_header(test_seller["token"]),
        )
        assert r1.status_code == 201
        conv_id = r1.json()["conversation_id"]

        # 2. Continue
        r2 = await client.post(
            "/api/llm/chat",
            json={
                "conversation_id": conv_id,
                "message": "My firm is Acme Corp",
                "language": "en",
            },
            headers=_auth_header(test_seller["token"]),
        )

    assert r2.status_code == 201
    data = r2.json()
    assert data["conversation_id"] == conv_id
    assert len(data["history"]) == 2
    assert data["history"][0]["content"] == "Start"
    assert data["history"][1]["content"] == "My firm is Acme Corp"
    assert data["current_step"] == "init"


# ---------------------------------------------------------------------------
# GET /api/llm/session/{session_id} — retrieve state
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_session_correct_step(test_seller: dict[str, str]) -> None:
    """GET returns the current conversation state including step."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create
        r = await client.post(
            "/api/llm/chat",
            json={"message": "Create order", "language": "en"},
            headers=_auth_header(test_seller["token"]),
        )
        conv_id = r.json()["conversation_id"]

        # Manually advance the step via Redis (simulating LLM backend update)
        redis = get_redis()
        await redis.hset(f"llm:conv:{conv_id}", "current_step", "firm_name")
        await redis.hset(f"llm:conv:{conv_id}", "filled_fields", '{"firm_name":"Acme"}')

        # GET
        r = await client.get(
            f"/api/llm/session/{conv_id}",
            headers=_auth_header(test_seller["token"]),
        )

    assert r.status_code == 200
    data = r.json()
    assert data["conversation_id"] == conv_id
    assert data["current_step"] == "firm_name"
    assert data["filled_fields"] == {"firm_name": "Acme"}


# ---------------------------------------------------------------------------
# 24h TTL — key expires
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_conversation_ttl_expiry(test_seller: dict[str, str]) -> None:
    """After the TTL elapses the conversation returns 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create
        r = await client.post(
            "/api/llm/chat",
            json={"message": "ttl test", "language": "en"},
            headers=_auth_header(test_seller["token"]),
        )
        conv_id = r.json()["conversation_id"]

        # Force-expire the key
        redis = get_redis()
        await redis.expire(f"llm:conv:{conv_id}", 1)

        await asyncio.sleep(1.5)

        # Should be gone
        r2 = await client.get(
            f"/api/llm/session/{conv_id}",
            headers=_auth_header(test_seller["token"]),
        )

    assert r2.status_code == 404


# ---------------------------------------------------------------------------
# 403 — other user tries to access
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_other_user_forbidden(test_seller: dict[str, str]) -> None:
    """A different seller cannot access another seller's conversation."""
    second_seller = await _create_second_seller()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Seller A creates a conversation
        r = await client.post(
            "/api/llm/chat",
            json={"message": "private", "language": "en"},
            headers=_auth_header(test_seller["token"]),
        )
        conv_id = r.json()["conversation_id"]

        # Seller B tries to GET it
        r2 = await client.get(
            f"/api/llm/session/{conv_id}",
            headers=_auth_header(second_seller["token"]),
        )

    assert r2.status_code == 403


@pytest.mark.asyncio
async def test_other_user_delete_forbidden(test_seller: dict[str, str]) -> None:
    """A different seller cannot delete another seller's conversation."""
    second_seller = await _create_second_seller()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Seller A creates a conversation
        r = await client.post(
            "/api/llm/chat",
            json={"message": "private", "language": "en"},
            headers=_auth_header(test_seller["token"]),
        )
        conv_id = r.json()["conversation_id"]

        # Seller B tries to DELETE it
        r2 = await client.delete(
            f"/api/llm/session/{conv_id}",
            headers=_auth_header(second_seller["token"]),
        )

    assert r2.status_code == 403


# ---------------------------------------------------------------------------
# 404 — expired / non-existent conversation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_nonexistent_session_404(test_seller: dict[str, str]) -> None:
    """Requesting a non-existent session returns 404."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        fake_id = uuid.uuid4().hex
        r = await client.get(
            f"/api/llm/session/{fake_id}",
            headers=_auth_header(test_seller["token"]),
        )

    assert r.status_code == 404


# ---------------------------------------------------------------------------
# DELETE — successful deletion
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_session_204(test_seller: dict[str, str]) -> None:
    """Owner can delete their own conversation (204 No Content)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create
        r = await client.post(
            "/api/llm/chat",
            json={"message": "to be deleted", "language": "en"},
            headers=_auth_header(test_seller["token"]),
        )
        conv_id = r.json()["conversation_id"]

        # Delete
        r2 = await client.delete(
            f"/api/llm/session/{conv_id}",
            headers=_auth_header(test_seller["token"]),
        )

    assert r2.status_code == 204

    # Verify it's gone
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r3 = await client.get(
            f"/api/llm/session/{conv_id}",
            headers=_auth_header(test_seller["token"]),
        )
    assert r3.status_code == 404


# ---------------------------------------------------------------------------
# Auth — unauthenticated / wrong role
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_chat_unauthenticated(test_seller: dict[str, str]) -> None:
    """No token → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/llm/chat",
            json={"message": "hi", "language": "en"},
        )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_chat_buyer_forbidden(test_buyer: dict[str, str]) -> None:
    """Buyer role → 403 from require_role('seller')."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.post(
            "/api/llm/chat",
            json={"message": "hi", "language": "en"},
            headers=_auth_header(test_buyer["token"]),
        )
    assert r.status_code == 403
