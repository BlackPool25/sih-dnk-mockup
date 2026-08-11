"""Tests for auth.services.jwt — token creation, decoding, revocation."""

from datetime import UTC, datetime, timedelta

import jwt as pyjwt
import pytest
from fakeredis import FakeAsyncRedis

from auth.services.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    is_revoked,
    revoke_token,
)

SECRET = "a" * 32  # meets storage.config 32-char minimum
DATA = {"sub": "user-42", "role": "seller"}


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


def test_roundtrip_access():
    """create_access_token → decode_token should return correct claims."""
    token = create_access_token(DATA, SECRET)
    payload = decode_token(token, SECRET)

    assert payload["sub"] == "user-42"
    assert payload["role"] == "seller"
    assert "jti" in payload
    assert "iat" in payload
    assert "exp" in payload
    # exp must be in the future
    now_ts = int(datetime.now(UTC).timestamp())
    assert payload["exp"] > now_ts


def test_roundtrip_refresh():
    """create_refresh_token → decode_token should return correct claims."""
    token = create_refresh_token(DATA, SECRET)
    payload = decode_token(token, SECRET)

    assert payload["sub"] == "user-42"
    assert payload["role"] == "seller"
    assert "jti" in payload
    # Refresh should expire later than an access token
    now_ts = int(datetime.now(UTC).timestamp())
    assert payload["exp"] > now_ts


def test_unique_jti():
    """Two calls to create_access_token must produce different jti values."""
    t1 = create_access_token(DATA, SECRET)
    t2 = create_access_token(DATA, SECRET)
    assert decode_token(t1, SECRET)["jti"] != decode_token(t2, SECRET)["jti"]


# ---------------------------------------------------------------------------
# Expired token
# ---------------------------------------------------------------------------


def test_expired():
    """Decoding a token with a past expiry raises ExpiredSignatureError."""
    token = create_access_token(DATA, SECRET, expires_delta_minutes=0)
    with pytest.raises(pyjwt.ExpiredSignatureError):
        decode_token(token, SECRET)


# ---------------------------------------------------------------------------
# Tampered token
# ---------------------------------------------------------------------------


def test_tampered():
    """Modifying the token payload after signing must fail signature check."""
    token = create_access_token(DATA, SECRET)
    # Flip the last character to break the signature
    tampered = token[:-1] + ("a" if token[-1] != "a" else "b")

    with pytest.raises(pyjwt.InvalidSignatureError):
        decode_token(tampered, SECRET)


# ---------------------------------------------------------------------------
# Wrong secret key
# ---------------------------------------------------------------------------


def test_wrong_secret():
    """Decoding with the wrong key raises InvalidSignatureError."""
    token = create_access_token(DATA, SECRET)
    wrong_key = "b" * 32

    with pytest.raises(pyjwt.InvalidSignatureError):
        decode_token(token, wrong_key)


# ---------------------------------------------------------------------------
# Revocation (async — uses FakeAsyncRedis)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_revocation():
    """After revoking a token's jti, is_revoked must return True."""
    token = create_access_token(DATA, SECRET)
    payload = decode_token(token, SECRET)
    jti = payload["jti"]
    exp = payload["exp"]  # Unix timestamp (int)

    redis_client = FakeAsyncRedis()
    await revoke_token(jti, exp, redis_client)

    assert await is_revoked(jti, redis_client) is True


@pytest.mark.asyncio
async def test_is_revoked_returns_false_for_unknown():
    """A jti that was never revoked must NOT be flagged."""
    redis_client = FakeAsyncRedis()
    assert await is_revoked("nonexistent-jti", redis_client) is False


@pytest.mark.asyncio
async def test_revoke_with_datetime_exp():
    """revoke_token must accept a datetime exp and compute TTL correctly."""
    token = create_access_token(DATA, SECRET, expires_delta_minutes=10)
    payload = decode_token(token, SECRET)
    jti = payload["jti"]
    exp_dt = datetime.now(UTC) + timedelta(minutes=10)

    redis_client = FakeAsyncRedis()
    await revoke_token(jti, exp_dt, redis_client)

    assert await is_revoked(jti, redis_client) is True


@pytest.mark.asyncio
async def test_revoke_already_expired_noop():
    """Revoking an already-expired token is a no-op (TTL <= 0)."""
    redis_client = FakeAsyncRedis()
    past = datetime.now(UTC) - timedelta(minutes=5)
    await revoke_token("stale-jti", past, redis_client)
    # Should not raise; key should not be set
    assert await is_revoked("stale-jti", redis_client) is False
