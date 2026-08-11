from __future__ import annotations

import sys
import uuid
from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio

# The production Docker image sets PYTHONPATH=/opt so that
#   import auth.middleware   →  /opt/auth/middleware/
# Local dev must replicate this by adding the monorepo root.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent)
sys.path.insert(0, _PROJECT_ROOT)

from auth.models import User, UserRole
from auth.services.jwt import create_access_token
from auth.services.password import hash_password
from sqlalchemy import Column, Table, select
from sqlalchemy.dialects.postgresql import UUID
from storage.config import Settings
from storage.db import get_session

TEST_SETTINGS_DATA: dict[str, str] = {
    "DATABASE_URL": "postgresql+psycopg://sih_dnk:a33519424ab397927a939a2eb3c89f372af70ca44b05c9d3@localhost:5433/sih_dnk",
    "REDIS_URL": "redis://127.0.0.1:6379/0",
    "ENCRYPTION_MASTER_KEY": "ab" * 32,
    "JWT_SECRET_KEY": "dev-secret-key-that-is-at-least-32-characters-long!!!",
    "JWT_ALGORITHM": "HS256",
    "SAHAYAK_EMAIL": "s@test.com",
    "SAHAYAK_PASSWORD": "p",
    "DEMO_SELLER_EMAIL": "s@test.com",
    "DEMO_SELLER_PASSWORD": "p",
    "DEMO_BUYER_EMAIL": "b@test.com",
    "DEMO_BUYER_PASSWORD": "p",
}

TEST_SETTINGS = Settings(**TEST_SETTINGS_DATA)


@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("storage.config.settings", TEST_SETTINGS)


@pytest.fixture(autouse=True)
def _mock_is_revoked(monkeypatch: pytest.MonkeyPatch) -> None:
    async def _noop(_jti: str, _redis: object) -> bool:
        return False

    monkeypatch.setattr("auth.services.jwt.is_revoked", _noop)


@pytest.fixture(autouse=True)
def _mock_get_redis(monkeypatch: pytest.MonkeyPatch) -> None:
    from unittest.mock import MagicMock

    _dummy = MagicMock()
    monkeypatch.setattr("auth.middleware.get_redis", lambda: _dummy)


@pytest.fixture(autouse=True)
def _patch_crypto_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    crypto_settings = Settings(
        DATABASE_URL=TEST_SETTINGS_DATA["DATABASE_URL"],
        REDIS_URL=TEST_SETTINGS_DATA["REDIS_URL"],
        ENCRYPTION_MASTER_KEY=TEST_SETTINGS_DATA["ENCRYPTION_MASTER_KEY"],
        JWT_SECRET_KEY=TEST_SETTINGS_DATA["JWT_SECRET_KEY"],
        SAHAYAK_EMAIL="s@test.com",
        SAHAYAK_PASSWORD="p",
        DEMO_SELLER_EMAIL="s@test.com",
        DEMO_SELLER_PASSWORD="p",
        DEMO_BUYER_EMAIL="b@test.com",
        DEMO_BUYER_PASSWORD="p",
    )
    monkeypatch.setattr("app.services.profile_crypto.settings", crypto_settings)


@pytest.fixture(autouse=True, scope="session")
def _register_users_table() -> None:
    from app.models import Base

    Table(
        "users",
        Base.metadata,
        Column("id", UUID(as_uuid=True), primary_key=True),
        extend_existing=True,
    )


@pytest_asyncio.fixture
async def test_seller() -> AsyncIterator[dict[str, str]]:
    email = f"test_seller_{uuid.uuid4().hex[:8]}@profiletest.com"

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
        TEST_SETTINGS.JWT_SECRET_KEY,
        TEST_SETTINGS.JWT_ALGORITHM,
        60,
    )

    yield {"user_id": user_id, "email": email, "role": "seller", "token": token}

    async with get_session()() as session:
        from app.models.profile import SellerProfile

        result = await session.execute(
            select(SellerProfile).where(
                SellerProfile.user_id == uuid.UUID(user_id)
            )
        )
        profile = result.scalar_one_or_none()
        if profile is not None:
            await session.delete(profile)
            await session.flush()

        result = await session.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        u = result.scalar_one_or_none()
        if u is not None:
            await session.delete(u)
            await session.commit()


@pytest_asyncio.fixture
async def test_sahayak() -> AsyncIterator[dict[str, str]]:
    email = f"test_sahayak_{uuid.uuid4().hex[:8]}@profiletest.com"

    async with get_session()() as session:
        user = User(
            email=email,
            password_hash=hash_password("testpass"),
            role=UserRole("sahayak"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    user_id = str(user.id)
    token = create_access_token(
        {"sub": user_id, "role": "sahayak", "email": email},
        TEST_SETTINGS.JWT_SECRET_KEY,
        TEST_SETTINGS.JWT_ALGORITHM,
        60,
    )

    yield {"user_id": user_id, "email": email, "role": "sahayak", "token": token}

    async with get_session()() as session:
        result = await session.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        u = result.scalar_one_or_none()
        if u is not None:
            await session.delete(u)
            await session.commit()


@pytest_asyncio.fixture
async def test_buyer() -> AsyncIterator[dict[str, str]]:
    email = f"test_buyer_{uuid.uuid4().hex[:8]}@profiletest.com"

    async with get_session()() as session:
        user = User(
            email=email,
            password_hash=hash_password("testpass"),
            role=UserRole("buyer"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    user_id = str(user.id)
    token = create_access_token(
        {"sub": user_id, "role": "buyer", "email": email},
        TEST_SETTINGS.JWT_SECRET_KEY,
        TEST_SETTINGS.JWT_ALGORITHM,
        60,
    )

    yield {"user_id": user_id, "email": email, "role": "buyer", "token": token}

    async with get_session()() as session:
        result = await session.execute(
            select(User).where(User.id == uuid.UUID(user_id))
        )
        u = result.scalar_one_or_none()
        if u is not None:
            await session.delete(u)
            await session.commit()
