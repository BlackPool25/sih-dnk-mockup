"""Order — partial update payload schemas.

Every field is optional (default ``None``) to support progressive
order composition: the frontend sends only the fields the user has
filled so far, and the backend merges them into the live Order.

``None`` means *not provided in this payload* — the caller does NOT
want to update this field.  This is strictly a data-transfer shape,
not a database model; there are NO SQLAlchemy imports, no DB queries,
and no business logic here.

Line items are modelled as a nested ``LineItemPayload`` list so the
payload can carry zero, one, or many line items in a single request.

Money fields use integer minor units (paise), weight fields use
grams — matching the storage convention of the Order model.
"""

from __future__ import annotations

from pydantic import BaseModel

# ── Nested line-item schema ────────────────────────────────────────────


class LineItemPayload(BaseModel):
    """A single line item within an order payload.

    All fields are optional — every field defaults to ``None``,
    meaning *not provided* rather than *empty* or *zero*.
    """

    category_slug: str | None = None
    quantity: int | None = None
    weight_g: int | None = None
    hs_code: str | None = None
    value_minor: int | None = None
    dimensions: dict | None = None


# ── Top-level order schema ─────────────────────────────────────────────


class OrderPayload(BaseModel):
    """Partial order payload — all fields optional for progressive fills.

    ``order_id`` is ``None`` for new orders (the backend assigns a
    UUID on first persistence).  When non-``None``, the backend
    updates the existing row identified by that UUID.

    ``line_items`` is ``None`` when no line items are included; an
    empty list ``[]`` means *clear all line items*.  A non-empty list
    replaces the full set (the API uses full-replace semantics for
    line items within a partial-order payload).
    """

    order_id: str | None = None
    seller_id: str | None = None
    buyer_id: str | None = None
    destination_country: str | None = None
    value_minor: int | None = None
    currency: str | None = None
    consignee: str | None = None
    net_weight_g: int | None = None
    gross_weight_g: int | None = None
    article_id: str | None = None
    iec: str | None = None
    gstin: str | None = None
    ad_code: str | None = None
    bank_account: str | None = None
    bank_name: str | None = None
    ifsc: str | None = None
    quote_id: str | None = None
    exporter_name: str | None = None
    exporter_address: str | None = None
    state_code: str | None = None
    line_items: list[LineItemPayload] | None = None


__all__ = [
    "LineItemPayload",
    "OrderPayload",
]
