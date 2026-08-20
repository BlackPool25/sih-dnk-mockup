"""Marketplace proxy — backend-core /api/marketplace/* → marketplace service.

Proxies to MARKETPLACE_URL (default http://marketplace:8000/marketplace/*).
Forwards query params (limit/category/price/country), preserves Authorization,
adds X-Proxied: marketplace header, returns 502 when downstream down.
"""

from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, Header, Request
from fastapi.responses import JSONResponse

from storage.config import settings

router = APIRouter(prefix="/api/marketplace", tags=["marketplace-proxy"])

_MARKETPLACE_URL = os.environ.get("MARKETPLACE_URL", "http://marketplace:8000")

# Also try settings if present
try:
    _cfg_url: str | None = getattr(settings, "MARKETPLACE_URL", None)
    if _cfg_url:
        _MARKETPLACE_URL = _cfg_url
except Exception:
    pass


def _marketplace_url() -> str:
    url = os.environ.get("MARKETPLACE_URL")
    if url:
        return url.rstrip("/")
    try:
        v = getattr(settings, "MARKETPLACE_URL", None)
        if isinstance(v, str) and v:
            return v.rstrip("/")
    except Exception:
        pass
    return "http://marketplace:8000"


def _forward_headers(request: Request, extra: dict[str, str] | None = None) -> dict[str, str]:
    headers: dict[str, str] = {}
    auth = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth:
        headers["Authorization"] = auth
    # preserve X-Request-Id if present
    rid = request.headers.get("X-Request-Id") or request.headers.get("x-request-id")
    if rid:
        headers["X-Request-Id"] = rid
    # preserve X-Seller-Id for product creation
    sid = request.headers.get("X-Seller-Id") or request.headers.get("x-seller-id")
    if sid:
        headers["X-Seller-Id"] = sid
    if extra:
        headers.update(extra)
    return headers


async def _proxy_get(
    path: str,
    request: Request,
    params: dict[str, str | int | None] | None = None,
) -> JSONResponse:
    base = _marketplace_url()
    target = f"{base}{path}"
    # filter None params
    q: dict[str, str] = {}
    if params:
        for k, v in params.items():
            if v is not None:
                q[k] = str(v)
    # also include any original query params not explicitly listed
    for k, v in request.query_params.items():
        if k not in q:
            q[k] = v
    headers = _forward_headers(request)
    timeout = httpx.Timeout(10.0, connect=5.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(target, params=q, headers=headers)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.TimeoutException):
        return JSONResponse(
            status_code=502,
            content={"detail": "marketplace service unavailable", "mocked": True},
            headers={"X-Proxied": "marketplace"},
        )
    except httpx.RequestError:
        return JSONResponse(
            status_code=502,
            content={"detail": "marketplace service unavailable", "mocked": True},
            headers={"X-Proxied": "marketplace"},
        )
    # pass through status and body, add X-Proxied header
    try:
        body = resp.json()
    except Exception:
        body = {"raw": resp.text, "mocked": True}
    return JSONResponse(
        status_code=resp.status_code,
        content=body,
        headers={"X-Proxied": "marketplace"},
    )


async def _proxy_post(
    path: str,
    request: Request,
    x_seller_id: str | None = None,
) -> JSONResponse:
    base = _marketplace_url()
    target = f"{base}{path}"
    extra: dict[str, str] = {}
    if x_seller_id:
        extra["X-Seller-Id"] = x_seller_id
    headers = _forward_headers(request, extra)
    # ensure content-type json if not present
    if "content-type" not in {k.lower() for k in headers}:
        headers["Content-Type"] = "application/json"
    try:
        body_bytes = await request.body()
    except Exception:
        body_bytes = b"{}"
    timeout = httpx.Timeout(10.0, connect=5.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(target, content=body_bytes, headers=headers)
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.TimeoutException):
        return JSONResponse(
            status_code=502,
            content={"detail": "marketplace service unavailable", "mocked": True},
            headers={"X-Proxied": "marketplace"},
        )
    except httpx.RequestError:
        return JSONResponse(
            status_code=502,
            content={"detail": "marketplace service unavailable", "mocked": True},
            headers={"X-Proxied": "marketplace"},
        )
    try:
        body = resp.json()
    except Exception:
        body = {"raw": resp.text, "mocked": True}
    return JSONResponse(
        status_code=resp.status_code,
        content=body,
        headers={"X-Proxied": "marketplace"},
    )


@router.get("/feed")
async def marketplace_feed_proxy(
    request: Request,
    limit: int | None = None,
    category: str | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    country: str | None = None,
) -> JSONResponse:
    params: dict[str, str | int | None] = {
        "limit": limit,
        "category": category,
        "price_min": price_min,
        "price_max": price_max,
        "country": country,
    }
    return await _proxy_get("/marketplace/feed", request, params)


@router.get("/metrics")
async def marketplace_metrics_proxy(request: Request) -> JSONResponse:
    return await _proxy_get("/marketplace/metrics", request)


@router.get("/ranking/preview")
async def marketplace_ranking_preview_proxy(request: Request) -> JSONResponse:
    return await _proxy_get("/marketplace/ranking/preview", request)


@router.post("/products")
async def marketplace_products_proxy(
    request: Request,
    x_seller_id: str | None = Header(default=None, alias="X-Seller-Id"),
) -> JSONResponse:
    return await _proxy_post("/marketplace/products", request, x_seller_id=x_seller_id)
