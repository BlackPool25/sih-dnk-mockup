"""Pydantic stubs mapping messaging_* DB tables."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ThreadCreate(BaseModel):
    order_id: uuid.UUID
    seller_id: uuid.UUID
    buyer_id: uuid.UUID


class ThreadOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    seller_id: uuid.UUID
    buyer_id: uuid.UUID
    created_at: datetime
    last_message_at: datetime | None = None
    last_preview_encrypted: str | None = None

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    thread_id: uuid.UUID
    sender_id: uuid.UUID
    sender_role: str = Field(max_length=16)
    body_ciphertext: str
    enc_nonce_b64: str = Field(max_length=64)
    attachments: object | None = None


class MessageOut(BaseModel):
    id: uuid.UUID
    thread_id: uuid.UUID
    sender_id: uuid.UUID
    sender_role: str
    body_ciphertext: str
    enc_nonce_b64: str
    attachments: object | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
