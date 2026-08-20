"""Tracking proxy — thin authenticated proxy over tracking-api.

POST /tracking/shipments                         — register (auth)
GET  /tracking/shipments/{tracking_number}       — get one
POST /tracking/shipments/{tracking_number}/events — add event
GET  /tracking/shipments/{tracking_number}/events — list events
GET  /tracking/orders/{order_id}/shipments       — list per order (via tracking-api)

Propagates Authorization/X-Request-Id, 1:1 status passthrough.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.services.tracking_client import (
    DuplicateError,
    InvalidInputError as TrackingInvalid,
)
from app.services.tracking_client import (
    NotFoundError as TrackingNotFound,
)
from app.services.tracking_client import (
    ServiceUnavailable as TrackingUnavailable,
)
from app.services.tracking_client import tracking_client
from auth.deps import get_current_user

router = APIRouter(prefix="/tracking", tags=["tracking"])


def _fwd_headers(request: Request) -> dict[str, str]:
    h: dict[str, str] = {}
    auth = request.headers.get("Authorization") or request.headers.get("authorization")
    if auth:
        h["Authorization"] = auth
    rid = request.headers.get("X-Request-Id") or request.headers.get("x-request-id") or request.headers.get("X-Request-ID")
    if rid:
        h["X-Request-Id"] = rid
    return h


def _map_error(exc: Exception) -> HTTPException:
    if isinstance(exc, TrackingNotFound):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, DuplicateError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, TrackingInvalid):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, TrackingUnavailable):
        return HTTPException(status_code=503, detail=str(exc))
    return HTTPException(status_code=502, detail=str(exc))


@router.post(
    "/shipments",
    dependencies=[Depends(get_current_user)],
)
async def register_shipment(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from None
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")
    tracking_number = body.get("tracking_number")
    carrier = body.get("carrier")
    if not isinstance(tracking_number, str) or not tracking_number.strip():
        raise HTTPException(status_code=422, detail="tracking_number is required")
    if not isinstance(carrier, str) or not carrier.strip():
        raise HTTPException(status_code=422, detail="carrier is required")
    order_id = body.get("order_id") if isinstance(body.get("order_id"), str) else None
    parcel_id = body.get("parcel_id") if isinstance(body.get("parcel_id"), str) else None
    try:
        data = await tracking_client.register_shipment(
            tracking_number.strip(), carrier.strip(), order_id=order_id, parcel_id=parcel_id, headers=_fwd_headers(request)
        )
    except (TrackingNotFound, DuplicateError, TrackingInvalid, TrackingUnavailable) as exc:
        raise _map_error(exc) from exc
    return JSONResponse(status_code=200, content=data)


@router.get(
    "/shipments/{tracking_number}",
    dependencies=[Depends(get_current_user)],
)
async def get_shipment(request: Request, tracking_number: str) -> JSONResponse:
    try:
        data = await tracking_client.get_shipment(tracking_number, headers=_fwd_headers(request))
    except (TrackingNotFound, TrackingInvalid, TrackingUnavailable, DuplicateError) as exc:
        raise _map_error(exc) from exc
    return JSONResponse(status_code=200, content=data)


@router.post(
    "/shipments/{tracking_number}/events",
    dependencies=[Depends(get_current_user)],
)
async def add_event(request: Request, tracking_number: str) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from None
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")
    status_val = body.get("status")
    if not isinstance(status_val, str) or not status_val.strip():
        raise HTTPException(status_code=422, detail="status is required")
    location = body.get("location") if isinstance(body.get("location"), str) else None
    try:
        data = await tracking_client.add_event(
            tracking_number, status_val.strip(), location=location, headers=_fwd_headers(request)
        )
    except (TrackingNotFound, TrackingInvalid, TrackingUnavailable, DuplicateError) as exc:
        raise _map_error(exc) from exc
    return JSONResponse(status_code=200, content=data)


@router.get(
    "/shipments/{tracking_number}/events",
    dependencies=[Depends(get_current_user)],
)
async def get_events(request: Request, tracking_number: str) -> JSONResponse:
    try:
        data = await tracking_client.get_events(tracking_number, headers=_fwd_headers(request))
    except (TrackingNotFound, TrackingInvalid, TrackingUnavailable, DuplicateError) as exc:
        raise _map_error(exc) from exc
    return JSONResponse(status_code=200, content=data)


@router.get(
    "/orders/{order_id}/shipments",
    dependencies=[Depends(get_current_user)],
)
async def list_order_shipments(request: Request, order_id: str) -> JSONResponse:
    try:
        data = await tracking_client.list_order_shipments(order_id, headers=_fwd_headers(request))
    except (TrackingNotFound, TrackingInvalid, TrackingUnavailable, DuplicateError) as exc:
        raise _map_error(exc) from exc
    # normalize to {shipments: [...] } if list, else pass through
    if isinstance(data, list):
        return JSONResponse(status_code=200, content={"shipments": data, "order_id": order_id})
    if isinstance(data, dict):
        return JSONResponse(status_code=200, content=data)
    return JSONResponse(status_code=200, content={"shipments": data})
