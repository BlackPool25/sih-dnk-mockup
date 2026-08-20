"""Pydantic schemas for messaging — inbox, thread, messages with mocked:true."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Thread create
# ---------------------------------------------------------------------------
class ThreadCreate(BaseModel):
    order_id: uuid.UUID
    seller_id: uuid.UUID
    buyer_id: uuid.UUID


class ThreadCreateResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    seller_id: uuid.UUID
    buyer_id: uuid.UUID
    created_at: datetime
    last_message_at: datetime | None = None
    mocked: Literal[True] = True


# ---------------------------------------------------------------------------
# Thread detail (GET /threads/{id})
# ---------------------------------------------------------------------------
class ThreadDetailResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    seller_id: uuid.UUID
    buyer_id: uuid.UUID
    created_at: datetime
    last_message_at: datetime | None = None
    last_preview: str | None = None
    mocked: Literal[True] = True


# ---------------------------------------------------------------------------
# Inbox
# ---------------------------------------------------------------------------
class InboxItem(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    seller_id: uuid.UUID
    buyer_id: uuid.UUID
    created_at: datetime
    last_message_at: datetime | None = None
    last_preview: str | None = None
    unread_count: int = 0


class InboxResponse(BaseModel):
    items: list[InboxItem]
    total: int
    limit: int
    offset: int
    mocked: Literal[True] = True


# ---------------------------------------------------------------------------
# Messages paging
# ---------------------------------------------------------------------------
class AttachmentMeta(BaseModel):
    filename: str
    content_type: str
    size_bytes: int


class MessageItem(BaseModel):
    id: uuid.UUID
    thread_id: uuid.UUID
    sender_id: uuid.UUID
    sender_role: str
    body: str
    attachments: list[AttachmentMeta] | None = None
    created_at: datetime


class MessagesPageResponse(BaseModel):
    items: list[MessageItem]
    total: int
    limit: int
    offset: int
    mocked: Literal[True] = True


class MessageCreateResponse(BaseModel):
    id: uuid.UUID
    thread_id: uuid.UUID
    sender_id: uuid.UUID
    sender_role: str
    body: str
    attachments: list[AttachmentMeta] | None = None
    created_at: datetime
    mocked: Literal[True] = True


# ---------------------------------------------------------------------------
# Legacy keep — not used but preserved for compat
# ---------------------------------------------------------------------------
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


class ThreadOut(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    seller_id: uuid.UUID
    buyer_id: uuid.UUID
    created_at: datetime
    last_message_at: datetime | None = None
    last_preview_encrypted: str | None = None

    model_config = {"from_attributes": True}
