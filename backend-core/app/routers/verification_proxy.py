"""Verification proxy — backend-core → verification-service.

Proxies /verify/*, /trust/*, /bindings/* to VERIFICATION_SERVICE_URL
(default http://verification-service:8000). Forwards Authorization,
X-Request-Id, Content-Type. Returns 502 with mocked:true when downstream down.
"""

from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from storage.config import settings

router = APIRouter(tags=["verification-proxy"])


def _verification_url() -> str:
    url = os.environ.get("VERIFICATION_SERVICE_URL")
    if url:
        return url.rstrip("/")
    try:
        v = getattr(settings, "VERIFICATION_SERVICE_URL", None)
        if isinstance(v, str) and v:
            return v.rstrip("/")
    except Exception:
        pass
    return "http://verification-service:8000"


def _forward_headers(request: Request) -> dict[str, str]:
    headers: dict[str, str] = {}
    auth = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth:
        headers["Authorization"] = auth
    rid = request.headers.get("X-Request-Id") or request.headers.get("x-request-id") or request.headers.get("X-Request-ID")
    if rid:
        headers["X-Request-Id"] = rid
    ctype = request.headers.get("Content-Type") or request.headers.get("content-type")
    if ctype:
        headers["Content-Type"] = ctype
    return headers


async def _proxy(request: Request, target_path: str, method: str | None = None) -> JSONResponse:
    base = _verification_url()
    target = f"{base}{target_path}"
    headers = _forward_headers(request)
    params = dict(request.query_params)
    try:
        body_bytes = await request.body()
    except Exception:
        body_bytes = b""
    http_method = method or request.method
    timeout = httpx.Timeout(10.0, connect=5.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.request(
                method=http_method,
                url=target,
                params=params,
                content=body_bytes if body_bytes else None,
                headers=headers,
            )
    except (httpx.ConnectError, httpx.ConnectTimeout, httpx.ReadTimeout, httpx.TimeoutException, httpx.RequestError):
        return JSONResponse(
            status_code=502,
            content={"detail": "verification service unavailable", "mocked": True},
            headers={"X-Proxied": "verification"},
        )
    try:
        body = resp.json()
    except Exception:
        body = {"raw": resp.text, "mocked": True}
    return JSONResponse(
        status_code=resp.status_code,
        content=body,
        headers={"X-Proxied": "verification"},
    )


# --- Generic catch-alls (covers all verify/trust/bindings routes) ---


@router.api_route("/verify/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_verify(request: Request, path: str) -> JSONResponse:
    return await _proxy(request, f"/verify/{path}")


@router.api_route("/trust/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_trust(request: Request, path: str) -> JSONResponse:
    return await _proxy(request, f"/trust/{path}")


@router.api_route("/bindings/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_bindings(request: Request, path: str) -> JSONResponse:
    return await _proxy(request, f"/bindings/{path}")
