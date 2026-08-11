"""JWT token management — create, decode, revoke, and blacklist-check tokens.

Uses PyJWT_ (``import jwt``) under the hood.  The Redis client is received as a
parameter so callers inject ``storage.redis.get_redis()`` rather than this
module pulling a global import.

.. _PyJWT: https://pyjwt.readthedocs.io/
"""

import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Any

import jwt

if TYPE_CHECKING:
    import redis.asyncio as redis


# ---------------------------------------------------------------------------
# Token creation
# ---------------------------------------------------------------------------


def create_access_token(
    data: dict[str, Any],
    secret_key: str,
    algorithm: str = "HS256",
    expires_delta_minutes: int = 15,
) -> str:
    """Create a signed JWT access token.

    Args:
        data: Must contain ``"sub"`` (user identifier), ``"role"``, and
            ``"email"`` keys.
        secret_key: HS256 / RS256 / … signing key.
        algorithm: JWT signing algorithm (default ``HS256``).
        expires_delta_minutes: Token lifetime in minutes.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": data["sub"],
        "role": data["role"],
        "email": data["email"],
        "iat": now,
        "exp": now + timedelta(minutes=expires_delta_minutes),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, secret_key, algorithm=algorithm)


def create_refresh_token(
    data: dict[str, Any],
    secret_key: str,
    expires_delta_days: int = 7,
) -> str:
    """Create a signed JWT refresh token with longer expiry.

    Args:
        data: Must contain ``"sub"`` (user identifier), ``"role"``, and
            ``"email"`` keys.
        secret_key: Signing key.
        expires_delta_days: Token lifetime in days.

    Returns:
        Encoded JWT string.
    """
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": data["sub"],
        "role": data["role"],
        "email": data["email"],
        "iat": now,
        "exp": now + timedelta(days=expires_delta_days),
        "jti": str(uuid.uuid4()),
    }
    return jwt.encode(payload, secret_key, algorithm="HS256")


# ---------------------------------------------------------------------------
# Token decoding / validation
# ---------------------------------------------------------------------------


def decode_token(
    token: str,
    secret_key: str,
    algorithm: str = "HS256",
) -> dict[str, Any]:
    """Decode and cryptographically verify a JWT.

    Args:
        token: Encoded JWT string.
        secret_key: Key used to sign the token.
        algorithm: Expected algorithm (default ``HS256``).

    Returns:
        Decoded payload dict.

    Raises:
        jwt.ExpiredSignatureError: Token has expired.
        jwt.InvalidSignatureError: Signature verification failed.
        jwt.InvalidTokenError: Any other JWT validation error.
    """
    return jwt.decode(token, secret_key, algorithms=[algorithm])


# ---------------------------------------------------------------------------
# Revocation / blacklisting (async — Redis-backed)
# ---------------------------------------------------------------------------


async def revoke_token(
    jti: str,
    exp: datetime | int,
    redis_client: "redis.Redis",
) -> None:
    """Blacklist a JWT *jti* in Redis so it cannot be reused.

    The key ``bl:{jti}`` is stored with a TTL that matches the token's
    remaining lifetime.

    Args:
        jti: The JWT ID (``jti`` claim) to blacklist.
        exp: Token expiry — either a UTC-aware ``datetime`` or a Unix
            timestamp (int).  Used to compute the Redis key TTL.
        redis_client: An async Redis client (``redis.asyncio.Redis``).
    """
    if isinstance(exp, datetime):
        now = datetime.now(UTC)
        ttl = int((exp - now).total_seconds())
    else:
        # exp is a JWT "exp" claim — Unix timestamp in seconds
        now_ts = int(datetime.now(UTC).timestamp())
        ttl = exp - now_ts

    if ttl <= 0:
        return  # already expired / nothing to revoke

    await redis_client.set(f"bl:{jti}", "revoked", ex=ttl)


async def is_revoked(jti: str, redis_client: "redis.Redis") -> bool:
    """Check whether a *jti* has been blacklisted.

    Args:
        jti: The JWT ID to look up.
        redis_client: An async Redis client.

    Returns:
        ``True`` if the key ``bl:{jti}`` exists in Redis.
    """
    return await redis_client.exists(f"bl:{jti}") > 0
