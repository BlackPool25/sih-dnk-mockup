"""Document-pack generation routes.

POST /orders/{order_id}/generate-docs — generate CI, PL, CN, and PBE
documents from order data and persist as a DocPack row.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select

from app.models.doc_pack import DocPack
from app.models.order import Order, OrderStatus
from app.services.doc_generator import (
    generate_ci,
    generate_cn,
    generate_pbe,
    generate_pl,
)
from auth.deps import get_current_user, require_role
from storage.config import settings
from storage.crypto import DecryptionError, decrypt_field
from storage.db import get_session

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/orders/{order_id}", tags=["docs"])

_KEY_VERSION = 1


def _master_key() -> bytes:
    return bytes.fromhex(settings.ENCRYPTION_MASTER_KEY)


def _try_decrypt(encrypted_value: dict | None, user_uuid: str) -> str:
    """Safely decrypt an encrypted JSONB field, returning empty string on failure."""
    if encrypted_value is None:
        return ""
    try:
        return decrypt_field(encrypted_value, user_uuid, _master_key())
    except (DecryptionError, Exception):  # noqa: BLE001
        return ""


def _build_order_data(order: Order, user_id: str) -> dict:
    """Extract and decrypt order fields into a dict for the doc generators."""
    return {
        "id": str(order.id),
        "exporter_name": order.exporter_name,
        "exporter_address": order.exporter_address,
        "iec": order.iec,
        "consignee": order.consignee,
        "destination_country": order.destination_country,
        "currency": order.currency,
        "value_minor": order.value_minor,
        "net_weight_g": order.net_weight_g,
        "gross_weight_g": order.gross_weight_g,
        "line_items": order.line_items,
        "bank_name": order.bank_name,
        "ifsc": order.ifsc,
        "bank_account": _try_decrypt(order.bank_account_encrypted, user_id),
        "ad_code": _try_decrypt(order.ad_code_encrypted, user_id),
        "state_code": order.state_code,
        "article_id": order.article_id,
    }


# ---------------------------------------------------------------------------
# POST /orders/{order_id}/generate-docs
# ---------------------------------------------------------------------------


@router.post(
    "/generate-docs",
    status_code=201,
    dependencies=[Depends(get_current_user), Depends(require_role("seller"))],
)
async def generate_docs(
    request: Request,
    order_id: str,
) -> dict:
    """Generate all four export documents for an order and persist as a DocPack.

    Requires seller authentication.  Only the order's owner may generate docs.
    Documents are stored as JSONB — no PDF rendering is performed here.
    """
    user = request.state.user
    user_id: str = str(user["user_id"])

    # Parse and fetch order
    try:
        oid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid order ID")

    async with get_session()() as session:
        result = await session.execute(select(Order).where(Order.id == oid))
        order = result.scalar_one_or_none()

    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    # Owner check — only the seller who created the order
    if str(order.seller_id) != user_id:
        raise HTTPException(status_code=403, detail="Only the order owner can generate documents")

    # Prevent duplicate generation
    if order.doc_pack_id is not None:
        raise HTTPException(
            status_code=409,
            detail="Documents already generated for this order",
        )

    # Build order data with decrypted fields
    order_data = _build_order_data(order, user_id)

    # Generate all four documents
    ci_doc = generate_ci(order_data)
    pl_doc = generate_pl(order_data)
    cn_doc = generate_cn(order_data)
    pbe_doc = generate_pbe(order_data)

    # Persist DocPack row and update order status
    async with get_session()() as session:
        doc_pack = DocPack(
            order_id=order.id,
            ci_json=ci_doc,
            pl_json=pl_doc,
            cn_json=cn_doc,
            pbe_json=pbe_doc,
        )
        session.add(doc_pack)
        await session.flush()  # populate doc_pack.id

        # Update order
        order = await session.get(Order, order.id)
        order.status = OrderStatus.docs_generated
        order.doc_pack_id = doc_pack.id

        await session.commit()
        await session.refresh(doc_pack)

    return {
        "id": str(doc_pack.id),
        "order_id": str(doc_pack.order_id),
        "documents": {
            "commercial_invoice": ci_doc,
            "packing_list": pl_doc,
            "customs_declaration": cn_doc,
            "postal_bill_of_export": pbe_doc,
        },
        "generated_at": doc_pack.generated_at.isoformat(),
    }
