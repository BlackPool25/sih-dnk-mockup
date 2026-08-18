"""Pydantic schemas for order proxies — request/response validation.

backend-core is a thin authenticated proxy over the validation-engine's
unified ``orders`` table.  These schemas mirror the engine's wire format:
no encrypted columns (ad_code/bank_account/gstin are plaintext), no
profile_version/doc_pack_id — those live in validation-engine now.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class LineItemRequest(BaseModel):
    """A single line item within an order-create payload."""

    model_config = ConfigDict(extra="forbid")

    category_slug: str = Field(..., min_length=1)
    quantity: int = Field(..., gt=0)
    weight_g: int = Field(..., gt=0)
    hs_code: str | None = Field(None, max_length=20)
    value_minor: int = Field(..., gt=0)


class OrderCreateRequest(BaseModel):
    """Schema for POST /orders — trade-order fields sent to validation-engine.

    Seller identity fields (iec, ad_code, bank details, exporter name/address,
    state_code) are auto-filled from the authenticated seller's profile by the
    router; only ``gstin`` and ``state_code`` may be overridden by the caller.
    """

    model_config = ConfigDict(extra="forbid")

    destination_country: str = Field(..., min_length=1, max_length=100)
    value_minor: int = Field(..., gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    consignee: str = Field(..., min_length=1, max_length=255)
    net_weight_g: int = Field(..., gt=0)
    gross_weight_g: int = Field(..., gt=0)
    article_id: str | None = Field(None, max_length=50)
    line_items: list[LineItemRequest] = Field(..., min_length=1)
    gstin: str | None = Field(None, max_length=20)
    state_code: str | None = Field(None, min_length=2, max_length=2)


class OrderResponse(BaseModel):
    """Schema for order responses — mirrors validation-engine's unified order.

    Fields are nullable to match the engine's sparse/partial order rows;
    ``validation_report`` is populated only on POST /orders.
    """

    model_config = ConfigDict(extra="forbid")

    id: str
    seller_id: str | None = None
    buyer_id: str | None = None
    status: str
    validation_state: str | None = None
    destination_country: str | None = None
    value_minor: int | None = None
    currency: str = "INR"
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
    qr_token_jti: str | None = None
    version: int | None = None
    line_items: list[dict]
    created_at: str | None = None
    updated_at: str | None = None
    validation_report: dict | None = None


class OrderListResponse(BaseModel):
    """Paginated list of orders."""

    orders: list[OrderResponse]
    total: int
    limit: int
    offset: int
