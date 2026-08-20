"""Messaging + Quotes proxy — backend-core → messaging-service.

Proxies /messages/* and /quotes/* to MESSAGING_SERVICE_URL
(default http://messaging-service:8000). Forwards Authorization,
X-Request-Id, Content-Type, X-Buyer-Id. Handles multipart for
POST /messages/threads/{id}/messages. WS at /messages/ws/threads/{id}
is bridged via websockets. Returns 502 with mocked:true when downstream down.
"""

from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from storage.config import settings

router = APIRouter(tags=["messaging-proxy"])


def _messaging_url() -> str:
    url = os.environ.get("MESSAGING_SERVICE_URL")
    if url:
        return url.rstrip("/")
    try:
        v = getattr(settings, "MESSAGING_SERVICE_URL", None)
        if isinstance(v, str) and v:
            return v.rstrip("/")
    except Exception:
        pass
    return "http://messaging-service:8000"


def _forward_headers(request: Request, extra: dict[str, str] | None = None) -> dict[str, str]:
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
    buyer = request.headers.get("X-Buyer-Id") or request.headers.get("x-buyer-id")
    if buyer:
        headers["X-Buyer-Id"] = buyer
    seller = request.headers.get("X-Seller-Id") or request.headers.get("x-seller-id")
    if seller:
        headers["X-Seller-Id"] = seller
    if extra:
        headers.update(extra)
    return headers


def _ws_target_url(thread_id: str, query_string: str) -> str:
    base = _messaging_url()
    # convert http://host:port → ws://host:port
    if base.startswith("https://"):
        ws_base = "wss://" + base[len("https://") :]
    elif base.startswith("http://"):
        ws_base = "ws://" + base[len("http://") :]
    else:
        ws_base = base
    ws_base = ws_base.rstrip("/")
    target = f"{ws_base}/messages/ws/threads/{thread_id}"
    if query_string:
        target = f"{target}?{query_string}"
    return target


async def _proxy_generic(
    request: Request,
    target_path: str,
    method: str | None = None,
) -> JSONResponse:
    base = _messaging_url()
    target = f"{base}{target_path}"
    headers = _forward_headers(request)
    # Build query passthrough from original request
    params = dict(request.query_params)
    try:
        body_bytes = await request.body()
    except Exception:
        body_bytes = b""
    # For GET without body, don't send content
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
            content={"detail": "messaging service unavailable", "mocked": True},
            headers={"X-Proxied": "messaging"},
        )
    try:
        body = resp.json()
    except Exception:
        body = {"raw": resp.text, "mocked": True}
    return JSONResponse(
        status_code=resp.status_code,
        content=body,
        headers={"X-Proxied": "messaging"},
    )


# --- Messages ---


@router.post("/messages/threads")
async def proxy_create_thread(request: Request) -> JSONResponse:
    return await _proxy_generic(request, "/messages/threads", method="POST")


@router.get("/messages/inbox")
async def proxy_inbox(request: Request) -> JSONResponse:
    return await _proxy_generic(request, "/messages/inbox", method="GET")


@router.get("/messages/threads/{thread_id}")
async def proxy_get_thread(request: Request, thread_id: str) -> JSONResponse:
    return await _proxy_generic(request, f"/messages/threads/{thread_id}", method="GET")


@router.get("/messages/threads/{thread_id}/messages")
async def proxy_list_messages(request: Request, thread_id: str) -> JSONResponse:
    return await _proxy_generic(request, f"/messages/threads/{thread_id}/messages", method="GET")


@router.post("/messages/threads/{thread_id}/messages")
async def proxy_post_message(request: Request, thread_id: str) -> JSONResponse:
    # preserves multipart Content-Type + body bytes
    return await _proxy_generic(request, f"/messages/threads/{thread_id}/messages", method="POST")


@router.get("/messages/threads/{thread_id}/poll")
async def proxy_poll(request: Request, thread_id: str) -> JSONResponse:
    return await _proxy_generic(request, f"/messages/threads/{thread_id}/poll", method="GET")


@router.get("/messages/ws")
async def proxy_ws_info(request: Request) -> JSONResponse:
    return await _proxy_generic(request, "/messages/ws", method="GET")


@router.websocket("/messages/ws/threads/{thread_id}")
async def proxy_ws_thread(websocket: WebSocket, thread_id: str) -> None:
    # Accept client WS, then bridge to downstream messaging-service WS
    # Forward Authorization via ?token= query param fallback per messaging-service auth
    # Also extract Authorization header for forwarding as query param if needed
    auth = websocket.headers.get("Authorization") or websocket.headers.get("authorization")
    qs = websocket.url.query
    if auth and "token=" not in qs:
        # messaging-service accepts token via query; strip Bearer
        token = auth.removeprefix("Bearer ").strip() if auth.startswith("Bearer ") else auth
        qs = f"{qs}&token={token}" if qs else f"token={token}"
    target = _ws_target_url(thread_id, qs)
    await websocket.accept()
    try:
        import websockets  # type: ignore
        import websockets.exceptions  # type: ignore
    except ImportError:
        await websocket.close(code=1011)
        return
    try:
        async with websockets.connect(target) as downstream:  # type: ignore[attr-defined]
            # Bidirectional relay
            import asyncio

            async def client_to_downstream() -> None:
                try:
                    while True:
                        data = await websocket.receive_text()
                        await downstream.send(data)
                except WebSocketDisconnect:
                    await downstream.close()
                except Exception:
                    try:
                        await downstream.close()
                    except Exception:
                        pass

            async def downstream_to_client() -> None:
                try:
                    async for msg in downstream:
                        # msg may be str or bytes
                        if isinstance(msg, bytes):
                            await websocket.send_bytes(msg)
                        else:
                            await websocket.send_text(str(msg))
                except websockets.exceptions.ConnectionClosed:
                    pass
                except Exception:
                    pass
                finally:
                    try:
                        await websocket.close()
                    except Exception:
                        pass

            await asyncio.gather(client_to_downstream(), downstream_to_client())
    except Exception:
        try:
            await websocket.close(code=1011)
        except Exception:
            pass


# --- Quotes ---


@router.post("/quotes")
async def proxy_create_quote(request: Request) -> JSONResponse:
    return await _proxy_generic(request, "/quotes", method="POST")


@router.get("/quotes/by-order/{order_id}")
async def proxy_quotes_by_order(request: Request, order_id: str) -> JSONResponse:
    return await _proxy_generic(request, f"/quotes/by-order/{order_id}", method="GET")


@router.get("/quotes/{quote_id}")
async def proxy_get_quote(request: Request, quote_id: str) -> JSONResponse:
    return await _proxy_generic(request, f"/quotes/{quote_id}", method="GET")


@router.post("/quotes/{quote_id}/approve")
async def proxy_approve_quote(request: Request, quote_id: str) -> JSONResponse:
    return await _proxy_generic(request, f"/quotes/{quote_id}/approve", method="POST")


@router.post("/quotes/{quote_id}/reject")
async def proxy_reject_quote(request: Request, quote_id: str) -> JSONResponse:
    return await _proxy_generic(request, f"/quotes/{quote_id}/reject", method="POST")


@router.post("/quotes/{quote_id}/revise")
async def proxy_revise_quote(request: Request, quote_id: str) -> JSONResponse:
    return await _proxy_generic(request, f"/quotes/{quote_id}/revise", method="POST")


@router.post("/quotes/{quote_id}/mock-pay")
async def proxy_mock_pay(request: Request, quote_id: str) -> JSONResponse:
    return await _proxy_generic(request, f"/quotes/{quote_id}/mock-pay", method="POST")


@router.post("/quotes/{quote_id}/webhook")
async def proxy_webhook(request: Request, quote_id: str) -> JSONResponse:
    return await _proxy_generic(request, f"/quotes/{quote_id}/webhook", method="POST")


@router.post("/payment/mock/generate")
async def proxy_payment_generate(request: Request) -> JSONResponse:
    return await _proxy_generic(request, "/payment/mock/generate", method="POST")


@router.get("/payment/mock/{payment_id}")
async def proxy_payment_get(request: Request, payment_id: str) -> JSONResponse:
    return await _proxy_generic(request, f"/payment/mock/{payment_id}", method="GET")


@router.post("/payment/mock/{payment_id}/pay")
async def proxy_payment_pay(request: Request, payment_id: str) -> JSONResponse:
    return await _proxy_generic(request, f"/payment/mock/{payment_id}/pay", method="POST")
