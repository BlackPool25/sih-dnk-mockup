"""Document generation API — POST /docs/generate and POST /docs/generate-all."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from app.db import SessionLocal
from app.models.order import Order
from app.schemas.shipment import (
    DESTINATION_UNSTATED,
    QUANTITY_UNSTATED,
    WEIGHT_UNSTATED,
    Shipment,
)
from app.services.docs.document import (
    DocumentData,
    NonLatinFreeTextError,
    build_document_data,
    ensure_latin_free_text,
)
from app.services.docs.renderer import render
from app.services.graded import graded_evaluate

router = APIRouter(prefix="/docs", tags=["docs"])


def _document_data_for(order: Order, doc_type: str, parcel: dict | None = None) -> DocumentData:
    first_li = order.line_items[0] if order.line_items else None
    category_slug = first_li.category_slug if first_li else "embroidered-home-textiles"
    destination = order.destination_country or DESTINATION_UNSTATED
    parcel_lane = parcel.get("lane") if parcel else None
    if parcel is not None:
        # Aggregated parcel values from pricing-engine parcel dict
        qty_map = parcel.get("item_quantities", {})
        total_qty = sum(qty_map.values()) if qty_map else (first_li.quantity if first_li and first_li.quantity else QUANTITY_UNSTATED)
        # Map item ids to line items for value sum
        id_to_li = {str(li.id): li for li in order.line_items}
        total_value = 0
        for item_id, q in qty_map.items():
            li = id_to_li.get(item_id)
            if li and li.value_minor:
                # parcel value = unit value * quantity in parcel
                unit_val = (li.value_minor // (li.quantity or 1)) if li.quantity else li.value_minor
                total_value += unit_val * q
        if total_value == 0:
            # fallback to proportional or order value slice
            total_value = parcel.get("total_cost_minor") or order.value_minor
            if total_value is None:
                total_value = first_li.value_minor if first_li else None
        weight = parcel.get("actual_weight_g") or parcel.get("product_weight_g") or (first_li.weight_g if first_li and first_li.weight_g else WEIGHT_UNSTATED)
        # Use actual_weight clipped to product weight for doc semantics (parcel product weight)
        quantity = total_qty
        value_minor = total_value if total_value and total_value > 0 else order.value_minor
    else:
        # Single-parcel: use optimal lane if exists
        parcel_lane = None
        if order.parcels and len(order.parcels) == 1:
            parcel_lane = order.parcels[0].get("lane")
        quantity = first_li.quantity if first_li and first_li.quantity else QUANTITY_UNSTATED
        weight = first_li.weight_g if first_li and first_li.weight_g else WEIGHT_UNSTATED
        value_minor = order.value_minor

    shipment = Shipment(
        product_category=category_slug,
        quantity=quantity,
        weight_grams=weight,
        destination_country=destination,
        confidence="high",
    )
    kwargs: dict = {
        "consignee": order.consignee,
        "value_minor": value_minor,
        "iec": order.iec,
        "gstin": order.gstin,
        "net_weight_g": order.net_weight_g,
    }
    if parcel_lane:
        kwargs["lane"] = parcel_lane
    return build_document_data(shipment, doc_type, **kwargs)


@router.post("/generate")
def generate_docs(
    order_id: str = Query(...),
    doc_type: str = Query("INVOICE"),
) -> dict:
    with SessionLocal.begin() as session:
        order = session.execute(select(Order).where(Order.id == uuid.UUID(order_id))).scalar_one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail=f"order {order_id!r} not found")
        try:
            ensure_latin_free_text(order.consignee, "consignee")
        except NonLatinFreeTextError as exc:
            raise HTTPException(status_code=422, detail=f"translate before submit: {exc}") from exc
        report = graded_evaluate(order)
        if report.validation_state != "ready":
            return {
                "status": "incomplete",
                "order_id": order_id,
                "validation_state": report.validation_state,
                "missing_fields": [m.field_key for m in report.missing],
                "message": "Order validation incomplete — cannot generate documents",
            }
        parcels = order.parcels or []
        if len(parcels) > 1:
            docs = []
            for parcel in parcels:
                try:
                    data = _document_data_for(order, doc_type, parcel)
                    doc = render(data, doc_type, order=order, parcel_id=parcel.get("parcel_id"))
                except NonLatinFreeTextError as exc:
                    raise HTTPException(status_code=422, detail=f"translate before submit: {exc}") from exc
                docs.append(doc)
            primary = docs[0]
            return {
                "pdf_url": primary.file_path,
                "checksum": primary.checksum,
                "doc_type": primary.doc_type,
                "version": primary.version,
                "order_id": order_id,
                "parcel_id": primary.parcel_id,
                "parcels": [{"parcel_id": d.parcel_id, "pdf_url": d.file_path, "doc_type": d.doc_type} for d in docs],
            }
        try:
            data = _document_data_for(order, doc_type)
            parcel_id = parcels[0].get("parcel_id") if len(parcels) == 1 else None
            doc = render(data, doc_type, order=order, parcel_id=parcel_id)
        except NonLatinFreeTextError as exc:
            raise HTTPException(status_code=422, detail=f"translate before submit: {exc}") from exc
        return {
            "pdf_url": doc.file_path,
            "checksum": doc.checksum,
            "doc_type": doc.doc_type,
            "version": doc.version,
            "order_id": order_id,
            "parcel_id": doc.parcel_id,
        }


@router.post("/generate-all")
def generate_all_docs(order_id: str = Query(...)) -> dict:
    with SessionLocal.begin() as session:
        order = session.execute(select(Order).where(Order.id == uuid.UUID(order_id))).scalar_one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail=f"order {order_id!r} not found")
        try:
            ensure_latin_free_text(order.consignee, "consignee")
        except NonLatinFreeTextError as exc:
            raise HTTPException(status_code=422, detail=f"translate before submit: {exc}") from exc
        report = graded_evaluate(order)
        if report.validation_state != "ready":
            return {
                "status": "incomplete",
                "order_id": order_id,
                "validation_state": report.validation_state,
                "missing_fields": [m.field_key for m in report.missing],
                "message": "Order validation incomplete — cannot generate documents",
            }
        parcels = order.parcels or []
        documents: list[dict] = []
        if len(parcels) > 1:
            for doc_type in ("INVOICE", "PACKING_LIST", "CN22", "PBE_IV"):
                for parcel in parcels:
                    try:
                        doc = render(_document_data_for(order, doc_type, parcel), doc_type, order=order, parcel_id=parcel.get("parcel_id"))
                    except NonLatinFreeTextError as exc:
                        raise HTTPException(status_code=422, detail=f"translate before submit: {exc}") from exc
                    documents.append(
                        {
                            "doc_type": doc.doc_type,
                            "version": doc.version,
                            "checksum": doc.checksum,
                            "pdf_url": doc.file_path,
                            "parcel_id": doc.parcel_id,
                            "generated_at": doc.created_at.isoformat() if doc.created_at else None,
                        }
                    )
        else:
            parcel_id_single = parcels[0].get("parcel_id") if len(parcels) == 1 else None
            for doc_type in ("INVOICE", "PACKING_LIST", "CN22", "PBE_IV"):
                try:
                    doc = render(_document_data_for(order, doc_type), doc_type, order=order, parcel_id=parcel_id_single)
                except NonLatinFreeTextError as exc:
                    raise HTTPException(status_code=422, detail=f"translate before submit: {exc}") from exc
                documents.append(
                    {
                        "doc_type": doc.doc_type,
                        "version": doc.version,
                        "checksum": doc.checksum,
                        "pdf_url": doc.file_path,
                        "parcel_id": doc.parcel_id,
                        "generated_at": doc.created_at.isoformat() if doc.created_at else None,
                    }
                )
        return {
            "order_id": order_id,
            "validation_state": "ready",
            "status": "complete",
            "documents": documents,
        }
