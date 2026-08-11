"""E2E integration tests — 12 full-stack scenarios using httpx against the test app.

Each scenario exercises multiple routers and middleware layers (auth, rate
limiting, profiles, orders, docs, QR) to verify end-to-end request/response
behaviour with mocked DB and Redis.
"""

from __future__ import annotations

import hashlib
import math
import secrets as _secrets
import time as _stdlib_time
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from app.main import app
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from auth.models import User, UserRole
from auth.services.jwt import create_access_token, decode_token
from auth.services.password import hash_password
from storage.config import settings as _settings
from storage.db import get_session as _db_get_session

# ---------------------------------------------------------------------------
# Shared test data (matches patterns from test_profile_routes / test_order_routes)
# ---------------------------------------------------------------------------

PROFILE_PAYLOAD: dict[str, str] = {
    "firm_name": "Test Exports Ltd",
    "owner_name": "John Doe",
    "pan": "ABCDE1234F",
    "bank_name": "State Bank of India",
    "bank_account": "12345678901",
    "ifsc": "SBIN0001234",
    "bank_branch": "Mumbai Main",
    "iec": "1234567890",
    "ad_code": "9876543",
    "gstin": "22AAAAA0000A1Z5",
    "address_line1": "123 Shipping Lane",
    "address_line2": "Andheri East",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400069",
    "phone": "9876543210",
}

ORDER_PAYLOAD: dict[str, object] = {
    "destination_country": "US",
    "value_minor": 50000,
    "consignee": "Acme Corp, New York",
    "net_weight_g": 1000.0,
    "gross_weight_g": 1200.0,
    "line_items": [
        {
            "description": "Cotton T-Shirts",
            "hsn_code": "61091000",
            "quantity": 100,
            "unit_price_minor": 500,
            "total_minor": 50000,
        },
    ],
    "currency": "INR",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_RATE_LIMIT_MOD = "app.middleware.rate_limiter"


def _patch_storage_db_get_session(monkeypatch: pytest.MonkeyPatch) -> None:
    """Monkeypatch get_session so auth routes work with ``async with``.

    SQLAlchemy 2.0.51's async_sessionmaker does not support ``async with``
    directly.  The auth routes call ``async with get_session() as session:``
    (single set of parens) while the profile/order/doc routers call
    ``async with get_session()() as session:`` (double set of parens).

    This wrapper returns an object that supports BOTH patterns:
    - ``async with get_session() as session:``  (auth routes)
    - ``async with get_session()() as session:`` (profile/order/doc routes)
    """

    class _SessionWrapper:
        """Supports both ``async with obj`` and ``async with obj()``."""

        async def __aenter__(self):
            maker = _db_get_session()
            session = maker()
            self._ctx = session
            return await session.__aenter__()

        async def __aexit__(self, *args: object) -> None:
            await self._ctx.__aexit__(*args)

        def __call__(self):
            """Support the double-call pattern: ``get_session()()``."""
            maker = _db_get_session()
            return maker()

    _wrapper = _SessionWrapper()

    # auth.routes and auth.cli.__main__ import ``get_session`` at module level
    # and bind it to their own namespace, so we must patch those modules directly.
    monkeypatch.setattr("auth.routes.get_session", lambda: _wrapper)
    monkeypatch.setattr("auth.cli.__main__.get_session", lambda: _wrapper)
    # Also patch the source module for any lazy importers.
    monkeypatch.setattr("storage.db.get_session", lambda: _wrapper)


async def _create_profile(client: AsyncClient, token: str) -> dict:
    resp = await client.post(
        "/profile",
        json=PROFILE_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"Profile creation failed: {resp.text}"
    return resp.json()


async def _create_order(
    client: AsyncClient, token: str, payload: dict | None = None
) -> str:
    resp = await client.post(
        "/orders",
        json=payload or ORDER_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"Order creation failed: {resp.text}"
    return resp.json()["id"]


async def _generate_docs(client: AsyncClient, token: str, order_id: str) -> dict:
    resp = await client.post(
        f"/orders/{order_id}/generate-docs",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"Doc generation failed: {resp.text}"
    return resp.json()


async def _generate_qr(client: AsyncClient, token: str, order_id: str) -> dict:
    resp = await client.post(
        f"/orders/{order_id}/generate-qr",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"QR generation failed: {resp.text}"
    return resp.json()


async def _create_second_seller(email: str) -> dict[str, str]:
    """Create a second seller user outside the standard fixture."""
    async with _db_get_session()() as session:
        user = User(
            email=email,
            password_hash=hash_password("testpass"),
            role=UserRole("seller"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    token = create_access_token(
        {"sub": str(user.id), "role": "seller", "email": email},
        _settings.JWT_SECRET_KEY,
        _settings.JWT_ALGORITHM,
        60,
    )
    return {"user_id": str(user.id), "email": email, "role": "seller", "token": token}


# ---------------------------------------------------------------------------
# Fake Redis for rate-limit and password-reset testing
# ---------------------------------------------------------------------------


class _FakeRateLimitRedis:
    """In-memory Redis mock supporting evalsha (rate-limit Lua), kv ops."""

    def __init__(self) -> None:
        self._entries: dict[str, list[float]] = {}
        self._kv: dict[str, str] = {}

    async def script_load(self, _script: str) -> str:
        return "fake-sha"

    async def evalsha(
        self,
        _sha: str,
        _numkeys: int,
        key: str,
        now_ms: int,
        window_s: int,
        limit: int,
    ) -> list[int]:
        cutoff = now_ms - window_s * 1000
        timestamps = [t for t in self._entries.get(key, []) if t >= cutoff]
        if len(timestamps) >= limit:
            wait = window_s
            if timestamps:
                oldest_ms = min(timestamps)
                wait = math.ceil((oldest_ms - cutoff) / 1000)
            self._entries[key] = timestamps
            return [len(timestamps), wait]
        timestamps.append(float(now_ms))
        self._entries[key] = timestamps
        return [len(timestamps), 0]

    async def get(self, key: str) -> bytes | None:
        val = self._kv.get(key)
        return val.encode() if val is not None else None

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self._kv[key] = value

    async def delete(self, key: str) -> None:
        self._kv.pop(key, None)

    async def exists(self, key: str) -> int:
        return 1 if key in self._kv else 0


# ---------------------------------------------------------------------------
# Pytest markers
# ---------------------------------------------------------------------------

pytestmark = pytest.mark.asyncio


# ===========================================================================
# Scenario 1 — Register seller + buyer
# ===========================================================================


async def test_e2e_01_register_seller_and_buyer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """POST /auth/register → 201 for both seller and buyer roles.

    Verifies response shape: id, email, role, created_at."""
    _patch_storage_db_get_session(monkeypatch)

    seller_email = f"e2e_seller_{uuid.uuid4().hex[:8]}@test.com"
    buyer_email = f"e2e_buyer_{uuid.uuid4().hex[:8]}@test.com"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        seller_resp = await client.post(
            "/auth/register",
            json={"email": seller_email, "password": "securepass123", "role": "seller"},
        )
        buyer_resp = await client.post(
            "/auth/register",
            json={"email": buyer_email, "password": "securepass123", "role": "buyer"},
        )

    assert seller_resp.status_code == 201
    sdata = seller_resp.json()
    assert sdata["email"] == seller_email
    assert sdata["role"] == "seller"
    assert "id" in sdata
    assert "created_at" in sdata

    assert buyer_resp.status_code == 201
    bdata = buyer_resp.json()
    assert bdata["email"] == buyer_email
    assert bdata["role"] == "buyer"
    assert "id" in bdata

    # Cleanup
    async with _db_get_session()() as session:
        for uid in [sdata["id"], bdata["id"]]:
            result = await session.execute(
                select(User).where(User.id == uuid.UUID(uid))
            )
            u = result.scalar_one_or_none()
            if u is not None:
                await session.delete(u)
        await session.commit()


# ===========================================================================
# Scenario 2 — Seed sahayak
# ===========================================================================


async def test_e2e_02_seed_sahayak(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Seed sahayak account via the seed-sahayak CLI function → user exists.

    Verifies the sahayak user is created with the correct role in the DB."""
    _patch_storage_db_get_session(monkeypatch)

    email = f"e2e_sahayak_{uuid.uuid4().hex[:8]}@officer.gov.in"
    password = "adminpass123"

    # Override settings on the ACTUAL object that the CLI module imported.
    # The CLI module imported its own reference before the conftest patch,
    # so we must set attributes on auth.cli.__main__.settings, not storage.config.settings.
    from auth.cli.__main__ import settings as _cli_settings

    object.__setattr__(_cli_settings, "SAHAYAK_EMAIL", email)
    object.__setattr__(_cli_settings, "SAHAYAK_PASSWORD", password)

    from auth.cli.__main__ import _seed_sahayak

    await _seed_sahayak()

    # Verify in DB
    async with _db_get_session()() as session:
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

    assert user is not None
    assert str(user.role) == "sahayak"
    assert user.is_active is True

    # Cleanup
    async with _db_get_session()() as session:
        result = await session.execute(select(User).where(User.email == email))
        u = result.scalar_one_or_none()
        if u is not None:
            await session.delete(u)
            await session.commit()


# ===========================================================================
# Scenario 3 — Seller profile + document upload
# ===========================================================================


async def test_e2e_03_seller_profile_and_upload(
    test_seller: dict[str, str],
) -> None:
    """POST /profile → 201, then POST /profile/documents → 201.

    Verifies profile is created with correct shape and uploaded doc metadata."""
    from io import BytesIO

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create profile
        profile_resp = await client.post(
            "/profile",
            json=PROFILE_PAYLOAD,
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

        # Upload a document
        fake_pdf = BytesIO(b"%PDF-1.4 fake content for testing")
        upload_resp = await client.post(
            "/profile/documents",
            files={"file": ("pan_card.pdf", fake_pdf, "application/pdf")},
            data={"doc_type": "pan_card"},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    # Profile assertions
    assert profile_resp.status_code == 201
    pdata = profile_resp.json()
    assert pdata["firm_name"] == "Test Exports Ltd"
    assert pdata["pan"] == "ABCDE1234F"
    assert pdata["profile_version"] == 1
    assert "id" in pdata
    assert "user_id" in pdata

    # Upload assertions
    assert upload_resp.status_code == 201
    udata = upload_resp.json()
    assert udata["doc_type"] == "pan_card"
    assert udata["filename"] == "pan_card.pdf"
    assert "id" in udata
    assert "checksum_sha256" in udata
    assert "uploaded_at" in udata


# ===========================================================================
# Scenario 4 — Order auto-fill from profile
# ===========================================================================


async def test_e2e_04_order_auto_fill_from_profile(
    test_seller: dict[str, str],
) -> None:
    """POST /orders → 201 with profile fields auto-filled (IEC, bank, exporter).

    Verifies the order inherits profile data: iec, bank_name, exporter_name, etc."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"])

        # Fetch the created order
        get_resp = await client.get(
            f"/orders/{order_id}",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert get_resp.status_code == 200
    odata = get_resp.json()

    # Auto-filled from profile
    assert odata["iec"] == "1234567890"
    assert odata["bank_name"] == "State Bank of India"
    assert odata["ifsc"] == "SBIN0001234"
    assert odata["bank_account"] == "12345678901"
    assert odata["ad_code"] == "9876543"
    assert odata["exporter_name"] == "Test Exports Ltd"
    assert "Mumbai" in odata["exporter_address"]
    assert odata["state_code"] == "Maharashtr"  # truncated to String(10)

    # User-submitted
    assert odata["destination_country"] == "US"
    assert odata["value_minor"] == 50000
    assert odata["status"] == "created"
    assert odata["seller_id"] == test_seller["user_id"]
    assert odata["line_items"][0]["description"] == "Cotton T-Shirts"


# ===========================================================================
# Scenario 5 — Doc pack generation + QR generation
# ===========================================================================


async def test_e2e_05_doc_pack_and_qr_generation(
    test_seller: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Generate docs → 201, then generate QR → 201 with valid doc_access JWT.

    Verifies all 4 doc types present and QR response contains decodable token."""
    # Mock Redis for QR router
    dummy_redis = AsyncMock()
    dummy_redis.exists = AsyncMock(return_value=0)
    monkeypatch.setattr("storage.redis.get_redis", lambda: dummy_redis)

    async def _is_not_revoked(_jti: str, _redis: object) -> bool:
        return False

    monkeypatch.setattr("app.routers.qr.is_revoked", _is_not_revoked)
    monkeypatch.setattr("app.routers.qr.revoke_token", AsyncMock())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"])

        # Generate doc pack
        docs_resp = await _generate_docs(client, test_seller["token"], order_id)

        # Generate QR
        qr_resp = await _generate_qr(client, test_seller["token"], order_id)

    # Doc pack assertions
    assert docs_resp["order_id"] == order_id
    assert "id" in docs_resp
    docs = docs_resp["documents"]
    assert "commercial_invoice" in docs
    assert "packing_list" in docs
    assert "customs_declaration" in docs
    assert "postal_bill_of_export" in docs
    assert docs["commercial_invoice"]["exporter_name"] == "Test Exports Ltd"

    # QR assertions
    assert qr_resp["order_id"] == order_id
    assert "qr_url" in qr_resp
    assert "token" in qr_resp
    assert "token_jti" in qr_resp
    assert "token_expiry" in qr_resp
    assert "qr_image_path" in qr_resp

    # QR token is a valid doc_access JWT
    decoded = decode_token(
        qr_resp["token"],
        _settings.JWT_SECRET_KEY,
        _settings.JWT_ALGORITHM,
    )
    assert decoded["sub"] == order_id
    assert decoded["purpose"] == "doc_access"
    assert decoded["jti"] == qr_resp["token_jti"]


# ===========================================================================
# Scenario 6 — Sahayak QR access → decrypted PAN visible
# ===========================================================================


async def test_e2e_06_sahayak_qr_access_decrypted_pan(
    test_seller: dict[str, str],
    test_sahayak: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Sahayak accesses order docs via QR token → 200 with decrypted PAN.

    Verifies sahayak can see sensitive fields (PAN, bank_account, ad_code)."""
    dummy_redis = AsyncMock()
    dummy_redis.exists = AsyncMock(return_value=0)
    monkeypatch.setattr("storage.redis.get_redis", lambda: dummy_redis)

    async def _is_not_revoked(_jti: str, _redis: object) -> bool:
        return False

    monkeypatch.setattr("app.routers.qr.is_revoked", _is_not_revoked)
    monkeypatch.setattr("app.routers.qr.revoke_token", AsyncMock())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"])
        await _generate_docs(client, test_seller["token"], order_id)
        qr_data = await _generate_qr(client, test_seller["token"], order_id)

        # Sahayak accesses docs with QR token
        resp = await client.get(
            f"/orders/{order_id}/docs",
            params={"token": qr_data["token"]},
            headers={"Authorization": f"Bearer {test_sahayak['token']}"},
        )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["pan"] == "ABCDE1234F"
    assert data["bank_account"] is not None
    assert data["ad_code"] is not None
    assert data["gstin"] is not None
    assert data["iec"] is not None
    assert data["order_id"] == order_id
    assert data["status"] in ("qr_generated", "docs_generated")
    assert data["doc_pack"] is not None


# ===========================================================================
# Scenario 7 — Wrong seller QR access → 403
# ===========================================================================


async def test_e2e_07_wrong_seller_qr_access_403(
    test_seller: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Different seller with valid doc_access token → 403.

    Verifies a seller who does not own the order cannot access docs via QR."""
    dummy_redis = AsyncMock()
    dummy_redis.exists = AsyncMock(return_value=0)
    monkeypatch.setattr("storage.redis.get_redis", lambda: dummy_redis)

    async def _is_not_revoked(_jti: str, _redis: object) -> bool:
        return False

    monkeypatch.setattr("app.routers.qr.is_revoked", _is_not_revoked)
    monkeypatch.setattr("app.routers.qr.revoke_token", AsyncMock())

    second_email = f"e2e_wrong_seller_{uuid.uuid4().hex[:8]}@test.com"
    second_seller = await _create_second_seller(second_email)

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            await _create_profile(client, test_seller["token"])
            order_id = await _create_order(client, test_seller["token"])
            await _generate_docs(client, test_seller["token"], order_id)
            qr_data = await _generate_qr(client, test_seller["token"], order_id)

            # Second seller tries to access the same docs
            resp = await client.get(
                f"/orders/{order_id}/docs",
                params={"token": qr_data["token"]},
                headers={"Authorization": f"Bearer {second_seller['token']}"},
            )

        assert resp.status_code == 403, resp.text
    finally:
        # Cleanup second seller
        async with _db_get_session()() as session:
            result = await session.execute(
                select(User).where(User.email == second_email)
            )
            u = result.scalar_one_or_none()
            if u is not None:
                await session.delete(u)
                await session.commit()


# ===========================================================================
# Scenario 8 — No auth QR access → 401
# ===========================================================================


async def test_e2e_08_no_auth_qr_access_401(
    test_seller: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """GET /orders/{id}/docs?token=X without Authorization header → 401.

    Verifies the docs endpoint requires user authentication."""
    dummy_redis = AsyncMock()
    dummy_redis.exists = AsyncMock(return_value=0)
    monkeypatch.setattr("storage.redis.get_redis", lambda: dummy_redis)

    async def _is_not_revoked(_jti: str, _redis: object) -> bool:
        return False

    monkeypatch.setattr("app.routers.qr.is_revoked", _is_not_revoked)
    monkeypatch.setattr("app.routers.qr.revoke_token", AsyncMock())

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"])
        await _generate_docs(client, test_seller["token"], order_id)
        qr_data = await _generate_qr(client, test_seller["token"], order_id)

        # No auth header
        resp = await client.get(
            f"/orders/{order_id}/docs",
            params={"token": qr_data["token"]},
        )

    assert resp.status_code == 401, resp.text


# ===========================================================================
# Scenario 9 — QR regeneration → old token revoked, new token works
# ===========================================================================


async def test_e2e_09_qr_regeneration_old_revoked_new_works(
    test_seller: dict[str, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Generate QR twice → old token returns 401, new token works.

    Verifies that revoke_token is called for the old JTI and the new token
    still grants access via the docs endpoint."""
    # Track revocation state
    revoked_jtis: set[str] = set()

    async def _track_revoke(jti: str, exp: object, redis_client: object) -> None:
        revoked_jtis.add(jti)

    async def _check_revoked(jti: str, redis_client: object) -> bool:
        return jti in revoked_jtis

    dummy_redis = AsyncMock()
    dummy_redis.exists = AsyncMock(return_value=0)
    monkeypatch.setattr("storage.redis.get_redis", lambda: dummy_redis)
    monkeypatch.setattr("app.routers.qr.revoke_token", _track_revoke)
    monkeypatch.setattr("app.routers.qr.is_revoked", _check_revoked)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"])
        await _generate_docs(client, test_seller["token"], order_id)

        # First QR
        qr1 = await _generate_qr(client, test_seller["token"], order_id)

        # Second QR — this revokes the first
        qr2 = await _generate_qr(client, test_seller["token"], order_id)

        # Old token should be rejected
        old_resp = await client.get(
            f"/orders/{order_id}/docs",
            params={"token": qr1["token"]},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

        # New token should work
        new_resp = await client.get(
            f"/orders/{order_id}/docs",
            params={"token": qr2["token"]},
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    # Old token is revoked
    assert old_resp.status_code == 401, old_resp.text
    assert "revoked" in old_resp.json()["detail"].lower()

    # New token works
    assert new_resp.status_code == 200, new_resp.text
    ndata = new_resp.json()
    assert ndata["pan"] == "ABCDE1234F"
    assert ndata["order_id"] == order_id

    # Verify old jti was tracked as revoked
    assert qr1["token_jti"] in revoked_jtis
    assert qr2["token_jti"] not in revoked_jtis
    assert qr1["token_jti"] != qr2["token_jti"]


# ===========================================================================
# Scenario 10 — Rate limit → 6th login returns 429
# ===========================================================================


async def test_e2e_10_rate_limit_6th_login_429(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """6 rapid POST /auth/login calls → first 5 pass, 6th returns 429.

    Uses a fake Redis and frozen time to simulate rate limiting.  The first
    5 requests are not asserted as 401 (which is the actual auth response
    for invalid credentials) — only that they are NOT 429."""
    _patch_storage_db_get_session(monkeypatch)

    fake_redis = _FakeRateLimitRedis()
    monkeypatch.setattr(f"{_RATE_LIMIT_MOD}.get_redis", lambda: fake_redis)

    # Freeze time
    frozen_s = _stdlib_time.time()

    class _Frozen:
        @staticmethod
        def time() -> float:
            return frozen_s

    monkeypatch.setattr(f"{_RATE_LIMIT_MOD}.time", _Frozen)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 5 requests — all should pass (may be 401 for wrong password, but NOT 429)
        for i in range(1, 6):
            resp = await client.post(
                "/auth/login",
                json={"email": f"rl{i}@test.com", "password": "wrongpass"},
            )
            assert resp.status_code != 429, (
                f"Request {i} was unexpectedly rate-limited (status={resp.status_code})"
            )

        # 6th request — should be rate limited
        resp6 = await client.post(
            "/auth/login",
            json={"email": "rl6@test.com", "password": "wrongpass"},
        )

    assert resp6.status_code == 429
    assert resp6.headers.get("Retry-After") is not None
    assert int(resp6.headers["Retry-After"]) > 0
    assert resp6.json()["detail"] == "Rate limit exceeded. Try again later."
    assert resp6.headers["X-RateLimit-Limit"] == "5"
    assert resp6.headers["X-RateLimit-Remaining"] == "0"


# ===========================================================================
# Scenario 11 — Password reset flow
# ===========================================================================


async def test_e2e_11_password_reset_flow(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Full password-reset flow: request → reset → login with new password.

    Verifies the old password is rejected and the new one works."""
    _patch_storage_db_get_session(monkeypatch)

    email = f"e2e_pwreset_{uuid.uuid4().hex[:8]}@test.com"
    old_password = "originalPass123"
    new_password = "newSecurePass456"

    # Use a fake Redis so pwreset tokens are stored.  The rate-limiter
    # middleware and auth.routes both import get_redis at module level,
    # so we must patch their local references too.
    fake_redis = _FakeRateLimitRedis()
    monkeypatch.setattr("storage.redis.get_redis", lambda: fake_redis)
    monkeypatch.setattr("auth.middleware.get_redis", lambda: fake_redis)
    monkeypatch.setattr("auth.routes.get_redis", lambda: fake_redis)
    monkeypatch.setattr(f"{_RATE_LIMIT_MOD}.get_redis", lambda: fake_redis)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register user
        reg_resp = await client.post(
            "/auth/register",
            json={"email": email, "password": old_password, "role": "seller"},
        )
        assert reg_resp.status_code == 201

        # Login with old password → works
        login_old = await client.post(
            "/auth/login",
            json={"email": email, "password": old_password},
        )
        assert login_old.status_code == 200

        # Request password reset — this stores the token hash in our fake Redis
        reset_req = await client.post(
            "/auth/password-reset-request",
            json={"email": email},
        )
        assert reset_req.status_code == 200
        assert "If the email exists" in reset_req.json()["message"]

        # The password-reset-request endpoint generates raw_token internally,
        # hashes it, and stores hash→user_id in Redis.  We simulate the full
        # flow by generating our own token, hashing it the same way, and
        # storing it ourselves.
        raw_token = _secrets.token_hex(32)
        token_hash_val = hashlib.sha256(raw_token.encode()).hexdigest()

        # Look up user ID
        async with _db_get_session()() as session:
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()

        assert user is not None
        fake_redis._kv[f"pwreset:{token_hash_val}"] = str(user.id)

        # Reset password with the token
        reset_do = await client.post(
            "/auth/password-reset",
            json={"token": raw_token, "new_password": new_password},
        )
        assert reset_do.status_code == 200
        assert reset_do.json()["message"] == "Password reset successful"

        # Login with old password → 401
        login_old_again = await client.post(
            "/auth/login",
            json={"email": email, "password": old_password},
        )
        assert login_old_again.status_code == 401

        # Login with new password → 200
        login_new = await client.post(
            "/auth/login",
            json={"email": email, "password": new_password},
        )
        assert login_new.status_code == 200
        assert login_new.json()["user"]["email"] == email

    # Cleanup
    async with _db_get_session()() as session:
        result = await session.execute(select(User).where(User.email == email))
        u = result.scalar_one_or_none()
        if u is not None:
            await session.delete(u)
            await session.commit()


# ===========================================================================
# Scenario 12 — Logout → token blacklisted
# ===========================================================================


async def test_e2e_12_logout_token_blacklisted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Login → get token → logout → token is rejected on subsequent use.

    Verifies that after POST /auth/logout, the access token returns 401."""
    _patch_storage_db_get_session(monkeypatch)

    # Track revoked jtis in a set shared across the auth stack.
    revoked_jtis: set[str] = set()

    async def _track_revoke(jti: str, exp: object, redis_client: object) -> None:
        revoked_jtis.add(jti)

    async def _check_revoked(jti: str, redis_client: object) -> bool:
        return jti in revoked_jtis

    # Prevent rate-limiter from calling real Redis (it imports get_redis
    # at module level so we must patch its local reference).
    monkeypatch.setattr(f"{_RATE_LIMIT_MOD}.get_redis", lambda: MagicMock())

    # Patch is_revoked in the module where auth.middleware imports it from.
    monkeypatch.setattr("auth.services.jwt.is_revoked", _check_revoked)
    monkeypatch.setattr("auth.services.jwt.revoke_token", _track_revoke)
    # Also patch auth.routes since logout calls revoke_token there
    monkeypatch.setattr("auth.routes.revoke_token", _track_revoke)

    email = f"e2e_logout_{uuid.uuid4().hex[:8]}@test.com"

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register
        reg_resp = await client.post(
            "/auth/register",
            json={"email": email, "password": "logoutPass123", "role": "seller"},
        )
        assert reg_resp.status_code == 201

        # Login
        login_resp = await client.post(
            "/auth/login",
            json={"email": email, "password": "logoutPass123"},
        )
        assert login_resp.status_code == 200
        login_data = login_resp.json()
        token = login_data["access_token"]
        assert token is not None

        # Verify token works — call /auth/me
        me_before = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_before.status_code == 200
        assert me_before.json()["email"] == email

        # Logout
        logout_resp = await client.post(
            "/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert logout_resp.status_code == 200
        assert logout_resp.json()["message"] == "Logged out"

    # Now the token should be rejected on subsequent auth requests
    transport2 = ASGITransport(app=app)
    async with AsyncClient(transport=transport2, base_url="http://test") as client2:
        me_after = await client2.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert me_after.status_code == 401

    # Cleanup
    async with _db_get_session()() as session:
        result = await session.execute(select(User).where(User.email == email))
        u = result.scalar_one_or_none()
        if u is not None:
            await session.delete(u)
            await session.commit()
