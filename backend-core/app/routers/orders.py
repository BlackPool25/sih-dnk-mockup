"""Order routes — create, list, and retrieve trade orders with profile auto-fill.

POST  /orders          — create order (seller, auto-fills from profile)
GET   /orders          — list orders (role-scoped)
GET   /orders/{id}     — get single order (access-controlled, decrypted for seller)
"""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select

from app.models.order import Order, OrderStatus
from app.models.profile import SellerProfile
from app.schemas.order import (
    OrderCreateRequest,
    OrderListResponse,
    OrderResponse,
)
from auth.deps import get_current_user, require_role
from storage.crypto import DecryptionError, decrypt_field, encrypt_field
from storage.db import get_session

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/orders", tags=["orders"])

_KEY_VERSION = 1
_DEFAULT_LIMIT = 50


def _get_settings():
    """Lazily import settings so test patches apply."""
    from storage.config import settings as s

    return s


def _master_key() -> bytes:
    return bytes.fromhex(_get_settings().ENCRYPTION_MASTER_KEY)


# ---------------------------------------------------------------------------
# Helpers — profile snapshot
# ---------------------------------------------------------------------------


def _build_profile_snapshot(profile: SellerProfile) -> dict:
    """Build a plain dict from a SellerProfile for snapshotting.

    Encrypted fields (pan_encrypted, bank_account_encrypted, ad_code_encrypted,
    gstin_encrypted) are included *as-is* — they remain encrypted in the snapshot.
    """
    return {
        "firm_name": profile.firm_name,
        "owner_name": profile.owner_name,
        "pan_encrypted": profile.pan_encrypted,
        "bank_name": profile.bank_name,
        "bank_account_encrypted": profile.bank_account_encrypted,
        "ifsc": profile.ifsc,
        "bank_branch": profile.bank_branch,
        "iec": profile.iec,
        "ad_code_encrypted": profile.ad_code_encrypted,
        "gstin_encrypted": profile.gstin_encrypted,
        "address_line1": profile.address_line1,
        "address_line2": profile.address_line2,
        "city": profile.city,
        "state": profile.state,
        "pincode": profile.pincode,
        "phone": profile.phone,
        "is_verified": profile.is_verified,
    }


def _build_exporter_address(profile: SellerProfile) -> str:
    """Combine address fields into a single exporter address string."""
    parts: list[str] = []
    if profile.address_line1:
        parts.append(profile.address_line1)
    if profile.address_line2:
        parts.append(profile.address_line2)
    if profile.city:
        parts.append(profile.city)
    if profile.state:
        parts.append(profile.state)
    if profile.pincode:
        parts.append(profile.pincode)
    return ", ".join(parts)


# ---------------------------------------------------------------------------
# Helpers — response building
# ---------------------------------------------------------------------------


def _try_decrypt_field(encrypted_value: dict | None, user_uuid: str) -> str | None:
    """Safely decrypt an encrypted JSONB field, returning None on failure."""
    if encrypted_value is None:
        return None
    try:
        return decrypt_field(encrypted_value, user_uuid, _master_key())
    except DecryptionError:
        return None


def _build_order_response(order: Order, requesting_user_id: str) -> dict[str, object]:
    """Build a dict suitable for OrderResponse.

    Encrypted fields are decrypted only when *requesting_user_id* matches
    the seller — otherwise they are returned as None.
    """
    is_seller = str(order.seller_id) == requesting_user_id

    return {
        "id": str(order.id),
        "seller_id": str(order.seller_id),
        "buyer_id": str(order.buyer_id),
        "status": order.status.value,
        "profile_version": order.profile_version,
        "destination_country": order.destination_country,
        "value_minor": order.value_minor,
        "currency": order.currency,
        "consignee": order.consignee,
        "net_weight_g": order.net_weight_g,
        "gross_weight_g": order.gross_weight_g,
        "article_id": order.article_id,
        "iec": order.iec,
        "ad_code": (
            _try_decrypt_field(order.ad_code_encrypted, requesting_user_id)
            if is_seller
            else None
        ),
        "bank_account": (
            _try_decrypt_field(order.bank_account_encrypted, requesting_user_id)
            if is_seller
            else None
        ),
        "bank_name": order.bank_name,
        "ifsc": order.ifsc,
        "exporter_name": order.exporter_name,
        "exporter_address": order.exporter_address,
        "state_code": order.state_code,
        "line_items": order.line_items,
        "doc_pack_id": str(order.doc_pack_id) if order.doc_pack_id else None,
        "qr_token_jti": order.qr_token_jti,
        "created_at": order.created_at.isoformat(),
        "updated_at": order.updated_at.isoformat(),
    }


# ---------------------------------------------------------------------------
# Access control helpers
# ---------------------------------------------------------------------------


def _check_order_access(order: Order, user: dict[str, str]) -> None:
    """Raise 403 unless the user is the seller, the buyer, or a sahayak."""
    user_id = user["user_id"]
    role = user["role"]

    if role == "sahayak":
        return
    if role == "seller" and str(order.seller_id) == user_id:
        return
    if role == "buyer" and str(order.buyer_id) == user_id:
        return

    raise HTTPException(status_code=403, detail="Access denied to this order")


# ---------------------------------------------------------------------------
# POST /orders — Create
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
    """Create a new trade order with profile auto-fill.

    Fetches the authenticated seller's profile and auto-fills IEC, AD code,
    bank details, exporter name/address, and state code.  The full profile
    is encrypted and stored as a snapshot for audit purposes.
    """
    user = request.state.user
    user_id: str = str(user["user_id"])

    # 1. Fetch profile -----------------------------------------------------
    async with get_session()() as session:
        result = await session.execute(
            select(SellerProfile).where(
                SellerProfile.user_id == uuid.UUID(user_id),
            ),
        )
        profile = result.scalar_one_or_none()

    if profile is None:
        raise HTTPException(status_code=400, detail="Complete profile first")

    # 2. Build and encrypt profile snapshot ----------------------------------
    snapshot = _build_profile_snapshot(profile)
    snapshot_json = json.dumps(snapshot, default=str)
    encrypted_snapshot = encrypt_field(
        snapshot_json,
        user_id,
        _master_key(),
        _KEY_VERSION,
    )

    # 3. Auto-fill order fields from profile ---------------------------------
    exporter_address = _build_exporter_address(profile)
    buyer_id = user_id  # seller creates order for themselves as the buyer

    # 4. Serialize line items to list of dicts -------------------------------
    line_items = [item.model_dump() for item in body.line_items]

    # 5. Create Order --------------------------------------------------------
    order = Order(
        seller_id=uuid.UUID(user_id),
        buyer_id=uuid.UUID(buyer_id),
        status=OrderStatus.created,
        profile_version=profile.profile_version,
        profile_snapshot_encrypted=encrypted_snapshot,
        destination_country=body.destination_country,
        value_minor=body.value_minor,
        currency=body.currency,
        consignee=body.consignee,
        net_weight_g=body.net_weight_g,
        gross_weight_g=body.gross_weight_g,
        article_id=body.article_id,
        iec=profile.iec or "",
        ad_code_encrypted=profile.ad_code_encrypted or {},
        bank_name=profile.bank_name or "",
        ifsc=profile.ifsc or "",
        bank_account_encrypted=profile.bank_account_encrypted or {},
        exporter_name=profile.firm_name,
        exporter_address=exporter_address,
        state_code=(profile.state or "")[:10],
        line_items=line_items,
    )

    async with get_session()() as session:
        session.add(order)
        await session.commit()
        await session.refresh(order)

    return _build_order_response(order, user_id)


# ---------------------------------------------------------------------------
# GET /orders — List
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

    - **seller**: sees orders where they are the seller
    - **buyer**:  sees orders where they are the buyer
    - **sahayak**: sees ALL orders
    """
    user = request.state.user
    user_id: str = str(user["user_id"])
    role: str = str(user["role"])

    query = select(Order)
    count_query = select(Order)

    # Role-based scoping
    if role == "seller":
        query = query.where(Order.seller_id == uuid.UUID(user_id))
        count_query = count_query.where(Order.seller_id == uuid.UUID(user_id))
    elif role == "buyer":
        query = query.where(Order.buyer_id == uuid.UUID(user_id))
        count_query = count_query.where(Order.buyer_id == uuid.UUID(user_id))

    # Optional status filter
    if status is not None:
        try:
            status_enum = OrderStatus(status)
            query = query.where(Order.status == status_enum)
            count_query = count_query.where(Order.status == status_enum)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid status value",
            )

    # Apply ordering and pagination
    query = query.order_by(Order.created_at.desc()).offset(offset).limit(limit)

    async with get_session()() as session:
        # Count
        count_result = await session.execute(count_query)
        total = len(count_result.scalars().all())

        # Fetch
        result = await session.execute(query)
        orders = result.scalars().all()

    return {
        "orders": [_build_order_response(o, user_id) for o in orders],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ---------------------------------------------------------------------------
# GET /orders/{order_id} — Get one
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
    """Get a single order by ID.

    Accessible to the seller, the buyer, or a sahayak.
    Encrypted fields are decrypted only when the requester is the seller.
    """
    user = request.state.user

    try:
        oid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID")

    async with get_session()() as session:
        result = await session.execute(select(Order).where(Order.id == oid))
        order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    _check_order_access(order, user)

    return _build_order_response(order, str(user["user_id"]))
