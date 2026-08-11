"""Redis sliding-window rate limiter as FastAPI / Starlette middleware.

Uses Redis sorted sets for per-IP + per-endpoint tracking:

- **Key pattern**: ``ratelimit:{ip}:{endpoint_path}``
- **Operations**: ZADD (add timestamp), ZREMRANGEBYSCORE (prune old entries),
  ZCARD (count requests in window)
- **Thresholds**: Per-path from :mod:`storage.config` — ``/auth/login`` →
  ``RATE_LIMIT_LOGIN_TUPLE``, ``/auth/register`` →
  ``RATE_LIMIT_REGISTER_TUPLE``, everything else →
  ``RATE_LIMIT_DEFAULT_TUPLE``.
- **On limit**: 429 with ``Retry-After`` header (seconds until next slot opens).
- **Fail-open**: If Redis is unreachable, skip rate limiting and log a warning.

Import as::

    from app.middleware.rate_limiter import RateLimitMiddleware
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from typing import ClassVar

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from storage.config import settings
from storage.redis import get_redis

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_KEY_PREFIX = "ratelimit"

# Map endpoints to their rate-limit tuples from settings.
_ENDPOINT_LIMIT_MAP: dict[str, tuple[int, int]] = {
    "/auth/login": settings.RATE_LIMIT_LOGIN_TUPLE,
    "/auth/register": settings.RATE_LIMIT_REGISTER_TUPLE,
}


# ---------------------------------------------------------------------------
# Lua script — atomic check-and-record
# ---------------------------------------------------------------------------

_RATE_LIMIT_LUA = """
local key = KEYS[1]
local now = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local limit = tonumber(ARGV[3])
local cutoff = now - window * 1000

redis.call('ZREMRANGEBYSCORE', key, '-inf', cutoff)
local count = redis.call('ZCARD', key)

if count >= limit then
    local oldest = redis.call('ZRANGE', key, 0, 0, 'WITHSCORES')
    local wait = window
    if #oldest > 0 then
        wait = math.ceil((oldest[2] - cutoff) / 1000)
    end
    return {count, wait}
end

redis.call('ZADD', key, now, now .. ':' .. (count + 1))
redis.call('EXPIRE', key, window)
return {count + 1, 0}
"""


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


class RateLimitMiddleware(BaseHTTPMiddleware):
    """ASGI middleware that rate-limits requests per IP + endpoint path.

    **Sliding window** — timestamps stored in a Redis sorted set;
    only entries within the last *window* seconds count toward the limit.

    Uses an atomic Lua script so the ZREMRANGEBYSCORE + ZCARD + ZADD
    sequence is executed in a single round-trip with no race condition.
    """

    # ------------------------------------------------------------------
    # Path → limit tuple overrides
    # ------------------------------------------------------------------

    _endpoint_limits: ClassVar[dict[str, tuple[int, int]]] = _ENDPOINT_LIMIT_MAP

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_key(ip: str, path: str) -> str:
        return f"{_KEY_PREFIX}:{ip}:{path}"

    @staticmethod
    def _client_ip(request: Request) -> str:
        """Extract the client IP from the request.

        Checks ``X-Forwarded-For`` first (for proxied deployments), then
        ``X-Real-IP``, then falls back to ``request.client.host``.
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        client = request.client
        if client is not None:
            return client.host

        return "127.0.0.1"

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Rate-limit the request; pass through if Redis is unavailable.

        Steps
        -----
        1. Determine (max_requests, window_seconds) for the endpoint path.
        2. Execute the atomic Lua rate-limit script against Redis.
        3. If over limit, return 429 with ``Retry-After``.
        4. If Redis errors, log and continue (fail-open).
        """
        path = request.url.path
        max_req, window_s = self._endpoint_limits.get(
            path, settings.RATE_LIMIT_DEFAULT_TUPLE
        )

        ip = self._client_ip(request)
        key = self._build_key(ip, path)

        now_ms = int(time.time() * 1000)

        try:
            r = get_redis()
        except Exception:  # noqa: BLE001
            logger.warning(
                "Rate limiting skipped — Redis connection failed for %s", key
            )
            return await call_next(request)

        try:
            lua_sha = getattr(self, "_lua_sha", None)
            if lua_sha is None:
                lua_sha = await r.script_load(_RATE_LIMIT_LUA)
                object.__setattr__(self, "_lua_sha", lua_sha)

            result = await r.evalsha(
                lua_sha,
                1,
                key,
                now_ms,
                window_s,
                max_req,
            )
        except Exception:
            logger.warning(
                "Rate limiting skipped — Redis operation failed for %s",
                key,
                exc_info=True,
            )
            return await call_next(request)

        consumed: int = result[0]
        retry_after: int = result[1]

        # Block before calling the handler when the limit is hit.
        if retry_after > 0:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(max_req),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response: Response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(max_req)
        response.headers["X-RateLimit-Remaining"] = str(max(0, max_req - consumed))
        return response
