"""Proxy routes — forward requests to downstream engines.

Routes under /api/validate, /api/pricing, /api/tracking, and /api/voice
are proxied to the corresponding microservice.  Auth is required via
the JWTAuthMiddleware and the get_current_user dependency.

ConnectError → 503 (service unavailable)
TimeoutException → 504 (gateway timeout)
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import httpx
from auth.deps import get_current_user
from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse, StreamingResponse
from storage.config import settings

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/api", tags=["proxy"])

# ---------------------------------------------------------------------------
# HTTP methods we accept
# ---------------------------------------------------------------------------

_ALL_METHODS = {"GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"}

# ---------------------------------------------------------------------------
# Proxy helper
# ---------------------------------------------------------------------------


async def _proxy(
    request: Request,
    base_url: str,
    path: str,
    service_name: str,
    timeout_s: float = 30.0,
) -> StreamingResponse | JSONResponse:
    """Forward the incoming request to a downstream engine.

    Args:
        request: Incoming FastAPI request.
        base_url: Downstream service URL (e.g. http://pricing-engine:8000).
        path: Remaining path segment captured from the URL.
        service_name: Human-readable service name for error messages.
        timeout_s: Total request timeout in seconds.
    """
    target_url = _build_target_url(base_url, path)

    # Selectively forward headers (strip hop-by-hop ones).
    forward_headers = _filter_headers(request.headers, target_url)

    timeout = httpx.Timeout(timeout_s, connect=10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            body = await request.body()
            resp = await client.request(
                method=request.method,
                url=target_url,
                headers=forward_headers,
                params=dict(request.query_params),
                content=body,
            )
        except httpx.ConnectError:
            return JSONResponse(
                status_code=503,
                content={
                    "detail": f"{service_name} service is currently unavailable",
                },
            )
        except httpx.TimeoutException:
            return JSONResponse(
                status_code=504,
                content={"detail": f"{service_name} service timed out"},
            )

    # Build response — stream binary content back to the caller.
    return _build_response(resp)


def _build_target_url(base_url: str, path: str) -> str:
    """Join base_url and captured path into a clean target URL."""
    base = base_url.rstrip("/")
    segment = path.lstrip("/")
    if segment:
        return f"{base}/{segment}"
    return base


def _filter_headers(headers: object, target_url: str) -> dict[str, str]:
    """Return a filtered dict of headers safe to forward.

    Strips hop-by-hop headers (Host, Connection, Transfer-Encoding, etc.)
    and sets a correct Host for the downstream target.
    """
    import urllib.parse

    parsed = urllib.parse.urlparse(target_url)
    host_header = parsed.netloc

    hop_by_hop = frozenset(
        {
            "host",
            "connection",
            "transfer-encoding",
            "te",
            "trailer",
            "upgrade",
            "proxy-authorization",
            "proxy-authenticate",
        }
    )

    fwd: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() in hop_by_hop:
            continue
        fwd[key] = value

    fwd["host"] = host_header
    return fwd


async def _stream_response(resp: httpx.Response) -> AsyncIterator[bytes]:
    """Yield response bytes in chunks."""
    async for chunk in resp.aiter_bytes():
        yield chunk


def _build_response(resp: httpx.Response) -> StreamingResponse:
    """Convert an httpx response into a FastAPI StreamingResponse.

    Filters out hop-by-hop headers from the downstream response as well.
    """
    resp_hop_by_hop = frozenset(
        {
            "transfer-encoding",
            "connection",
            "keep-alive",
            "proxy-authenticate",
            "proxy-authorization",
            "te",
            "trailers",
            "upgrade",
        }
    )
    resp_headers = {
        k: v for k, v in resp.headers.items() if k.lower() not in resp_hop_by_hop
    }

    return StreamingResponse(
        _stream_response(resp),
        status_code=resp.status_code,
        headers=resp_headers,
    )


# ---------------------------------------------------------------------------
# Proxy endpoints — one per downstream service
# ---------------------------------------------------------------------------


@router.api_route(
    "/validate/{path:path}",
    methods=_ALL_METHODS,
    response_model=None,
    dependencies=[Depends(get_current_user)],
)
async def proxy_validate(request: Request, path: str = "") -> StreamingResponse | JSONResponse:
    """Proxy to the Validation Engine."""
    return await _proxy(request, settings.VALIDATION_ENGINE_URL, path, "Validation")


@router.api_route(
    "/pricing/{path:path}",
    methods=_ALL_METHODS,
    response_model=None,
    dependencies=[Depends(get_current_user)],
)
async def proxy_pricing(request: Request, path: str = "") -> StreamingResponse | JSONResponse:
    """Proxy to the Pricing Engine."""
    return await _proxy(request, settings.PRICING_ENGINE_URL, path, "Pricing")


@router.api_route(
    "/tracking/{path:path}",
    methods=_ALL_METHODS,
    response_model=None,
    dependencies=[Depends(get_current_user)],
)
async def proxy_tracking(request: Request, path: str = "") -> StreamingResponse | JSONResponse:
    """Proxy to the Tracking API."""
    return await _proxy(request, settings.TRACKING_API_URL, path, "Tracking")


@router.api_route(
    "/voice/{path:path}",
    methods=_ALL_METHODS,
    response_model=None,
    dependencies=[Depends(get_current_user)],
)
async def proxy_voice(request: Request, path: str = "") -> StreamingResponse | JSONResponse:
    """Proxy to the Voice Pipeline."""
    return await _proxy(request, settings.VOICE_PIPELINE_URL, path, "Voice")
