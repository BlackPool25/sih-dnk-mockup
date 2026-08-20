"""JWT auth + per-thread member-check for messaging-service.

Reuses storage.config settings (JWT_SECRET_KEY, JWT_ALGORITHM) and
auth.services.jwt decode semantics. Supports both HTTP Authorization
Bearer header and WS ?token= query param.

Member-check:
  - Fetch messaging_threads row by thread_id
  - Allow if user.role == "sahayak" (read-only observer) OR
    user.user_id in (seller_id, buyer_id)
  - Otherwise 403
  - Sahayak POST/write → 403 (observer cannot send messages)

401/403 matrix (mirrors auth.middleware.JWTAuthMiddleware):
  401 missing/invalid/expired token, malformed claims
  403 authenticated but not a member of the thread
  403 sahayak attempting write
  404 thread not found (subclass of 403 matrix, distinct for UX)
"""

from __future__ import annotations

import os
import uuid
from typing import TypedDict

import jwt
from fastapi import HTTPException, Request, WebSocket
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import MessagingThread


class AuthUser(TypedDict):
    """Authenticated user identity extracted from JWT."""

    user_id: str
    role: str
    email: str


def _get_jwt_settings() -> tuple[str, str]:
    """Return (secret_key, algorithm) from storage.config or env fallback."""
    try:
        from storage.config import settings as storage_settings  # type: ignore[import-untyped]

        return str(storage_settings.JWT_SECRET_KEY), str(storage_settings.JWT_ALGORITHM)
    except Exception:
        secret = os.environ.get("JWT_SECRET_KEY", "")
        algo = os.environ.get("JWT_ALGORITHM", "HS256")
        return secret, algo


def _decode_token(token: str) -> AuthUser:
    """Decode and verify a JWT, returning AuthUser or raising HTTPException 401."""
    secret, algo = _get_jwt_settings()
    if not secret:
        raise HTTPException(status_code=401, detail="JWT configuration missing")
    try:
        payload: dict[str, object] = jwt.decode(token, secret, algorithms=[algo])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired") from None
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from None

    sub = payload.get("sub")
    role = payload.get("role")
    email = payload.get("email")
    if not isinstance(sub, str) or not isinstance(role, str) or not isinstance(email, str):
        raise HTTPException(status_code=401, detail="Token payload missing required claims (sub, role, email)")
    if not sub or not role or not email:
        raise HTTPException(status_code=401, detail="Token payload missing required claims (sub, role, email)")
    return AuthUser(user_id=sub, role=role, email=email)


def _extract_token_from_request(request: Request) -> str | None:
    """Extract Bearer token from Authorization header or ?token query param."""
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        tok = auth_header[len("Bearer ") :].strip()
        if tok:
            return tok
    # Fallback for WS-style query param on HTTP polling path as well
    token_qs = request.query_params.get("token")
    if token_qs and token_qs.strip():
        return token_qs.strip()
    return None


def _extract_token_from_ws(websocket: WebSocket) -> str | None:
    """Extract Bearer token from WS headers or ?token query param."""
    auth_header = websocket.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        tok = auth_header[len("Bearer ") :].strip()
        if tok:
            return tok
    token_qs = websocket.query_params.get("token")
    if token_qs and token_qs.strip():
        return token_qs.strip()
    return None


async def get_current_user(request: Request) -> AuthUser:
    """FastAPI dependency: return authenticated user or raise 401.

    Checks Authorization: Bearer <token> first, then ?token= query param
    (for WebSocket upgrade and polling fallback).
    """
    token = _extract_token_from_request(request)
    if token is None:
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")
    return _decode_token(token)


async def get_current_user_ws(websocket: WebSocket) -> AuthUser:
    """WebSocket variant: extract token from header or ?token= and validate."""
    token = _extract_token_from_ws(websocket)
    if token is None:
        raise HTTPException(status_code=401, detail="Missing or malformed Authorization header")
    return _decode_token(token)


def _parse_thread_uuid(thread_id: str | uuid.UUID) -> uuid.UUID:
    """Parse thread_id string to UUID, raising 404 if malformed."""
    if isinstance(thread_id, uuid.UUID):
        return thread_id
    try:
        return uuid.UUID(thread_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Thread not found") from None


async def require_member(
    thread_id: str | uuid.UUID,
    user: AuthUser,
    session: AsyncSession,
) -> MessagingThread:
    """Enforce that *user* is a member of *thread_id* (read access).

    - sahayak role → allowed (read-only observer)
    - seller_id / buyer_id match → allowed
    - otherwise → 403
    - thread not found → 404

    Returns the MessagingThread row on success.

    Raises:
        HTTPException(404): thread does not exist
        HTTPException(403): authenticated but not a member
    """
    tid = _parse_thread_uuid(thread_id)
    result = await session.execute(select(MessagingThread).where(MessagingThread.id == tid))
    thread = result.scalar_one_or_none()
    if thread is None:
        raise HTTPException(status_code=404, detail="Thread not found")

    role = user["role"]
    user_id = user["user_id"]

    if role == "sahayak":
        return thread

    # Compare string forms to handle UUID vs str callers
    seller = str(thread.seller_id)
    buyer = str(thread.buyer_id)
    if user_id == seller or user_id == buyer:
        return thread

    raise HTTPException(status_code=403, detail="Not a member of this thread")


async def require_member_for_write(
    thread_id: str | uuid.UUID,
    user: AuthUser,
    session: AsyncSession,
) -> MessagingThread:
    """Enforce write access: member + sahayak observer cannot POST.

    Calls require_member for read check, then denies sahayak role with 403.

    Raises:
        HTTPException(403): sahayak attempting write or non-member
        HTTPException(404): thread not found
    """
    thread = await require_member(thread_id, user, session)
    if user["role"] == "sahayak":
        raise HTTPException(status_code=403, detail="Sahayak observer cannot send messages")
    return thread


def assert_can_write(user: AuthUser) -> None:
    """Synchronous helper: raise 403 if user is sahayak observer attempting write."""
    if user["role"] == "sahayak":
        raise HTTPException(status_code=403, detail="Sahayak observer cannot send messages")


def is_sahayak(user: AuthUser) -> bool:
    """Return True if user is sahayak observer."""
    return user["role"] == "sahayak"
