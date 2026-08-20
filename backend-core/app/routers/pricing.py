"""Pricing proxy — thin authenticated proxy over validation-engine order pricing + pricing-engine direct.

GET  /orders/{order_id}/pricing  — query pricing (all roles, access-checked)
POST /orders/{order_id}/pricing  — trigger pricing (seller, owner)
POST /pricing/calculate          — ad-hoc quote via pricing-engine (auth required)

Thin proxy only — no math. Verbatim status/body passthrough, propagates
Authorization and X-Request-Id.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.services.pricing_client import (
    InvalidInputError as PricingInvalid,
)
from app.services.pricing_client import (
    NotFoundError as PricingNotFound,
)
from app.services.pricing_client import (
    ServiceUnavailable as PricingUnavailable,
)
from app.services.pricing_client import pricing_client
from app.services.val_client import NotFoundError, ServiceUnavailable, val_client
from auth.deps import get_current_user, require_role

router = APIRouter(tags=["pricing"])


def _fwd_headers(request: Request) -> dict[str, str]:
    h: dict[str, str] = {}
    auth = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth:
        h["Authorization"] = auth
    rid = request.headers.get("X-Request-Id") or request.headers.get("x-request-id") or request.headers.get("X-Request-ID")
    if rid:
        h["X-Request-Id"] = rid
    return h


async def _get_order_or_404(order_id: str) -> dict[str, object]:
    try:
        return await val_client.get_order(order_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail="Order not found") from exc
    except ServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _check_order_access(order: dict[str, object], user: dict[str, str]) -> None:
    user_id = user["user_id"]
    role = user["role"]
    seller_id = str(order.get("seller_id") or "")
    buyer_id = str(order.get("buyer_id") or "")
    if role == "sahayak":
        return
    if role == "seller" and seller_id == user_id:
        return
    if role == "buyer" and buyer_id == user_id:
        return
    raise HTTPException(status_code=403, detail="Access denied to this order")


def _map_pricing_error(exc: Exception) -> HTTPException:
    if isinstance(exc, PricingNotFound):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, PricingInvalid):
        # validation-engine returns 422 for invalid pricing config; proxy as 422
        detail = str(exc)
        # keep JSON detail shape if possible
        return HTTPException(status_code=422, detail=detail)
    if isinstance(exc, PricingUnavailable):
        return HTTPException(status_code=503, detail=str(exc))
    return HTTPException(status_code=502, detail=str(exc))


@router.get(
    "/orders/{order_id}/pricing",
    dependencies=[Depends(get_current_user)],
)
async def get_order_pricing(request: Request, order_id: str) -> JSONResponse:
    """Query pricing for an order — proxied to validation-engine GET /orders/{id}/pricing."""
    user = request.state.user  # set by JWT middleware
    order_data = await _get_order_or_404(order_id)
    order = order_data.get("order") if isinstance(order_data.get("order"), dict) else {}
    if isinstance(order, dict) and order:
        _check_order_access(order, user)
    try:
        data = await pricing_client.query_pricing(order_id, headers=_fwd_headers(request))
    except (PricingNotFound, PricingInvalid, PricingUnavailable) as exc:
        raise _map_pricing_error(exc) from exc
    return JSONResponse(status_code=200, content=data)


@router.post(
    "/orders/{order_id}/pricing",
    dependencies=[Depends(get_current_user), Depends(require_role("seller"))],
)
async def trigger_order_pricing(request: Request, order_id: str) -> JSONResponse:
    """Trigger pricing for an order — proxied to validation-engine POST /orders/{id}/pricing."""
    user = request.state.user
    order_data = await _get_order_or_404(order_id)
    order = order_data.get("order") if isinstance(order_data.get("order"), dict) else {}
    if isinstance(order, dict) and order:
        # only seller owner may trigger
        if str(order.get("seller_id") or "") != user["user_id"] and user["role"] != "sahayak":
            raise HTTPException(status_code=403, detail="Only the order owner can trigger pricing")
    try:
        data = await pricing_client.trigger_pricing(order_id, headers=_fwd_headers(request))
    except (PricingNotFound, PricingInvalid, PricingUnavailable) as exc:
        raise _map_pricing_error(exc) from exc
    return JSONResponse(status_code=200, content=data)


@router.post(
    "/pricing/calculate",
    dependencies=[Depends(get_current_user)],
)
async def calculate_pricing(request: Request) -> JSONResponse:
    """Ad-hoc quote — proxies body verbatim to pricing-engine POST /pricing."""
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from None
    if not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")
    try:
        data = await pricing_client.calculate(payload, headers=_fwd_headers(request))
    except (PricingNotFound, PricingInvalid, PricingUnavailable) as exc:
        raise _map_pricing_error(exc) from exc
    return JSONResponse(status_code=200, content=data)
