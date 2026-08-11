"""Auth route definitions — register, login, refresh, logout, password reset, me."""

from __future__ import annotations

import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated

import jwt as pyjwt
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from storage.config import settings
from storage.db import get_session
from storage.redis import get_redis

from auth.deps import get_current_user
from auth.models import RefreshToken, User, UserRole
from auth.services.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    revoke_token,
)
from auth.services.password import hash_password, verify_password

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------


class RegisterRequest(BaseModel):
    email: str
    password: str
    role: str


class RegisterResponse(BaseModel):
    id: str
    email: str
    role: str
    created_at: str


class LoginRequest(BaseModel):
    email: str
    password: str


class UserInfo(BaseModel):
    id: str
    email: str
    role: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class LoginResponse(TokenResponse):
    user: UserInfo


class RefreshRequest(BaseModel):
    refresh_token: str


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetBody(BaseModel):
    token: str
    new_password: str


class MessageResponse(BaseModel):
    message: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _token_data(user: User) -> dict[str, str]:
    return {
        "sub": str(user.id),
        "role": str(user.role),
        "email": user.email,
    }


def _token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def _user_response(user: User) -> dict[str, object]:
    return {
        "id": str(user.id),
        "email": user.email,
        "role": str(user.role),
        "created_at": user.created_at.isoformat(),
    }


async def _issue_token_pair(
    user: User,
    redis_client,
) -> tuple[str, str, str]:
    """Create access + refresh tokens and persist the refresh token row.

    Returns (access_token, refresh_token, refresh_jti).
    """
    data = _token_data(user)
    access = create_access_token(
        data,
        settings.JWT_SECRET_KEY,
        settings.JWT_ALGORITHM,
        settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    refresh = create_refresh_token(
        data,
        settings.JWT_SECRET_KEY,
        settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )
    payload = decode_token(refresh, settings.JWT_SECRET_KEY, settings.JWT_ALGORITHM)
    jti = str(payload["jti"])
    exp = payload["exp"]
    expires_at = datetime.fromtimestamp(exp, tz=UTC)

    async with get_session() as session:
        rt = RefreshToken(
            user_id=user.id,
            token_hash=_token_hash(refresh),
            jti=jti,
            expires_at=expires_at,
        )
        session.add(rt)
        await session.commit()

    return access, refresh, jti


async def _revoke_refresh_in_db(jti: str) -> None:
    async with get_session() as session:
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        rt = result.scalar_one_or_none()
        if rt is not None:
            rt.revoked = True
            await session.commit()


async def _revoke_all_refresh_tokens_for_user(user_id: str) -> None:
    from uuid import UUID

    async with get_session() as session:
        result = await session.execute(
            select(RefreshToken).where(
                RefreshToken.user_id == UUID(user_id),
                RefreshToken.revoked == False,
            )
        )
        for rt in result.scalars():
            rt.revoked = True
        await session.commit()


# ---------------------------------------------------------------------------
# 1. POST /auth/register
# ---------------------------------------------------------------------------


@router.post("/register", status_code=201, response_model=RegisterResponse)
async def register(body: RegisterRequest) -> dict[str, object]:
    if body.role not in ("seller", "buyer"):
        raise HTTPException(
            status_code=400, detail="Forbidden role: use 'seller' or 'buyer'"
        )

    async with get_session() as session:
        existing = await session.execute(select(User).where(User.email == body.email))
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(status_code=409, detail="Email already registered")

        user = User(
            email=body.email,
            password_hash=hash_password(body.password),
            role=UserRole(body.role),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        return _user_response(user)


# ---------------------------------------------------------------------------
# 2. POST /auth/login
# ---------------------------------------------------------------------------


@router.post("/login", response_model=LoginResponse)
async def login(body: LoginRequest) -> dict[str, object]:
    async with get_session() as session:
        result = await session.execute(select(User).where(User.email == body.email))
        user = result.scalar_one_or_none()

        if user is None or not verify_password(body.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid email or password")

        redis_client = get_redis()
        access, refresh, _ = await _issue_token_pair(user, redis_client)

        return {
            "access_token": access,
            "refresh_token": refresh,
            "token_type": "bearer",
            "user": {
                "id": str(user.id),
                "email": user.email,
                "role": str(user.role),
            },
        }


# ---------------------------------------------------------------------------
# 3. POST /auth/refresh
# ---------------------------------------------------------------------------


@router.post("/refresh", response_model=TokenResponse)
async def refresh(body: RefreshRequest) -> dict[str, object]:
    try:
        payload = decode_token(
            body.refresh_token,
            settings.JWT_SECRET_KEY,
            settings.JWT_ALGORITHM,
        )
    except (pyjwt.InvalidTokenError, pyjwt.ExpiredSignatureError):
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")

    jti = payload.get("jti")
    if not isinstance(jti, str):
        raise HTTPException(
            status_code=401, detail="Invalid refresh token: missing jti"
        )

    # Look up DB row — must exist, not revoked, not expired
    async with get_session() as session:
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.jti == jti)
        )
        rt = result.scalar_one_or_none()

        if rt is None:
            raise HTTPException(status_code=401, detail="Refresh token not found")
        if rt.revoked:
            raise HTTPException(status_code=401, detail="Refresh token already revoked")
        if rt.expires_at.replace(tzinfo=UTC) < datetime.now(UTC):
            raise HTTPException(status_code=401, detail="Refresh token expired")

        # Revoke old refresh token
        rt.revoked = True
        await session.commit()

    # Blacklist old jti in Redis
    redis_client = get_redis()
    await revoke_token(jti, payload["exp"], redis_client)

    # Look up user
    user_id_str = str(payload["sub"])
    from uuid import UUID

    async with get_session() as session:
        result = await session.execute(select(User).where(User.id == UUID(user_id_str)))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

    access, new_refresh, _ = await _issue_token_pair(user, redis_client)

    return {
        "access_token": access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }


# ---------------------------------------------------------------------------
# 4. POST /auth/logout
# ---------------------------------------------------------------------------


@router.post("/logout", response_model=MessageResponse)
async def logout(
    request: Request,
    current_user: Annotated[dict[str, str], Depends(get_current_user)],
) -> dict[str, str]:
    jti = getattr(request.state, "jti", None)
    redis_client = get_redis()

    # Blacklist the current access token jti
    if jti is not None and isinstance(jti, str):
        await revoke_token(jti, datetime.now(UTC) + timedelta(hours=1), redis_client)

    # Revoke all refresh tokens for this user in DB
    await _revoke_all_refresh_tokens_for_user(current_user["user_id"])

    return {"message": "Logged out"}


# ---------------------------------------------------------------------------
# 5. POST /auth/password-reset-request
# ---------------------------------------------------------------------------


@router.post("/password-reset-request", response_model=MessageResponse)
async def password_reset_request(body: PasswordResetRequest) -> dict[str, str]:
    async with get_session() as session:
        result = await session.execute(select(User).where(User.email == body.email))
        user = result.scalar_one_or_none()

    if user is not None:
        raw_token = secrets.token_hex(32)
        token_hash = _token_hash(raw_token)
        redis_client = get_redis()
        await redis_client.set(
            f"pwreset:{token_hash}",
            str(user.id),
            ex=900,  # 15 minutes
        )
        logger.info("would send email to %s with token %s", body.email, raw_token)

    return {"message": "If the email exists, a reset link has been sent"}


# ---------------------------------------------------------------------------
# 6. POST /auth/password-reset
# ---------------------------------------------------------------------------


@router.post("/password-reset", response_model=MessageResponse)
async def password_reset(body: PasswordResetBody) -> dict[str, str]:
    token_hash = _token_hash(body.token)
    redis_client = get_redis()
    user_id_bytes = await redis_client.get(f"pwreset:{token_hash}")

    if user_id_bytes is None:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    user_id_str = (
        user_id_bytes.decode()
        if isinstance(user_id_bytes, bytes)
        else str(user_id_bytes)
    )

    from uuid import UUID

    async with get_session() as session:
        result = await session.execute(select(User).where(User.id == UUID(user_id_str)))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=400, detail="Invalid or expired reset token"
            )

        user.password_hash = hash_password(body.new_password)
        await session.commit()

    # Delete the used reset token
    await redis_client.delete(f"pwreset:{token_hash}")

    # Revoke all refresh tokens for this user
    await _revoke_all_refresh_tokens_for_user(user_id_str)

    return {"message": "Password reset successful"}


# ---------------------------------------------------------------------------
# 7. GET /auth/me
# ---------------------------------------------------------------------------


@router.get("/me", response_model=UserInfo)
async def me(
    current_user: Annotated[dict[str, str], Depends(get_current_user)],
) -> dict[str, str]:
    return {
        "id": current_user["user_id"],
        "email": current_user["email"],
        "role": current_user["role"],
    }
