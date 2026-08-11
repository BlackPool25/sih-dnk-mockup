"""GET /orders/{order_id} — return persisted Order JSON with last_report and line_items."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db import SessionLocal
from app.models.order import Order

router = APIRouter(prefix="/orders", tags=["orders"])


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
            "order": {
                "id": str(order.id),
                "status": order.status.value,
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
                "version": order.version,
                "created_at": order.created_at.isoformat() if order.created_at else None,
                "updated_at": order.updated_at.isoformat() if order.updated_at else None,
            },
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


__all__ = ["router"]
