"""Document-generation routes — thin proxy over validation-engine's docs API.

POST /orders/{order_id}/generate-docs — batch-render CI, PL, CN, and PBE
documents in validation-engine and return the per-document metadata.
Re-generation is allowed (documents are immutable & versioned, never overwritten).
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from app.routers.orders import _get_order_or_404, _split_order_data
from app.services.val_client import (
    InvalidInputError,
    NotFoundError,
    ServiceUnavailable,
    val_client,
)
from auth.deps import get_current_user, require_role

# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/orders/{order_id}", tags=["docs"])

# validation-engine doc_type → named key in the generate-docs response.
_DOC_KEY_BY_TYPE: dict[str, str] = {
    "INVOICE": "commercial_invoice",
    "PACKING_LIST": "packing_list",
    "CN22": "customs_declaration",
    "CN23": "customs_declaration",
    "PBE_IV": "postal_bill_of_export",
}


def _map_generated_documents(docs: list[object]) -> dict[str, object]:
    """Map the engine's document list into named document slots."""
    mapped: dict[str, object] = {key: None for key in _DOC_KEY_BY_TYPE.values()}
    for doc in docs:
        if not isinstance(doc, dict):
            continue
        doc_type = doc.get("doc_type")
        key = _DOC_KEY_BY_TYPE.get(str(doc_type)) if doc_type is not None else None
        if key is not None:
            mapped[key] = doc
    return mapped


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
) -> dict[str, object]:
    """Generate all export documents for an order in validation-engine.

    Requires seller authentication; only the order's owner may trigger
    generation.  Documents are immutable & versioned — regeneration is allowed.
    """
    user = request.state.user
    user_id: str = str(user["user_id"])

    order_data = await _get_order_or_404(order_id)
    order, _line_items = _split_order_data(order_data)

    if str(order.get("seller_id") or "") != user_id:
        raise HTTPException(status_code=403, detail="Only the order owner can generate documents")

    try:
        result = await val_client.generate_docs_all(order_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except InvalidInputError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except ServiceUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    raw_docs = result.get("documents", [])
    doc_list = raw_docs if isinstance(raw_docs, list) else []

    generated_at = result.get("generated_at")
    if generated_at is None:
        for doc in doc_list:
            if isinstance(doc, dict) and doc.get("generated_at"):
                generated_at = doc.get("generated_at")
                break

    return {
        "order_id": str(result.get("order_id") or order_id),
        "status": result.get("status", "complete"),
        "validation_state": result.get("validation_state"),
        "documents": _map_generated_documents(doc_list),
        "generated_at": generated_at,
    }
