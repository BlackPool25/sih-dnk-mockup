"""ASGI middleware for JWT authentication.

Extracts and validates Bearer tokens from the Authorization header, decodes
the JWT payload, checks the token revocation blacklist, and injects user
identity and the current token's JTI into ``request.state`` so downstream
route handlers and dependencies can access them without re-parsing the token.

Import as::

    from auth.middleware import JWTAuthMiddleware
"""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from storage.config import settings
from storage.redis import get_redis

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Public paths — no authentication required
# ---------------------------------------------------------------------------

PUBLIC_AUTH_PATHS: frozenset[str] = frozenset(
    {
        "/auth/login",
        "/auth/register",
        "/auth/refresh",
        "/auth/password-reset-request",
        "/auth/password-reset",
    }
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _auth_error(status_code: int, detail: str) -> JSONResponse:
    """Return a JSON error response for authentication failures.

    Uses ``JSONResponse`` rather than raising ``HTTPException`` because
    ``BaseHTTPMiddleware.dispatch`` does not route exceptions through
    FastAPI's exception handlers — they propagate as raw exceptions.
    """
    return JSONResponse(status_code=status_code, content={"detail": detail})


# ---------------------------------------------------------------------------
# Public middleware class
# ---------------------------------------------------------------------------


class JWTAuthMiddleware(BaseHTTPMiddleware):
    """FastAPI / Starlette ASGI middleware that authenticates every request.

    Extracts the ``Bearer`` token, decodes and validates it, checks the
    Redis revocation blacklist, and injects ``request.state.user``
    (``{"user_id": str, "role": str, "email": str}``) and
    ``request.state.jti`` (str) for downstream use.

    Unauthenticated / invalid / revoked tokens receive a 401 response.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        """Authenticate the request before passing it to the next handler.

        Returns a 401 ``JSONResponse`` when authentication fails;
        otherwise delegates to the next handler in the stack.
        """
        # 0. Skip auth for public endpoints -----------------------------------------
        if request.url.path in PUBLIC_AUTH_PATHS:
            return await call_next(request)

        # 1. Extract Bearer token -------------------------------------------------
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return _auth_error(401, "Missing or malformed Authorization header")

        token = auth_header[len("Bearer ") :].strip()
        if not token:
            return _auth_error(401, "Empty Bearer token")

        # 2. Decode the JWT -------------------------------------------------------
        # Deferred import so the module is usable even before auth.services.jwt is
        # fully wired (Task 7 creates this in parallel).
        try:
            from auth.services.jwt import decode_token
        except ImportError:
            return _auth_error(401, "JWT service unavailable")

        try:
            payload: dict[str, object] = decode_token(
                token,
                settings.JWT_SECRET_KEY,
                settings.JWT_ALGORITHM,
            )
        except Exception:
            logger.debug("JWT decode failed", exc_info=True)
            return _auth_error(401, "Invalid or expired token")

        # 3. Check revocation blacklist --------------------------------------------
        jti = payload.get("jti")
        if jti is None or not isinstance(jti, str):
            return _auth_error(401, "Token missing JTI claim")

        try:
            from auth.services.jwt import is_revoked
        except ImportError:
            return _auth_error(401, "JWT service unavailable")

        redis_client = get_redis()
        if await is_revoked(jti, redis_client):
            return _auth_error(401, "Token has been revoked")

        # 4. Inject state for downstream handlers ----------------------------------
        user_id = payload.get("sub")
        role = payload.get("role")
        email = payload.get("email")

        if not isinstance(user_id, str) or not isinstance(role, str) or not isinstance(email, str):
            return _auth_error(401, "Token payload missing required claims (sub, role, email)")

        request.state.user = {
            "user_id": str(user_id),
            "role": str(role),
            "email": str(email),
        }
        request.state.jti = str(jti)

        return await call_next(request)
