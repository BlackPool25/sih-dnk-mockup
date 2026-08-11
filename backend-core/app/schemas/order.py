"""Pydantic schemas for order CRUD — request/response validation.

Encrypted fields (``ad_code``, ``bank_account``) use plaintext names in
responses — the router is responsible for decrypting before returning.
The ``profile_snapshot_encrypted`` is never exposed in responses.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LineItemRequest(BaseModel):
    """Single line item within an order."""

    model_config = ConfigDict(extra="forbid")

    description: str = Field(..., min_length=1, max_length=500)
    hsn_code: str = Field(..., min_length=1, max_length=12)
    quantity: int = Field(..., gt=0)
    unit_price_minor: int = Field(..., gt=0)
    total_minor: int = Field(..., gt=0)


class OrderCreateRequest(BaseModel):
    """Schema for POST /orders — all trade-order details except auto-filled profile fields."""

    model_config = ConfigDict(extra="forbid")

    destination_country: str = Field(..., min_length=1, max_length=100)
    value_minor: int = Field(..., gt=0)
    consignee: str = Field(..., min_length=1, max_length=255)
    net_weight_g: float = Field(..., gt=0)
    gross_weight_g: float = Field(..., gt=0)
    line_items: list[LineItemRequest] = Field(..., min_length=1)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    article_id: str | None = Field(None, max_length=50)


class OrderResponse(BaseModel):
    """Schema for order responses — encrypted fields are decrypted."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    seller_id: str
    buyer_id: str
    status: str
    profile_version: int
    destination_country: str
    value_minor: int
    currency: str
    consignee: str
    net_weight_g: float
    gross_weight_g: float
    article_id: str | None = None
    iec: str
    ad_code: str | None = None
    bank_account: str | None = None
    bank_name: str
    ifsc: str
    exporter_name: str
    exporter_address: str
    state_code: str
    line_items: list[dict]
    doc_pack_id: str | None = None
    qr_token_jti: str | None = None
    created_at: str
    updated_at: str


class OrderListResponse(BaseModel):
    """Paginated list of orders."""

    orders: list[OrderResponse]
    total: int
    limit: int
    offset: int
