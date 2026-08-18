"""Order API — list/fetch orders, per-order documents, and QR-token binding.

- GET /orders — paginated list filtered by seller/buyer/status.
- GET /orders/{order_id} — one order with last_report + line_items.
- GET /orders/{order_id}/documents — Document rows for the order (version desc).
- GET /orders/{order_id}/pdf — latest rendered PDF for a doc_type (FileResponse).
- POST /orders/{order_id}/qr-token — idempotently set order.qr_token_jti.
"""

from __future__ import annotations

import uuid
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
    """Serialize one Order row for the list + single-order responses."""
    return {
        "id": str(order.id),
        "seller_id": str(order.seller_id) if order.seller_id else None,
        "buyer_id": str(order.buyer_id) if order.buyer_id else None,
        "status": order.status.value if order.status else None,
        "validation_state": order.validation_state.value
        if order.validation_state
        else None,
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
        "created_at": order.created_at.isoformat() if order.created_at else None,
        "updated_at": order.updated_at.isoformat() if order.updated_at else None,
    }


def _document_dict(doc: Document) -> dict:
    """Serialize one Document row for the per-order document responses."""
    return {
        "doc_type": doc.doc_type,
        "version": doc.version,
        "checksum": doc.checksum,
        "pdf_url": doc.file_path,
        "generated_at": doc.created_at.isoformat() if doc.created_at else None,
    }


def _parse_uuid(raw: str, field: str) -> uuid.UUID:
    """Parse a UUID query param — 400 when the caller passes a non-UUID."""
    try:
        return uuid.UUID(raw)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"invalid {field} {raw!r}") from None


class QrTokenPayload(BaseModel):
    """Body for POST /orders/{order_id}/qr-token."""

    jti: str


@router.get("")
def list_orders(
    seller_id: str | None = None,
    buyer_id: str | None = None,
    status: str | None = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> dict:
    """List orders filtered by seller/buyer/status, newest first.

    Role scoping is backend-core's job — it passes ``seller_id`` when the
    calling user is a seller.  ``limit`` is clamped to 1..200 and ``offset``
    must be non-negative; an unknown ``status`` value is a 400.
    """
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
                detail=(
                    f"invalid status {status!r} — expected one of "
                    f"{[s.value for s in OrderStatus]}"
                ),
            ) from None

    with SessionLocal() as session:
        total = (
            session.scalar(select(func.count()).select_from(Order).where(*filters)) or 0
        )
        orders = session.scalars(
            select(Order)
            .where(*filters)
            .order_by(Order.created_at.desc())
            .limit(limit)
            .offset(offset)
        ).all()
        return {
            "orders": [_order_dict(o) for o in orders],
            "total": total,
            "limit": limit,
            "offset": offset,
        }


@router.get("/{order_id}")
def get_order(order_id: str) -> dict:
    with SessionLocal() as session:
        order = session.execute(
            select(Order)
            .where(Order.id == uuid.UUID(order_id))
            .options(selectinload(Order.line_items))
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


@router.get("/{order_id}/documents")
def list_order_documents(order_id: str) -> dict:
    """List Document rows for an order, newest version first.

    ``documents.order_id`` only exists once the W2-T5 migration runs — before
    that no row carries an order link, so the response is an empty list (the
    model file is untouched; the guard reads the mapped columns).
    """
    order_uuid = uuid.UUID(order_id)
    order_id_col = getattr(Document, "order_id", None)
    with SessionLocal() as session:
        if order_id_col is None:
            documents = []
        else:
            documents = session.scalars(
                select(Document)
                .where(order_id_col == order_uuid)
                .order_by(Document.version.desc(), Document.id.desc())
            ).all()
        return {
            "order_id": order_id,
            "documents": [_document_dict(d) for d in documents],
        }


@router.get("/{order_id}/pdf")
def order_pdf(order_id: str, doc_type: str = Query("INVOICE")) -> FileResponse:
    """Serve the latest PDF for (order_id, doc_type) — 404 when none exists."""
    order_uuid = uuid.UUID(order_id)
    order_id_col = getattr(Document, "order_id", None)
    with SessionLocal() as session:
        if order_id_col is None:
            raise HTTPException(
                status_code=404,
                detail=f"no {doc_type!r} document for order {order_id!r}",
            )
        doc = session.scalar(
            select(Document)
            .where(order_id_col == order_uuid, Document.doc_type == doc_type)
            .order_by(Document.version.desc(), Document.id.desc())
            .limit(1)
        )
        if doc is None or not Path(doc.file_path).is_file():
            raise HTTPException(
                status_code=404,
                detail=f"no {doc_type!r} document for order {order_id!r}",
            )
        return FileResponse(doc.file_path, media_type="application/pdf")


@router.post("/{order_id}/qr-token")
def set_qr_token(order_id: str, payload: QrTokenPayload) -> dict:
    """Idempotently bind the QR token's JTI to an order."""
    with SessionLocal.begin() as session:
        order = session.execute(
            select(Order).where(Order.id == uuid.UUID(order_id))
        ).scalar_one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail=f"order {order_id!r} not found")
        order.qr_token_jti = payload.jti
    return {"order_id": order_id, "qr_token_jti": payload.jti}


__all__ = ["router"]
