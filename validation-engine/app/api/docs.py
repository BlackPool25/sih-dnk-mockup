"""Document generation API — POST /docs/generate and POST /docs/generate-all.

Both endpoints re-validate the order via ``graded_evaluate()`` and gate on
``validation_state == "ready"`` before dispatching to the renderer.  When the
order has multiple line items and the requested doc type is INVOICE or
PACKING_LIST, ``render()`` delegates to ``render_line_items()`` internally.
"""

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


def _document_data_for(order: Order, doc_type: str) -> DocumentData:
    """Build DocumentData from the order's first line item (single-doc path).

    Mirrors graded_evaluate's gate inputs: the first line item's category
    supplies the HS/duty/lane lookups; destination/weights come from the order
    itself.  Multi-line INVOICE/PACKING_LIST orders delegate to
    ``render_line_items()`` which builds its own per-line DocumentData.
    """
    first_li = order.line_items[0] if order.line_items else None
    category_slug = first_li.category_slug if first_li else "embroidered-home-textiles"
    destination = order.destination_country or DESTINATION_UNSTATED
    quantity = first_li.quantity if first_li and first_li.quantity else QUANTITY_UNSTATED
    weight = first_li.weight_g if first_li and first_li.weight_g else WEIGHT_UNSTATED

    shipment = Shipment(
        product_category=category_slug,
        quantity=quantity,
        weight_grams=weight,
        destination_country=destination,
        confidence="high",
    )
    return build_document_data(
        shipment,
        doc_type,
        consignee=order.consignee,
        value_minor=order.value_minor,
        iec=order.iec,
        gstin=order.gstin,
        net_weight_g=order.net_weight_g,
    )


@router.post("/generate")
def generate_docs(
    order_id: str = Query(...),
    doc_type: str = Query("INVOICE"),
) -> dict:
    """Re-validate an order then render the requested document.

    - 404 if the order does not exist.
    - 200 with ``"incomplete"`` status when validation is not yet ready.
    - 200 with PDF metadata when the document is rendered successfully.
    """
    with SessionLocal.begin() as session:
        order = session.execute(
            select(Order).where(Order.id == uuid.UUID(order_id))
        ).scalar_one_or_none()
        if order is None:
            raise HTTPException(status_code=404, detail=f"order {order_id!r} not found")

        try:
            ensure_latin_free_text(order.consignee, "consignee")
        except NonLatinFreeTextError as exc:
            raise HTTPException(status_code=422, detail=f"translate before submit: {exc}") from exc

        # Re-run graded evaluation.
        report = graded_evaluate(order)

        # Gate: only render if the order is validated as ready.
        if report.validation_state != "ready":
            return {
                "status": "incomplete",
                "order_id": order_id,
                "validation_state": report.validation_state,
                "missing_fields": [m.field_key for m in report.missing],
                "message": "Order validation incomplete — cannot generate documents",
            }

        # Build DocumentData from the first line item for the single-doc
        # fallback path.  When the order has >1 line item and doc_type is
        # INVOICE/PACKING_LIST, ``render()`` delegates to
        # ``render_line_items()`` which builds its own DocumentData per line.
        try:
            data = _document_data_for(order, doc_type)
            doc = render(data, doc_type, order=order)
        except NonLatinFreeTextError as exc:
            raise HTTPException(status_code=422, detail=f"translate before submit: {exc}") from exc

        return {
            "pdf_url": doc.file_path,
            "checksum": doc.checksum,
            "doc_type": doc.doc_type,
            "version": doc.version,
            "order_id": order_id,
        }


@router.post("/generate-all")
def generate_all_docs(order_id: str = Query(...)) -> dict:
    """Re-validate an order then render all four document types.

    - 404 if the order does not exist.
    - 200 with ``"incomplete"`` status when validation is not yet ready.
    - 200 with ``"complete"`` + per-document metadata once all four render
      (INVOICE, PACKING_LIST, CN22 — which auto-switches to CN23 when the
      SDR value exceeds 300 — and PBE_IV).
    """
    with SessionLocal.begin() as session:
        order = session.execute(
            select(Order).where(Order.id == uuid.UUID(order_id))
        ).scalar_one_or_none()
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

        documents: list[dict] = []
        for doc_type in ("INVOICE", "PACKING_LIST", "CN22", "PBE_IV"):
            try:
                doc = render(_document_data_for(order, doc_type), doc_type, order=order)
            except NonLatinFreeTextError as exc:
                raise HTTPException(
                    status_code=422, detail=f"translate before submit: {exc}"
                ) from exc
            documents.append(
                {
                    "doc_type": doc.doc_type,
                    "version": doc.version,
                    "checksum": doc.checksum,
                    "pdf_url": doc.file_path,
                    "generated_at": doc.created_at.isoformat() if doc.created_at else None,
                }
            )

        return {
            "order_id": order_id,
            "validation_state": "ready",
            "status": "complete",
            "documents": documents,
        }
