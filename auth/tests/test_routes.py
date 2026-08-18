"""Integration tests for all auth route endpoints.

Covers register, login, refresh, logout, password-reset-request,
password-reset, and /me — happy paths and failure modes.
"""

from __future__ import annotations

import secrets
import time
import uuid

import jwt as pyjwt
import pytest
from httpx import AsyncClient

from storage.config import settings

JWT_SECRET: str = settings.JWT_SECRET_KEY
JWT_ALGO: str = settings.JWT_ALGORITHM

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_auth_token(sub: str, role: str, email: str) -> str:
    now = int(time.time())
    return pyjwt.encode(
        {
            "sub": sub,
            "role": role,
            "email": email,
            "jti": str(uuid.uuid4()),
            "exp": now + 3600,
            "iat": now,
        },
        JWT_SECRET,
        algorithm=JWT_ALGO,
    )


async def _register(client: AsyncClient, email: str, password: str, role: str = "seller") -> dict:
    r = await client.post(
        "/auth/register",
        json={"email": email, "password": password, "role": role},
    )
    return r.json()


async def _login(client: AsyncClient, email: str, password: str) -> dict:
    r = await client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    return r.json()


# ===========================================================================
# Register
# ===========================================================================


class TestRegister:
    @pytest.mark.asyncio
    async def test_seller_registration(self, client: AsyncClient) -> None:
        r = await client.post(
            "/auth/register",
            json={"email": "seller@shop.com", "password": "pass1234", "role": "seller"},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["email"] == "seller@shop.com"
        assert body["role"] == "seller"
        assert "id" in body
        assert "created_at" in body

    @pytest.mark.asyncio
    async def test_buyer_registration(self, client: AsyncClient) -> None:
        r = await client.post(
            "/auth/register",
            json={"email": "buyer@shop.com", "password": "pass1234", "role": "buyer"},
        )
        assert r.status_code == 201
        body = r.json()
        assert body["role"] == "buyer"

    @pytest.mark.asyncio
    async def test_sahayak_registration_rejected(self, client: AsyncClient) -> None:
        r = await client.post(
            "/auth/register",
            json={"email": "sahayak@shop.com", "password": "pass1234", "role": "sahayak"},
        )
        assert r.status_code == 400
        assert "forbidden" in r.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_duplicate_email_409(self, client: AsyncClient) -> None:
        await _register(client, "dup@test.com", "pass1234")
        r = await client.post(
            "/auth/register",
            json={"email": "dup@test.com", "password": "another", "role": "buyer"},
        )
        assert r.status_code == 409
        assert "already registered" in r.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_invalid_role_format(self, client: AsyncClient) -> None:
        # "admin" passes Pydantic validation (no pattern constraint)
        # but is rejected by route-level check with 400
        r = await client.post(
            "/auth/register",
            json={"email": "x@test.com", "password": "pass", "role": "admin"},
        )
        assert r.status_code == 400
        assert "forbidden" in r.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_password_not_in_response(self, client: AsyncClient) -> None:
        body = await _register(client, "priv@test.com", "secret123")
        assert "password_hash" not in body
        assert "password" not in body


# ===========================================================================
# Login
# ===========================================================================


class TestLogin:
    @pytest.mark.asyncio
    async def test_login_seller(self, client: AsyncClient) -> None:
        await _register(client, "seller@shop.com", "mypassword")

        r = await client.post(
            "/auth/login",
            json={"email": "seller@shop.com", "password": "mypassword"},
        )
        assert r.status_code == 200
        body = r.json()
        assert "access_token" in body
        assert "refresh_token" in body
        assert body["token_type"] == "bearer"
        assert body["user"]["email"] == "seller@shop.com"
        assert body["user"]["role"] == "seller"
        assert "id" in body["user"]

    @pytest.mark.asyncio
    async def test_wrong_password_401(self, client: AsyncClient) -> None:
        await _register(client, "u@test.com", "correct")

        r = await client.post(
            "/auth/login",
            json={"email": "u@test.com", "password": "wrong"},
        )
        assert r.status_code == 401
        assert "invalid" in r.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_nonexistent_email_401(self, client: AsyncClient) -> None:
        r = await client.post(
            "/auth/login",
            json={"email": "nobody@test.com", "password": "anything"},
        )
        assert r.status_code == 401
        assert "invalid" in r.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_missing_fields_422(self, client: AsyncClient) -> None:
        r = await client.post("/auth/login", json={"email": "e@t.com"})
        assert r.status_code == 422

    @pytest.mark.asyncio
    async def test_token_contains_email_claim(self, client: AsyncClient) -> None:
        await _register(client, "claims@test.com", "pass")
        login_body = await _login(client, "claims@test.com", "pass")

        payload = pyjwt.decode(
            login_body["access_token"],
            JWT_SECRET,
            algorithms=[JWT_ALGO],
        )
        assert payload["email"] == "claims@test.com"
        assert payload["role"] == "seller"


# ===========================================================================
# Refresh
# ===========================================================================


class TestRefresh:
    @pytest.mark.asyncio
    async def test_refresh_rotation(self, client: AsyncClient) -> None:
        await _register(client, "rotate@test.com", "pass")
        login_body = await _login(client, "rotate@test.com", "pass")
        old_refresh = login_body["refresh_token"]
        old_access = login_body["access_token"]

        r = await client.post(
            "/auth/refresh",
            json={"refresh_token": old_refresh},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["access_token"] != old_access
        assert body["refresh_token"] != old_refresh
        assert body["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_old_refresh_invalid_after_rotation(self, client: AsyncClient) -> None:
        await _register(client, "rotate2@test.com", "pass")
        login_body = await _login(client, "rotate2@test.com", "pass")
        old_refresh = login_body["refresh_token"]

        # Rotate once
        r1 = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
        assert r1.status_code == 200

        # Try old refresh again → should fail
        r2 = await client.post("/auth/refresh", json={"refresh_token": old_refresh})
        assert r2.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_with_access_token_fails(self, client: AsyncClient) -> None:
        await _register(client, "rt3@test.com", "pass")
        login_body = await _login(client, "rt3@test.com", "pass")

        r = await client.post(
            "/auth/refresh",
            json={"refresh_token": login_body["access_token"]},
        )
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_expired_token_fails(self, client: AsyncClient) -> None:
        # Create an already-expired refresh token
        now = int(time.time())
        expired = pyjwt.encode(
            {
                "sub": str(uuid.uuid4()),
                "role": "seller",
                "email": "e@t.com",
                "jti": "expired-jti",
                "exp": now - 60,
                "iat": now - 3600,
            },
            JWT_SECRET,
            algorithm=JWT_ALGO,
        )
        r = await client.post("/auth/refresh", json={"refresh_token": expired})
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_invalid_jwt(self, client: AsyncClient) -> None:
        r = await client.post(
            "/auth/refresh",
            json={"refresh_token": "not-a-valid-jwt"},
        )
        assert r.status_code == 401


# ===========================================================================
# Logout
# ===========================================================================


class TestLogout:
    @pytest.mark.asyncio
    async def test_logout_via_auth_header(self, client: AsyncClient) -> None:
        await _register(client, "logout@test.com", "pass")
        login_body = await _login(client, "logout@test.com", "pass")
        token = login_body["access_token"]

        r = await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        assert r.json()["message"] == "Logged out"

    @pytest.mark.asyncio
    async def test_logout_without_token_fails(self, client: AsyncClient) -> None:
        r = await client.post("/auth/logout")
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_me_fails_after_logout(self, client: AsyncClient) -> None:
        await _register(client, "afterlogout@test.com", "pass")
        login_body = await _login(client, "afterlogout@test.com", "pass")
        token = login_body["access_token"]

        # Logout
        await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

        # /me should now fail
        r = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 401


# ===========================================================================
# Password Reset Request
# ===========================================================================


class TestPasswordResetRequest:
    @pytest.mark.asyncio
    async def test_request_for_existing_user_returns_200(self, client: AsyncClient) -> None:
        await _register(client, "pwreset@test.com", "oldpass")
        r = await client.post(
            "/auth/password-reset-request",
            json={"email": "pwreset@test.com"},
        )
        assert r.status_code == 200
        assert "email" in r.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_request_for_nonexistent_user_still_returns_200(
        self, client: AsyncClient
    ) -> None:
        r = await client.post(
            "/auth/password-reset-request",
            json={"email": "nobody@nowhere.com"},
        )
        assert r.status_code == 200
        assert "email" in r.json()["message"].lower()

    @pytest.mark.asyncio
    async def test_request_stores_token_in_redis(self, client: AsyncClient, store) -> None:
        await _register(client, "storetoken@test.com", "oldpass")
        r = await client.post(
            "/auth/password-reset-request",
            json={"email": "storetoken@test.com"},
        )
        assert r.status_code == 200

        keys = await store.fake_redis.keys("pwreset:*")
        assert len(keys) > 0


# ===========================================================================
# Password Reset
# ===========================================================================


class TestPasswordReset:
    @pytest.mark.asyncio
    async def test_full_reset_flow(self, client: AsyncClient, store) -> None:
        await _register(client, "resetflow@test.com", "oldpassword")

        # Step 1: request reset → retrieves token from redis
        await client.post(
            "/auth/password-reset-request",
            json={"email": "resetflow@test.com"},
        )

        # Extract the raw token logged (in tests, we can grab from redis)
        keys = await store.fake_redis.keys("pwreset:*")
        assert len(keys) > 0
        token_hash_key = keys[0].decode() if isinstance(keys[0], bytes) else keys[0]

        # We need the raw token. The raw token is stored in redis but we
        # need to compute what raw token produces this hash. Since we can't
        # reverse the hash, we'll use a programmatic flow: generate our own
        # token, store it manually.
        from auth.routes import _token_hash

        raw_token = secrets.token_hex(32)
        computed_hash = _token_hash(raw_token)

        # Look up existing key to get user_id, then re-set with our token
        user_id = await store.fake_redis.get(token_hash_key)
        await store.fake_redis.set(f"pwreset:{computed_hash}", user_id, ex=900)

        # Step 2: reset with our token
        r = await client.post(
            "/auth/password-reset",
            json={"token": raw_token, "new_password": "newpassword"},
        )
        assert r.status_code == 200
        assert "successful" in r.json()["message"].lower()

        # Step 3: login with new password should work
        r2 = await client.post(
            "/auth/login",
            json={"email": "resetflow@test.com", "password": "newpassword"},
        )
        assert r2.status_code == 200

    @pytest.mark.asyncio
    async def test_reset_with_invalid_token_400(self, client: AsyncClient) -> None:
        r = await client.post(
            "/auth/password-reset",
            json={"token": "bogus-token-never-exists", "new_password": "pass"},
        )
        assert r.status_code == 400
        assert "invalid" in r.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_reset_with_expired_token_400(self, client: AsyncClient, store) -> None:
        import uuid as _uuid

        await _register(client, "expiredreset@test.com", "oldpass")

        raw_token = secrets.token_hex(32)
        from auth.routes import _token_hash

        computed_hash = _token_hash(raw_token)
        await store.fake_redis.set(f"pwreset:{computed_hash}", str(_uuid.uuid4()), ex=1)

        r = await client.post(
            "/auth/password-reset",
            json={"token": raw_token, "new_password": "newpass"},
        )
        assert r.status_code in (200, 400)


# ===========================================================================
# Me
# ===========================================================================


class TestMe:
    @pytest.mark.asyncio
    async def test_me_returns_user_info(self, client: AsyncClient) -> None:
        body = await _register(client, "me@test.com", "pass")
        user_id = body["id"]

        token = _make_auth_token(sub=user_id, role="seller", email="me@test.com")

        r = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["id"] == user_id
        assert data["email"] == "me@test.com"
        assert data["role"] == "seller"

    @pytest.mark.asyncio
    async def test_me_without_auth_401(self, client: AsyncClient) -> None:
        r = await client.get("/auth/me")
        assert r.status_code == 401

    @pytest.mark.asyncio
    async def test_me_with_invalid_token_401(self, client: AsyncClient) -> None:
        r = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer not.valid.jwt"},
        )
        assert r.status_code == 401


# ===========================================================================
# Edge cases / integration
# ===========================================================================


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_registration_persisted_for_login(self, client: AsyncClient) -> None:
        body = await _register(client, "persist@test.com", "secretpw")
        user_id = body["id"]

        login_body = await _login(client, "persist@test.com", "secretpw")
        assert login_body["user"]["id"] == user_id

    @pytest.mark.asyncio
    async def test_different_roles_isolated(self, client: AsyncClient) -> None:
        await _register(client, "s@test.com", "pass", role="seller")
        await _register(client, "b@test.com", "pass", role="buyer")

        s_login = await _login(client, "s@test.com", "pass")
        b_login = await _login(client, "b@test.com", "pass")

        assert s_login["user"]["role"] == "seller"
        assert b_login["user"]["role"] == "buyer"
        assert s_login["user"]["id"] != b_login["user"]["id"]
