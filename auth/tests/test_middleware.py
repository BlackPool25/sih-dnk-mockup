"""Integration tests for JWTAuthMiddleware and auth dependencies.

Uses a minimal FastAPI test application wrapped with the middleware and route
handlers that consume ``request.state.user`` and ``require_role``.  The JWT
service functions (``decode_token``, ``is_revoked``) are mocked because
``auth.services.jwt`` is built in a parallel task and may not exist yet.
"""

from __future__ import annotations

import os
import sys
import time
from typing import Any, cast
from unittest.mock import MagicMock, patch

import jwt as pyjwt  # PyJWT — for generating real test tokens
import pytest
import pytest_asyncio
from fastapi import Depends, FastAPI, Request
from httpx import ASGITransport, AsyncClient

# ═══════════════════════════════════════════════════════════════════════════
# Environment — set BEFORE any import that triggers Settings() singleton
# ═══════════════════════════════════════════════════════════════════════════
os.environ.setdefault("DATABASE_URL", "postgresql://localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("ENCRYPTION_MASTER_KEY", "a" * 64)
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-at-least-32-chars-long!")
os.environ.setdefault("SAHAYAK_EMAIL", "test@test.com")
os.environ.setdefault("SAHAYAK_PASSWORD", "test123")
os.environ.setdefault("DEMO_SELLER_EMAIL", "seller@test.com")
os.environ.setdefault("DEMO_SELLER_PASSWORD", "test123")
os.environ.setdefault("DEMO_BUYER_EMAIL", "buyer@test.com")
os.environ.setdefault("DEMO_BUYER_PASSWORD", "test123")

from storage.config import settings

# ═══════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════
JWT_SECRET: str = settings.JWT_SECRET_KEY
JWT_ALGO: str = settings.JWT_ALGORITHM

# ---------------------------------------------------------------------------
# Token helpers
# ---------------------------------------------------------------------------


def _make_token(
    *,
    sub: str,
    role: str,
    email: str,
    jti: str = "test-jti",
    exp_delta: int = 3600,
) -> str:
    now = int(time.time())
    return pyjwt.encode(
        {
            "sub": sub,
            "role": role,
            "email": email,
            "jti": jti,
            "exp": now + exp_delta,
            "iat": now,
        },
        JWT_SECRET,
        algorithm=JWT_ALGO,
    )


def _make_expired_token(
    sub: str = "user-1",
    role: str = "seller",
    email: str = "seller@test.com",
) -> str:
    now = int(time.time())
    return pyjwt.encode(
        {
            "sub": sub,
            "role": role,
            "email": email,
            "jti": "expired-jti",
            "exp": now - 10,
            "iat": now - 3600,
        },
        JWT_SECRET,
        algorithm=JWT_ALGO,
    )


# ---------------------------------------------------------------------------
# Mock JWT service — injected into sys.modules before middleware tries to
# import ``auth.services.jwt`` at runtime.
# ---------------------------------------------------------------------------


def _mock_decode_token(token: str, secret_key: str, algorithm: str) -> dict[str, Any]:
    """Simulate decode_token: delegate to real PyJWT decode with verification."""
    return pyjwt.decode(token, secret_key, algorithms=[algorithm])


async def _mock_is_revoked(jti: str, _redis_client: Any) -> bool:
    """Simulate is_revoked: only the hardcoded 'revoked-jti' is revoked."""
    return jti == "revoked-jti"


@pytest.fixture(autouse=True)
def _mock_jwt_service() -> MagicMock:
    """Inject a fake ``auth.services.jwt`` module into sys.modules.

    The middleware import is lazy (inside ``dispatch``), so the mock must
    be present in sys.modules before any request is processed.
    """
    fake_module = MagicMock()
    fake_module.decode_token = _mock_decode_token
    fake_module.is_revoked = _mock_is_revoked

    with patch.dict(sys.modules, {"auth.services.jwt": fake_module}):
        yield fake_module


# ═══════════════════════════════════════════════════════════════════════════
# Test application
# ═══════════════════════════════════════════════════════════════════════════


@pytest.fixture
def app() -> FastAPI:
    """Minimal FastAPI app with JWTAuthMiddleware and test routes."""
    from auth.deps import require_role
    from auth.middleware import JWTAuthMiddleware

    application = FastAPI()
    application.add_middleware(JWTAuthMiddleware)

    @application.get("/user-info")
    async def user_info(request: Request) -> dict[str, str]:
        """Return the injected user dict so tests can verify it."""
        return cast(dict[str, str], request.state.user)

    @application.get("/seller-only", dependencies=[Depends(require_role("seller"))])
    async def seller_only() -> dict[str, str]:
        return {"status": "ok"}

    return application


@pytest_asyncio.fixture
async def client(app: FastAPI) -> AsyncClient:
    """Async HTTP client for the test application."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ═══════════════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════════════


class TestNoToken:
    @pytest.mark.asyncio
    async def test_no_token(self, client: AsyncClient) -> None:
        """Request without Authorization header → 401."""
        response = await client.get("/user-info")
        assert response.status_code == 401


class TestMalformedToken:
    @pytest.mark.asyncio
    async def test_malformed_token(self, client: AsyncClient) -> None:
        """Bearer header with a non-JWT string → 401."""
        response = await client.get(
            "/user-info",
            headers={"Authorization": "Bearer not-a-jwt"},
        )
        assert response.status_code == 401


class TestValidToken:
    @pytest.mark.asyncio
    async def test_valid_token(self, client: AsyncClient) -> None:
        """Valid JWT → 200 with user info in response body."""
        token = _make_token(sub="user-1", role="buyer", email="buyer@test.com")
        response = await client.get(
            "/user-info",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        body = response.json()
        assert body["user_id"] == "user-1"
        assert body["role"] == "buyer"
        assert body["email"] == "buyer@test.com"


class TestRevokedToken:
    @pytest.mark.asyncio
    async def test_revoked_token(self, client: AsyncClient) -> None:
        """Revoked JWT (jti='revoked-jti') → 401."""
        token = _make_token(
            sub="user-1", role="buyer", email="buyer@test.com", jti="revoked-jti",
        )
        response = await client.get(
            "/user-info",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401


class TestSellerRole:
    @pytest.mark.asyncio
    async def test_seller_role(self, client: AsyncClient) -> None:
        """Seller token accessing a seller-protected route → 200."""
        token = _make_token(sub="seller-1", role="seller", email="seller@test.com")
        response = await client.get(
            "/seller-only",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}


class TestBuyerRoleOnSellerRoute:
    @pytest.mark.asyncio
    async def test_buyer_role_on_seller_route(self, client: AsyncClient) -> None:
        """Buyer token on a seller-protected route → 403."""
        token = _make_token(sub="buyer-1", role="buyer", email="buyer@test.com")
        response = await client.get(
            "/seller-only",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 403
        body = response.json()
        assert "seller" in body["detail"].lower()


class TestExpiredToken:
    @pytest.mark.asyncio
    async def test_expired_token(self, client: AsyncClient) -> None:
        """Expired JWT → 401."""
        token = _make_expired_token()
        response = await client.get(
            "/user-info",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 401


class TestMissingClaims:
    @pytest.mark.asyncio
    async def test_token_missing_role_claim(self, client: AsyncClient) -> None:
        """Token without 'role' claim → 401 (missing required claims)."""
        now = int(time.time())
        bad_token = pyjwt.encode(
            {"sub": "user-1", "email": "u@t.com", "jti": "jti-1", "exp": now + 3600, "iat": now},
            JWT_SECRET,
            algorithm=JWT_ALGO,
        )
        response = await client.get(
            "/user-info",
            headers={"Authorization": f"Bearer {bad_token}"},
        )
        assert response.status_code == 401


class TestDirectDependencyCalls:
    """Unit-style tests for deps.py functions (no middleware needed)."""

    @pytest.fixture
    def mock_request(self) -> MagicMock:
        """Fake FastAPI Request with configurable state."""
        req = MagicMock(spec=Request)
        return req

    def test_get_current_user_returns_dict(self, mock_request: MagicMock) -> None:
        from auth.deps import get_current_user

        mock_request.state.user = {"user_id": "u1", "role": "seller", "email": "s@t.com"}
        result = get_current_user(mock_request)
        assert result == {"user_id": "u1", "role": "seller", "email": "s@t.com"}

    def test_get_current_user_raises_401_on_missing_state(self, mock_request: MagicMock) -> None:
        from fastapi import HTTPException

        from auth.deps import get_current_user

        del mock_request.state.user  # no state
        with pytest.raises(HTTPException) as exc:
            get_current_user(mock_request)
        assert exc.value.status_code == 401

    def test_require_role_allows_correct_role(self, mock_request: MagicMock) -> None:
        from auth.deps import require_role

        mock_request.state.user = {"user_id": "u1", "role": "admin", "email": "a@t.com"}
        checker = require_role("admin", "moderator")
        checker(mock_request)  # should not raise

    def test_require_role_rejects_wrong_role(self, mock_request: MagicMock) -> None:
        from fastapi import HTTPException

        from auth.deps import require_role

        mock_request.state.user = {"user_id": "u1", "role": "guest", "email": "g@t.com"}
        checker = require_role("admin")
        with pytest.raises(HTTPException) as exc:
            checker(mock_request)
        assert exc.value.status_code == 403
        assert "admin" in exc.value.detail

    def test_require_role_rejects_unauthenticated(self, mock_request: MagicMock) -> None:
        from fastapi import HTTPException

        from auth.deps import require_role

        del mock_request.state.user
        checker = require_role("admin")
        with pytest.raises(HTTPException) as exc:
            checker(mock_request)
        assert exc.value.status_code == 401
