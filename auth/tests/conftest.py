"""Shared fixtures for auth route tests."""

from __future__ import annotations

import os
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
import pytest_asyncio
from fakeredis import FakeAsyncRedis
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENCRYPTION_MASTER_KEY", "a" * 64)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-at-least-32-chars-long!")
os.environ.setdefault("SAHAYAK_EMAIL", "sahayak@test.com")
os.environ.setdefault("SAHAYAK_PASSWORD", "test123")
os.environ.setdefault("DEMO_SELLER_EMAIL", "seller@test.com")
os.environ.setdefault("DEMO_SELLER_PASSWORD", "test123")
os.environ.setdefault("DEMO_BUYER_EMAIL", "buyer@test.com")
os.environ.setdefault("DEMO_BUYER_PASSWORD", "test123")


class InMemoryStore:
    def __init__(self) -> None:
        self.users: dict[str, Any] = {}
        self.users_by_id: dict[str, Any] = {}
        self.refresh_tokens: dict[str, Any] = {}
        self.fake_redis = FakeAsyncRedis()

    def reset(self) -> None:
        self.users.clear()
        self.users_by_id.clear()
        self.refresh_tokens.clear()
        self.fake_redis = FakeAsyncRedis()


def _extract_right_val(right: Any) -> Any:
    """Extract the literal value from a SQLAlchemy BindParameter or raw value."""
    if hasattr(right, "value"):
        return right.value
    if hasattr(right, "__wrapped__"):
        return right.__wrapped__
    return right


def _make_session_factory(store: InMemoryStore):
    from auth.models import RefreshToken, User

    class _Session:
        def __init__(self) -> None:
            self._added: list[Any] = []

        async def execute(self, stmt: Any) -> MagicMock:
            compiled = str(stmt)
            where_clause: Any = getattr(stmt, "_where_criteria", ())
            result = MagicMock()

            if "users" in compiled:
                row = self._resolve_user_query(where_clause)
                result.scalar_one_or_none = MagicMock(return_value=row)
                scalar_list = MagicMock()
                scalar_list.all = MagicMock(return_value=[row] if row else [])
                scalar_list.__iter__ = MagicMock(return_value=iter([row] if row else []))
                result.scalars = MagicMock(return_value=scalar_list)
            elif "refresh_tokens" in compiled:
                rows = self._resolve_refresh_query(where_clause)
                if isinstance(rows, list):
                    result.scalar_one_or_none = MagicMock(return_value=rows[0] if rows else None)
                    scalar_iter = MagicMock()
                    scalar_iter.all = MagicMock(return_value=rows)
                    scalar_iter.__iter__ = MagicMock(return_value=iter(rows))
                    result.scalars = MagicMock(return_value=scalar_iter)
                else:
                    result.scalar_one_or_none = MagicMock(return_value=rows)
                    scalar_iter = MagicMock()
                    scalar_iter.all = MagicMock(return_value=[rows] if rows else [])
                    scalar_iter.__iter__ = MagicMock(return_value=iter([rows] if rows else []))
                    result.scalars = MagicMock(return_value=scalar_iter)
            else:
                result.scalar_one_or_none = MagicMock(return_value=None)
            return result

        def _resolve_user_query(self, where: tuple[Any, ...]) -> Any | None:
            for criterion in where:
                left = getattr(criterion, "left", None)
                right = getattr(criterion, "right", None)
                if left is None or right is None:
                    continue
                left_name = str(left).split(".")[-1]
                right_val = _extract_right_val(right)
                if left_name == "email":
                    return store.users.get(str(right_val))
                if left_name == "id":
                    return store.users_by_id.get(str(right_val))
            return None

        def _resolve_refresh_query(self, where: tuple[Any, ...]) -> Any | list[Any] | None:
            jti_val = None
            user_id_val = None
            revoked_val: bool | None = None
            for criterion in where:
                left = getattr(criterion, "left", None)
                right = getattr(criterion, "right", None)
                if left is None or right is None:
                    continue
                left_name = str(left).split(".")[-1]
                if left_name == "jti":
                    jti_val = str(_extract_right_val(right))
                elif left_name == "user_id":
                    user_id_val = str(_extract_right_val(right))
                elif left_name == "revoked":
                    rv = _extract_right_val(right)
                    if rv is not None:
                        from sqlalchemy.sql.expression import False_ as SA_False, True_ as SA_True
                        if isinstance(rv, SA_False):
                            revoked_val = False
                        elif isinstance(rv, SA_True):
                            revoked_val = True
                        else:
                            revoked_val = True
            if jti_val is not None:
                return store.refresh_tokens.get(jti_val)
            if user_id_val is not None:
                results = [rt for rt in store.refresh_tokens.values() if str(rt.user_id) == user_id_val]
                if revoked_val is False:
                    results = [rt for rt in results if not rt.revoked]
                return results
            return None

        def add(self, obj: Any) -> None:
            self._added.append(obj)

        async def commit(self) -> None:
            for obj in self._added:
                if isinstance(obj, User):
                    if obj.id is None:
                        obj.id = uuid.uuid4()
                    if obj.created_at is None:
                        obj.created_at = datetime.now(UTC)
                    store.users[obj.email] = obj
                    store.users_by_id[str(obj.id)] = obj
                elif isinstance(obj, RefreshToken):
                    store.refresh_tokens[obj.jti] = obj
            self._added.clear()

        async def refresh(self, _obj: Any) -> None:
            pass

        async def rollback(self) -> None:
            self._added.clear()

        async def close(self) -> None:
            pass

    @asynccontextmanager
    async def _session_ctx():
        session = _Session()
        try:
            yield session
        finally:
            pass

    return _session_ctx


@pytest.fixture
def store() -> InMemoryStore:
    return InMemoryStore()


@pytest.fixture(autouse=True)
def _patch_all(store: InMemoryStore):
    """Patch get_session and get_redis at all relevant import sites.

    Uses side_effect (lambda) instead of return_value so that the fresh
    store.fake_redis reference is captured each time — hedge against
    fixture ordering where _reset_store replaces store.fake_redis.
    """
    factory = _make_session_factory(store)

    # get_session patches — use side_effect so each call creates a fresh session
    # get_redis patches — use side_effect=lambda to always get the current store.fake_redis
    with (
        patch("storage.db.get_session", side_effect=factory),
        patch("auth.routes.get_session", side_effect=factory),
        patch("storage.redis.get_redis", side_effect=lambda: store.fake_redis),
        patch("auth.routes.get_redis", side_effect=lambda: store.fake_redis),
        patch("auth.middleware.get_redis", side_effect=lambda: store.fake_redis),
    ):
        yield


@pytest.fixture(autouse=True)
def _reset_store(store: InMemoryStore) -> None:
    store.reset()


@pytest.fixture
def app() -> FastAPI:
    from auth.middleware import JWTAuthMiddleware
    from auth.routes import router
    application = FastAPI()
    application.add_middleware(JWTAuthMiddleware)
    application.include_router(router)
    return application


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
