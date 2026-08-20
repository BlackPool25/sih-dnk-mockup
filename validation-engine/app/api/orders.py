"""Order API — list/fetch orders, per-order documents, and QR-token binding."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from app.db import SessionLocal
from app.models.documents import Document
from app.models.order import Order, OrderStatus

router = APIRouter(prefix="/orders", tags=["orders"])


def _order_dict(order: Order) -> dict:
    return {
        "id": str(order.id),
        "seller_id": str(order.seller_id) if order.seller_id else None,
        "buyer_id": str(order.buyer_id) if order.buyer_id else None,
        "status": order.status.value if order.status else None,
        "validation_state": order.validation_state.value if order.validation_state else None,
        "destination_country": order.destination_country,
        "value_minor": order.value_minor,
        "currency": order.currency,
        "consignee": order.consignee,
        "net_weight_g": order.net_weight_g,
        "gross_weight_g": order.gross_weight_g,
        "article_id": order.article_id,
        "iec": order.iec,
        "gstin": order.gstin,
        "ad_code": order.ad_code,
        "bank_account": order.bank_account,
        "bank_name": order.bank_name,
        "ifsc": order.ifsc,
        "quote_id": order.quote_id,
        "exporter_name": order.exporter_name,
        "exporter_address": order.exporter_address,
        "state_code": order.state_code,
        "version": order.version,
        "last_report": order.last_report,
        "qr_token_jti": order.qr_token_jti,
        "pricing_breakdown": order.pricing_breakdown,
        "parcels": order.parcels,
        "qr_tokens": order.qr_tokens,
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
    }


def _document_dict(doc: Document) -> dict:
    return {
        "doc_type": doc.doc_type,
        "version": doc.version,
        "checksum": doc.checksum,
        "pdf_url": doc.file_path,
        "parcel_id": doc.parcel_id,
        "generated_at": doc.created_at.isoformat() if doc.created_at else None,
    }


def _parse_uuid(raw: str, field: str) -> uuid.UUID:
    try:
        return uuid.UUID(raw)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"invalid {field} {raw!r}") from None


class QrTokenPayload(BaseModel):
    jti: str
    parcel_id: str | None = None
    exp: str | None = None


class PaidHeldRequest(BaseModel):
    payment_id: str | None = None
    payment_link_id: str | None = None
    event: str | None = None
    event_id: str | None = None
    amount: int | None = None
    currency: str | None = None


class OrderStatusPatchRequest(BaseModel):
    status: str
    payment_id: str | None = None
    payment_link_id: str | None = None
    event: str | None = None
    event_id: str | None = None


# Allowed pre-states that may transition to paid_held.
_PAID_HELD_SOURCES: frozenset[OrderStatus] = frozenset(
    {OrderStatus.quote_accepted, OrderStatus.confirmed}
)

# States at or beyond paid_held — idempotent, no downgrade.
_POST_PAID_STATUSES: frozenset[OrderStatus] = frozenset(
    {
        OrderStatus.paid_held,
        OrderStatus.in_transit,
        OrderStatus.delivered,
        OrderStatus.disputed,
        OrderStatus.settled,
        OrderStatus.refunded,
    }
)


def _apply_paid_held(
    order: Order,
    *,
    payment_id: str | None,
    payment_link_id: str | None,
    event: str | None,
    event_id: str | None,
) -> tuple[bool, dict[str, object]]:
    """Idempotent transition to paid_held; returns (changed, payment_meta).

    Idempotency key is (payment_id, payment_link_id). Stored in
    ``last_report.payment`` for deduplication. If already paid_held with
    same key, returns not-changed.
    """
    existing_payment: dict[str, object] = {}
    if isinstance(order.last_report, dict):
        maybe = order.last_report.get("payment")
        if isinstance(maybe, dict):
            existing_payment = dict(maybe)

    incoming_key = f"{payment_id or ''}|{payment_link_id or ''}"
    existing_key = f"{existing_payment.get('payment_id') or ''}|{existing_payment.get('payment_link_id') or ''}"

    # Already beyond paid_held or already paid_held — idempotent.
    if order.status in _POST_PAID_STATUSES:
        if incoming_key and existing_key and incoming_key == existing_key:
            return False, existing_payment
        if order.status == OrderStatus.paid_held and not existing_key and incoming_key:
            # First payment metadata for already-paid order — store it without status change.
            pass
        elif order.status != OrderStatus.paid_held:
            # In_transit etc — never downgrade.
            return False, existing_payment

    # Validate source state.
    if order.status not in _PAID_HELD_SOURCES and order.status not in _POST_PAID_STATUSES:
        raise HTTPException(
            status_code=409,
            detail=f"cannot transition from {order.status.value!r} to 'paid_held'",
        )

    # If already paid_held with same key, idempotent no-op.
    if order.status == OrderStatus.paid_held and incoming_key and existing_key and incoming_key == existing_key:
        return False, existing_payment

    payment_meta: dict[str, object] = {
        "payment_id": payment_id,
        "payment_link_id": payment_link_id,
        "event": event,
        "event_id": event_id,
        "money_location": "RAZORPAY_MERCHANT_BALANCE",
        "paid_at": datetime.now(timezone.utc).isoformat(),
    }
    # Prune Nones for clean JSON.
    payment_meta = {k: v for k, v in payment_meta.items() if v is not None}

    # Merge into last_report.
    last = dict(order.last_report) if isinstance(order.last_report, dict) else {}
    last["payment"] = payment_meta
    # Also store top-level idempotency keys for quick lookup.
    if payment_id:
        last["payment_id"] = payment_id
    if payment_link_id:
        last["payment_link_id"] = payment_link_id
    order.last_report = last
    order.status = OrderStatus.paid_held
    order.version = (order.version or 0) + 1
    return True, payment_meta


@router.get("")
def list_orders(
    seller_id: str | None = None,
    buyer_id: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    filters = []
    if seller_id is not None:
        filters.append(Order.seller_id == _parse_uuid(seller_id, "seller_id"))
    if buyer_id is not None:
        filters.append(Order.buyer_id == _parse_uuid(buyer_id, "buyer_id"))
    if status is not None:
        try:
            filters.append(Order.status == OrderStatus(status))
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"invalid status {status!r} — expected one of {[s.value for s in OrderStatus]}",
            ) from None
    with SessionLocal() as session:
        total = session.scalar(select(func.count()).select_from(Order).where(*filters)) or 0
        orders = session.scalars(
            select(Order).where(*filters).order_by(Order.created_at.desc()).limit(limit).offset(offset)
        ).all()
        return {"orders": [_order_dict(o) for o in orders], "total": total, "limit": limit, "offset": offset}


@router.get("/{order_id}")
def get_order(order_id: str) -> dict:
    with SessionLocal() as session:
        order = session.execute(
            select(Order).where(Order.id == uuid.UUID(order_id)).options(selectinload(Order.line_items))
        ).scalar_one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail=f"order {order_id!r} not found")
        return {
            "order": _order_dict(order),
            "last_report": order.last_report,
            "line_items": [
                {
                    "id": li.id,
                    "category_slug": li.category_slug,
                    "quantity": li.quantity,
                    "weight_g": li.weight_g,
                    "hs_code": li.hs_code,
                    "value_minor": li.value_minor,
                    "dimensions": li.dimensions,
                    "prohibited_flags": li.prohibited_flags,
                }
                for li in order.line_items
            ],
        }


@router.get("/{order_id}/pricing")
def get_pricing(order_id: str) -> dict:
    with SessionLocal() as session:
        order = session.execute(select(Order).where(Order.id == uuid.UUID(order_id))).scalar_one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail=f"order {order_id!r} not found")
        if order.pricing_breakdown is None:
            raise HTTPException(status_code=404, detail=f"no pricing for order {order_id!r}")
        pb = order.pricing_breakdown
        return {
            "order_id": order_id,
            "pricing_breakdown": pb,
            "parcels": order.parcels or pb.get("parcels", []),
            "lane_breakdown": pb.get("lane_breakdown"),
            "cost": pb.get("cost"),
            "landed_cost": pb.get("landed_cost"),
        }


@router.get("/{order_id}/documents")
def list_order_documents(order_id: str, parcel_id: str | None = Query(None)) -> dict:
    order_uuid = uuid.UUID(order_id)
    order_id_col = getattr(Document, "order_id", None)
    with SessionLocal() as session:
        if order_id_col is None:
            documents: list[Document] = []
        else:
            stmt = select(Document).where(order_id_col == order_uuid)
            if parcel_id is not None:
                stmt = stmt.where(Document.parcel_id == parcel_id)
            stmt = stmt.order_by(Document.version.desc(), Document.id.desc())
            documents = session.scalars(stmt).all()
        return {"order_id": order_id, "documents": [_document_dict(d) for d in documents]}


@router.get("/{order_id}/pdf")
def order_pdf(
    order_id: str, doc_type: str = Query("INVOICE"), parcel_id: str | None = Query(None)
) -> FileResponse:
    order_uuid = uuid.UUID(order_id)
    order_id_col = getattr(Document, "order_id", None)
    with SessionLocal() as session:
        if order_id_col is None:
            raise HTTPException(status_code=404, detail=f"no {doc_type!r} document for order {order_id!r}")
        stmt = select(Document).where(order_id_col == order_uuid, Document.doc_type == doc_type)
        if parcel_id is not None:
            stmt = stmt.where(Document.parcel_id == parcel_id)
        stmt = stmt.order_by(Document.version.desc(), Document.id.desc()).limit(1)
        doc = session.scalar(stmt)
        if doc is None or not Path(doc.file_path).is_file():
            raise HTTPException(status_code=404, detail=f"no {doc_type!r} document for order {order_id!r}")
        return FileResponse(doc.file_path, media_type="application/pdf")


@router.post("/{order_id}/qr-token")
def set_qr_token(order_id: str, payload: QrTokenPayload) -> dict:
    with SessionLocal.begin() as session:
        order = session.execute(select(Order).where(Order.id == uuid.UUID(order_id))).scalar_one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail=f"order {order_id!r} not found")
        parcel_id = payload.parcel_id or (order.parcels[0]["parcel_id"] if order.parcels else None) or "parcel-1"
        if payload.exp:
            exp_val = payload.exp
        else:
            exp_val = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        entry = {"parcel_id": parcel_id, "jti": payload.jti, "exp": exp_val}
        existing = list(order.qr_tokens or [])
        found = False
        for idx, tok in enumerate(existing):
            if isinstance(tok, dict) and tok.get("parcel_id") == parcel_id:
                existing[idx] = entry
                found = True
                break
        if not found:
            existing.append(entry)
        order.qr_tokens = existing
        order.qr_token_jti = payload.jti
    return {"order_id": order_id, "qr_token_jti": payload.jti, "qr_tokens": existing, "parcel_id": parcel_id}


@router.post("/{order_id}/paid_held")
def mark_paid_held(order_id: str, payload: PaidHeldRequest) -> dict:
    try:
        oid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"invalid order_id {order_id!r}") from None
    with SessionLocal.begin() as session:
        order = session.execute(select(Order).where(Order.id == oid).with_for_update()).scalar_one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail=f"order {order_id!r} not found")
        changed, meta = _apply_paid_held(
            order,
            payment_id=payload.payment_id,
            payment_link_id=payload.payment_link_id,
            event=payload.event,
            event_id=payload.event_id,
        )
        session.flush()
        return {
            "order_id": order_id,
            "status": order.status.value,
            "changed": changed,
            "payment": meta,
            "order": _order_dict(order),
        }


@router.patch("/{order_id}/status")
def patch_order_status(order_id: str, payload: OrderStatusPatchRequest) -> dict:
    target = payload.status.strip()
    try:
        desired = OrderStatus(target)
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail=f"invalid status {target!r} — expected one of {[s.value for s in OrderStatus]}",
        ) from None
    if desired != OrderStatus.paid_held:
        raise HTTPException(status_code=422, detail="only transition to 'paid_held' is supported via this endpoint")
    try:
        oid = uuid.UUID(order_id)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"invalid order_id {order_id!r}") from None
    with SessionLocal.begin() as session:
        order = session.execute(select(Order).where(Order.id == oid).with_for_update()).scalar_one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail=f"order {order_id!r} not found")
        changed, meta = _apply_paid_held(
            order,
            payment_id=payload.payment_id,
            payment_link_id=payload.payment_link_id,
            event=payload.event,
            event_id=payload.event_id,
        )
        session.flush()
        return {
            "order_id": order_id,
            "status": order.status.value,
            "changed": changed,
            "payment": meta,
            "order": _order_dict(order),
        }


__all__ = ["router"]
