"""Payments proxy — thin proxy over pricing-engine /payment/* (Razorpay sandbox).

POST /payments/order              — create Razorpay order (auth, amount guard)
POST /payments/link               — create payment link (auth, amount guard)
GET  /payments/link/{id}         — link status (auth)
POST /payments/verify             — HMAC verify (auth)
POST /payments/webhook            — Razorpay webhook (NO auth, signature verified downstream)

Amount guard: if order_id/reference with an order, load order via validation-engine
and ignore client amount when it mismatches (server truth wins). Razorpay secrets
stay server-side in pricing-engine.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from app.services.payment_client import (
    InvalidInputError as PayInvalid,
)
from app.services.payment_client import (
    NotFoundError as PayNotFound,
)
from app.services.payment_client import (
    ServiceUnavailable as PayUnavailable,
)
from app.services.payment_client import payment_client
from app.services.val_client import val_client
from auth.deps import get_current_user

router = APIRouter(prefix="/payments", tags=["payments"])


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
    if isinstance(exc, PayNotFound):
        return HTTPException(status_code=404, detail=str(exc))
    if isinstance(exc, PayInvalid):
        return HTTPException(status_code=422, detail=str(exc))
    if isinstance(exc, PayUnavailable):
        return HTTPException(status_code=503, detail=str(exc))
    return HTTPException(status_code=502, detail=str(exc))


async def _guard_amount(order_id: str | None, client_amount: int | None) -> int | None:
    """If order_id given, load order and return server-side value_minor when mismatched.

    Returns the guarded amount if an order is found, else the original client_amount.
    """
    if not order_id or client_amount is None:
        return client_amount
    try:
        data = await val_client.get_order(order_id)
    except Exception:
        return client_amount
    order = data.get("order") if isinstance(data.get("order"), dict) else {}
    if not isinstance(order, dict):
        return client_amount
    server_minor = order.get("value_minor")
    if isinstance(server_minor, int) and server_minor != client_amount:
        return server_minor
    return client_amount


@router.post(
    "/order",
    dependencies=[Depends(get_current_user)],
)
async def create_payment_order(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from None
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")

    amount = body.get("amount_minor")
    currency = body.get("currency")
    receipt = body.get("receipt")
    notes = body.get("notes") if isinstance(body.get("notes"), dict) else {}
    order_id = body.get("order_id") if isinstance(body.get("order_id"), str) else None

    if not isinstance(amount, int) or amount <= 0:
        raise HTTPException(status_code=422, detail="amount_minor must be a positive int")
    if not isinstance(currency, str) or len(currency.strip()) != 3:
        raise HTTPException(status_code=422, detail="currency must be 3-letter code")
    if not isinstance(receipt, str) or not receipt.strip():
        raise HTTPException(status_code=422, detail="receipt is required")

    guarded = await _guard_amount(order_id, amount)
    if guarded is not None:
        amount = guarded

    try:
        data = await payment_client.create_order(
            amount_minor=amount, currency=currency.strip().upper(), receipt=receipt.strip(), notes=notes, headers=_fwd_headers(request)
        )
    except (PayNotFound, PayInvalid, PayUnavailable) as exc:
        raise _map_error(exc) from exc
    return JSONResponse(status_code=201, content=data)


@router.post(
    "/link",
    dependencies=[Depends(get_current_user)],
)
async def create_payment_link(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from None
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")

    amount = body.get("amount_minor")
    currency = body.get("currency")
    reference_id = body.get("reference_id")
    description = body.get("description")
    notes = body.get("notes") if isinstance(body.get("notes"), dict) else {}
    customer = body.get("customer") if isinstance(body.get("customer"), dict) else None
    order_id = body.get("order_id") if isinstance(body.get("order_id"), str) else None
    # also allow reference_id to be order_id for guard
    guard_id = order_id or (reference_id if isinstance(reference_id, str) else None)

    if not isinstance(amount, int) or amount <= 0:
        raise HTTPException(status_code=422, detail="amount_minor must be a positive int")
    if not isinstance(currency, str) or len(currency.strip()) != 3:
        raise HTTPException(status_code=422, detail="currency must be 3-letter code")
    if not isinstance(reference_id, str) or not reference_id.strip():
        raise HTTPException(status_code=422, detail="reference_id is required")
    if not isinstance(description, str) or not description.strip():
        raise HTTPException(status_code=422, detail="description is required")

    guarded = await _guard_amount(guard_id, amount)
    if guarded is not None:
        amount = guarded

    try:
        data = await payment_client.create_link(
            amount_minor=amount,
            currency=currency.strip().upper(),
            reference_id=reference_id.strip(),
            description=description.strip(),
            customer=customer,
            notes=notes,
            headers=_fwd_headers(request),
        )
    except (PayNotFound, PayInvalid, PayUnavailable) as exc:
        raise _map_error(exc) from exc
    return JSONResponse(status_code=201, content=data)


@router.get(
    "/link/{payment_link_id}",
    dependencies=[Depends(get_current_user)],
)
async def get_link_status(request: Request, payment_link_id: str) -> JSONResponse:
    try:
        data = await payment_client.get_link_status(payment_link_id, headers=_fwd_headers(request))
    except (PayNotFound, PayInvalid, PayUnavailable) as exc:
        raise _map_error(exc) from exc
    return JSONResponse(status_code=200, content=data)


@router.post(
    "/verify",
    dependencies=[Depends(get_current_user)],
)
async def verify_payment(request: Request) -> JSONResponse:
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from None
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Body must be a JSON object")
    for f in ("razorpay_order_id", "razorpay_payment_id", "razorpay_signature"):
        if not isinstance(body.get(f), str) or not str(body.get(f)).strip():
            raise HTTPException(status_code=422, detail=f"{f} is required")
    try:
        data = await payment_client.verify_payment(
            razorpay_order_id=str(body["razorpay_order_id"]).strip(),
            razorpay_payment_id=str(body["razorpay_payment_id"]).strip(),
            razorpay_signature=str(body["razorpay_signature"]).strip(),
            headers=_fwd_headers(request),
        )
    except (PayNotFound, PayInvalid, PayUnavailable) as exc:
        raise _map_error(exc) from exc
    return JSONResponse(status_code=200, content=data)


@router.post("/webhook")
async def webhook(request: Request) -> JSONResponse:
    """Proxy Razorpay webhook — no auth, but signature is verified downstream."""
    signature = request.headers.get("X-Razorpay-Signature") or request.headers.get("x-razorpay-signature") or ""
    event_id = request.headers.get("x-razorpay-event-id") or request.headers.get("X-Razorpay-Event-Id")
    raw = await request.body()
    # allow empty body → let downstream decide
    try:
        data = await payment_client.proxy_webhook(raw, signature, event_id=event_id, headers=_fwd_headers(request))
    except (PayNotFound, PayInvalid, PayUnavailable) as exc:
        raise _map_error(exc) from exc
    return JSONResponse(status_code=200, content=data)
