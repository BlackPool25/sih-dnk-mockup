"""Order routes — thin authenticated proxy over the validation-engine orders API.

POST  /orders               — create order (seller; profile auto-fill, proxied)
GET   /orders               — list orders (role-scoped, proxied)
GET   /orders/{id}          — get single order (access-controlled, proxied)
GET   /orders/{id}/pdf      — stream the INVOICE PDF (auto-generates docs first)

backend-core NEVER validates — it builds the payload from the seller profile,
proxies it to validation-engine, and maps the engine's response back.  The
unified orders table and all validation logic live in validation-engine.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncIterator

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy import select

from app.models.profile import SellerProfile
from app.schemas.order import (
    OrderCreateRequest,
    OrderListResponse,
    OrderResponse,
)
from app.services.translation import ensure_english_free_text
from app.services.val_client import (
    InvalidInputError,
    NotFoundError,
    ServiceUnavailable,
    val_client,
)
from auth.deps import get_current_user, require_role
from storage.crypto import DecryptionError, decrypt_field
from storage.db import get_session

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/orders", tags=["orders"])

_DEFAULT_LIMIT = 50

# Indian state name → 2-char ISO 3166-2 subdiv code (used for PBE state_code).
_STATE_CODES: dict[str, str] = {
    "Maharashtra": "MH",
    "Karnataka": "KA",
    "Tamil Nadu": "TN",
    "Uttar Pradesh": "UP",
    "Delhi": "DL",
    "Gujarat": "GJ",
    "Rajasthan": "RJ",
    "West Bengal": "WB",
    "Kerala": "KL",
    "Telangana": "TS",
    "Andhra Pradesh": "AP",
    "Madhya Pradesh": "MP",
    "Punjab": "PB",
    "Haryana": "HR",
    "Bihar": "BR",
    "Odisha": "OD",
    "Assam": "AS",
}

def _get_settings():
    """Lazily import settings so test patches apply."""
    from storage.config import settings as s

    return s


def _master_key() -> bytes:
    return bytes.fromhex(_get_settings().ENCRYPTION_MASTER_KEY)


# ---------------------------------------------------------------------------
# Helpers — profile-derived payload fields
# ---------------------------------------------------------------------------


def _build_exporter_address(profile: SellerProfile) -> str:
    """Combine address fields into a single exporter address string."""
    parts: list[str] = []
    for value in (
        profile.address_line1,
        profile.address_line2,
        profile.city,
        profile.state,
        profile.pincode,
    ):
        if value:
            parts.append(value)
    return ", ".join(parts)


def _derive_state_code(profile_state: str | None) -> str:
    """Map a full Indian state name to its 2-char code; '' when unknown."""
    if profile_state is None:
        return ""
    return _STATE_CODES.get(profile_state, "")


def _decrypt_or(encrypted_value: dict | None, user_uuid: str) -> str:
    """Decrypt an encrypted profile field; empty string on missing/DecryptionError."""
    if encrypted_value is None:
        return ""
    try:
        return decrypt_field(encrypted_value, user_uuid, _master_key())
    except DecryptionError:
        return ""


def _build_order_payload(profile: SellerProfile, user_id: str, body: OrderCreateRequest) -> dict[str, object]:
    """Assemble the validation-engine OrderPayload dict for a new order.

    Exporter identity is auto-filled from the seller profile (decrypted);
    ``gstin`` and ``state_code`` accept a request-body override.
    """
    return {
        "seller_id": user_id,
        "buyer_id": user_id,
        "destination_country": body.destination_country,
        "value_minor": body.value_minor,
        "currency": body.currency,
        "consignee": body.consignee,
        "net_weight_g": body.net_weight_g,
        "gross_weight_g": body.gross_weight_g,
        "article_id": body.article_id,
        "line_items": [item.model_dump() for item in body.line_items],
        "iec": profile.iec or "",
        "gstin": body.gstin or _decrypt_or(profile.gstin_encrypted, user_id),
        "ad_code": _decrypt_or(profile.ad_code_encrypted, user_id),
        "bank_account": _decrypt_or(profile.bank_account_encrypted, user_id),
        "bank_name": profile.bank_name or "",
        "ifsc": profile.ifsc or "",
        "exporter_name": profile.firm_name,
        "exporter_address": _build_exporter_address(profile),
        "state_code": body.state_code or _derive_state_code(profile.state),
    }


# ---------------------------------------------------------------------------
# Helpers — validation-engine call mapping
# ---------------------------------------------------------------------------


async def _fetch_seller_profile(user_id: str) -> SellerProfile | None:
    """Fetch the authenticated seller's SellerProfile row."""
    async with get_session()() as session:
        result = await session.execute(
            select(SellerProfile).where(SellerProfile.user_id == uuid.UUID(user_id)),
        )
        return result.scalar_one_or_none()


async def _get_order_or_404(order_id: str) -> dict[str, object]:
    """Call val_client.get_order, mapping engine exceptions to HTTP."""
    try:
        return await val_client.get_order(order_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail="Order not found") from exc
    except InvalidInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _split_order_data(data: dict[str, object]) -> tuple[dict[str, object], list[object]]:
    """Split a val_client.get_order response into (order_dict, line_items)."""
    order = data.get("order")
    line_items = data.get("line_items")
    order_dict = order if isinstance(order, dict) else {}
    items = line_items if isinstance(line_items, list) else []
    return order_dict, items


def _check_order_access(order: dict[str, object], user: dict[str, str]) -> None:
    """Raise 403 unless the user is the seller, the buyer, or a sahayak."""
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


def _coerce_order_entry(entry: object) -> tuple[dict[str, object], list[object]]:
    """Normalise one list-item entry into (order_dict, line_items).

    Accepts both the flat order dict and the ``{order, line_items}`` shape.
    """
    if not isinstance(entry, dict):
        return {}, []
    inner = entry.get("order")
    if isinstance(inner, dict):
        line_items = entry.get("line_items")
        return inner, line_items if isinstance(line_items, list) else []
    line_items = entry.get("line_items")
    return entry, line_items if isinstance(line_items, list) else []


def _build_order_response(order: dict[str, object], line_items: list[object]) -> dict[str, object]:
    """Map a validation-engine order dict + line items into OrderResponse fields."""
    return {
        "id": str(order.get("id") or ""),
        "seller_id": str(order["seller_id"]) if order.get("seller_id") else None,
        "buyer_id": str(order["buyer_id"]) if order.get("buyer_id") else None,
        "status": str(order.get("status") or ""),
        "validation_state": (
            str(order["validation_state"]) if order.get("validation_state") else None
        ),
        "destination_country": order.get("destination_country"),
        "value_minor": order.get("value_minor"),
        "currency": order.get("currency") or "INR",
        "consignee": order.get("consignee"),
        "net_weight_g": order.get("net_weight_g"),
        "gross_weight_g": order.get("gross_weight_g"),
        "article_id": order.get("article_id"),
        "iec": order.get("iec"),
        "gstin": order.get("gstin"),
        "ad_code": order.get("ad_code"),
        "bank_account": order.get("bank_account"),
        "bank_name": order.get("bank_name"),
        "ifsc": order.get("ifsc"),
        "quote_id": order.get("quote_id"),
        "exporter_name": order.get("exporter_name"),
        "exporter_address": order.get("exporter_address"),
        "state_code": order.get("state_code"),
        "qr_token_jti": order.get("qr_token_jti"),
        "version": order.get("version"),
        "line_items": line_items,
        "created_at": order.get("created_at"),
        "updated_at": order.get("updated_at"),
    }


# ---------------------------------------------------------------------------
# Helpers — PDF streaming (pattern mirrors app/routers/proxy.py)
# ---------------------------------------------------------------------------


async def _iter_response_bytes(resp: httpx.Response) -> AsyncIterator[bytes]:
    """Yield the buffered response body in chunks."""
    async for chunk in resp.aiter_bytes():
        yield chunk


async def _stream_order_pdf(order_id: str) -> StreamingResponse:
    """Stream the INVOICE PDF from validation-engine as a StreamingResponse."""
    base = _get_settings().VALIDATION_ENGINE_URL.rstrip("/")
    url = f"{base}/orders/{order_id}/pdf"
    timeout = httpx.Timeout(60.0, connect=10.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            resp = await client.get(url, params={"doc_type": "INVOICE"})
        except httpx.ConnectError as exc:
            raise HTTPException(
                status_code=503, detail="validation-engine is currently unavailable"
            ) from exc
        except httpx.TimeoutException as exc:
            raise HTTPException(status_code=504, detail="validation-engine timed out") from exc

    if resp.status_code != 200:
        raise HTTPException(
            status_code=502,
            detail=f"validation-engine could not render the PDF (status {resp.status_code})",
        )

    return StreamingResponse(
        _iter_response_bytes(resp),
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="invoice-{order_id}.pdf"'},
    )


# ---------------------------------------------------------------------------
# POST /orders — Create (proxy)
# ---------------------------------------------------------------------------


@router.post(
    "",
    status_code=201,
    response_model=OrderResponse,
    dependencies=[Depends(get_current_user), Depends(require_role("seller"))],
)
async def create_order(
    request: Request,
    body: OrderCreateRequest,
) -> dict[str, object]:
    """Create a new trade order in validation-engine with profile auto-fill."""
    user = request.state.user
    user_id: str = str(user["user_id"])

    profile = await _fetch_seller_profile(user_id)
    if profile is None:
        raise HTTPException(status_code=400, detail="Complete profile first")

    # English invariant: every free-text value reaching the validation engine
    # must be Latin-script. Session state keeps the Hindi-canonical value; the
    # Latin form is derived here, at the boundary. Never blocks on failure —
    # ensure_english_free_text falls back to the raw value.
    english = await ensure_english_free_text([("consignee", body.consignee)])
    body = body.model_copy(update={"consignee": english["consignee"]})

    payload = _build_order_payload(profile, user_id, body)
    try:
        report = await val_client.create_order(payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    order_id = str(report.get("order_id") or "")
    if not order_id:
        raise HTTPException(
            status_code=502, detail="validation-engine did not return an order_id"
        )

    order_data = await _get_order_or_404(order_id)
    order, line_items = _split_order_data(order_data)
    response = _build_order_response(order, line_items)
    response["validation_report"] = report
    return response


# ---------------------------------------------------------------------------
# GET /orders — List (proxy, role-scoped)
# ---------------------------------------------------------------------------


@router.get(
    "",
    response_model=OrderListResponse,
    dependencies=[Depends(get_current_user)],
)
async def list_orders(
    request: Request,
    status: str | None = Query(None, description="Filter by order status"),
    limit: int = Query(_DEFAULT_LIMIT, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict[str, object]:
    """List orders scoped to the current user's role.

    - **seller**:  sees orders where they are the seller
    - **buyer**:   sees orders where they are the buyer
    - **sahayak**: sees ALL orders
    """
    user = request.state.user
    user_id: str = str(user["user_id"])
    role: str = str(user["role"])

    seller_id = user_id if role == "seller" else None
    buyer_id = user_id if role == "buyer" else None

    try:
        data = await val_client.list_orders(
            seller_id=seller_id,
            buyer_id=buyer_id,
            status=status,
            limit=limit,
            offset=offset,
        )
    except InvalidInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    raw_orders = data.get("orders", [])
    entries = raw_orders if isinstance(raw_orders, list) else []

    orders: list[dict[str, object]] = []
    for entry in entries:
        order_dict, line_items = _coerce_order_entry(entry)
        if order_dict:
            orders.append(_build_order_response(order_dict, line_items))

    raw_total = data.get("total", len(orders))
    total = raw_total if isinstance(raw_total, int) else len(orders)

    return {
        "orders": orders,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ---------------------------------------------------------------------------
# GET /orders/{order_id} — Get one (proxy)
# ---------------------------------------------------------------------------


@router.get(
    "/{order_id}",
    response_model=OrderResponse,
    dependencies=[Depends(get_current_user)],
)
async def get_order(
    request: Request,
    order_id: str,
) -> dict[str, object]:
    """Get a single order by ID — seller owner, buyer, or sahayak may view."""
    user = request.state.user

    order_data = await _get_order_or_404(order_id)
    order, _line_items = _split_order_data(order_data)
    _check_order_access(order, user)

    return _build_order_response(order, _line_items)


# ---------------------------------------------------------------------------
# GET /orders/{order_id}/pdf — Stream INVOICE PDF (proxy)
# ---------------------------------------------------------------------------


@router.get(
    "/{order_id}/pdf",
    dependencies=[Depends(get_current_user)],
)
async def get_order_pdf(
    request: Request,
    order_id: str,
) -> StreamingResponse:
    """Stream the INVOICE PDF; auto-generates documents if none exist yet."""
    user = request.state.user

    order_data = await _get_order_or_404(order_id)
    order, _line_items = _split_order_data(order_data)
    _check_order_access(order, user)

    try:
        docs = await val_client.get_order_documents(order_id)
    except ServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    existing = docs.get("documents", [])
    if not (isinstance(existing, list) and existing):
        try:
            await val_client.generate_docs_all(order_id)
        except NotFoundError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        except InvalidInputError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc
        except ServiceUnavailable as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc

    return await _stream_order_pdf(order_id)
