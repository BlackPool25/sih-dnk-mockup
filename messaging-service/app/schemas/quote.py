"""Pydantic stubs mapping quote_* DB tables."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

QuoteStateLiteral = Literal["draft", "sent", "counter", "approved", "paid_held"]


class QuoteStateCreate(BaseModel):
    order_id: uuid.UUID
    thread_id: uuid.UUID | None = None
    seller_id: uuid.UUID
    buyer_id: uuid.UUID
    amount_minor: int = Field(ge=0)
    currency: str = Field(default="INR", max_length=3)
    qty: int | None = Field(default=None, ge=1)
    shipping_minor: int = Field(default=0, ge=0)
    state: QuoteStateLiteral = "draft"


class QuoteStateOut(BaseModel):
    quote_id: uuid.UUID
    order_id: uuid.UUID
    thread_id: uuid.UUID | None = None
    seller_id: uuid.UUID
    buyer_id: uuid.UUID
    current_version: int
    state: QuoteStateLiteral
    amount_minor: int
    currency: str
    qty: int | None = None
    shipping_minor: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class QuoteVersionCreate(BaseModel):
    quote_id: uuid.UUID
    version: int = Field(ge=1)
    price_minor: int = Field(ge=0)
    qty: int | None = Field(default=None, ge=1)
    shipping_minor: int = Field(default=0, ge=0)
    status: str = Field(max_length=16)
    created_by: uuid.UUID
    reason: str | None = None


class QuoteVersionOut(BaseModel):
    quote_id: uuid.UUID
    version: int
    price_minor: int
    qty: int | None = None
    shipping_minor: int
    status: str
    created_by: uuid.UUID
    reason: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
