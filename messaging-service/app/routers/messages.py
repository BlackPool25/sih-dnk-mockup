"""Messaging router — inbox + thread + send + paging + attachments."""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Annotated

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile
from sqlalchemy import ColumnElement, asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import MessagingMessage, MessagingThread
from app.schemas.message import (
    AttachmentMeta,
    InboxItem,
    InboxResponse,
    MessageCreateResponse,
    MessageItem,
    MessagesPageResponse,
    ThreadCreate,
    ThreadCreateResponse,
    ThreadDetailResponse,
)
from app.services.auth import AuthUser, get_current_user, require_member, require_member_for_write
from app.services.crypto import decrypt_thread_message, encrypt_thread_message

router = APIRouter(prefix="/messages", tags=["messages"])

MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
ALLOWED_CONTENT_PREFIXES: tuple[str, ...] = ("image/", "text/")
ALLOWED_EXACT: tuple[str, ...] = ("application/pdf",)
MAX_LIMIT = 50
DEFAULT_INBOX_LIMIT = 20
DEFAULT_MSG_LIMIT = 20


# ---------------------------------------------------------------------------
# DB session dependency
# ---------------------------------------------------------------------------
def _get_engine():
    url: str = os.environ.get("DATABASE_URL", "")
    if not url:
        url = "postgresql+psycopg://sih_dnk:changeme@localhost:5433/sih_dnk"
    return create_async_engine(url, pool_pre_ping=True)


def _get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(_get_engine(), expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = _get_sessionmaker()
    async with factory() as session:
        yield session  # type: ignore[misc]


SessionDep = Annotated[AsyncSession, Depends(get_session)]
UserDep = Annotated[AuthUser, Depends(get_current_user)]


def _master_key() -> bytes:
    hex_env: str | None = os.environ.get("ENCRYPTION_MASTER_KEY")
    if hex_env is not None and hex_env != "":
        return bytes.fromhex(hex_env)
    try:
        from storage.config import settings as s  # type: ignore[import-untyped]

        hex_key: str = str(s.ENCRYPTION_MASTER_KEY)
        if hex_key:
            return bytes.fromhex(hex_key)
    except Exception:
        pass
    return bytes.fromhex("00" * 32)


def _decrypt_preview(thread_id: str, stored: str | None, master_key: bytes) -> str | None:
    """Decrypt last_preview_encrypted JSON container; None if absent/corrupt."""
    if stored is None:
        return None
    is_json = stored.strip().startswith("{")
    if is_json:
        try:
            obj: dict[str, object] = json.loads(stored)
            ct = obj.get("ciphertext_b64")
            nonce = obj.get("nonce_b64")
            if isinstance(ct, str) and isinstance(nonce, str):
                return decrypt_thread_message(ct, nonce, thread_id, master_key)
        except Exception:
            return None
        return None
    # legacy colon form ciphertext:nonce
    if ":" in stored:
        parts: list[str] = stored.split(":", 1)
        try:
            return decrypt_thread_message(parts[0], parts[1], thread_id, master_key)
        except Exception:
            return None
    return None


def _encrypt_preview(thread_id: str, preview: str, master_key: bytes) -> str:
    """Encrypt preview text into JSON string for storage."""
    enc = encrypt_thread_message(preview, thread_id, master_key)
    return json.dumps({"ciphertext_b64": enc["ciphertext_b64"], "nonce_b64": enc["nonce_b64"]})


def _attachment_to_meta(att: object) -> AttachmentMeta | None:
    if isinstance(att, dict):
        fn = att.get("filename")
        ct = att.get("content_type")
        sz = att.get("size_bytes")
        if isinstance(fn, str) and isinstance(ct, str) and isinstance(sz, int):
            return AttachmentMeta(filename=fn, content_type=ct, size_bytes=sz)
    return None


def _attachments_from_jsonb(raw: object | None) -> list[AttachmentMeta] | None:
    if raw is None:
        return None
    if isinstance(raw, list):
        out: list[AttachmentMeta] = []
        for item in raw:
            meta = _attachment_to_meta(item)
            if meta is not None:
                out.append(meta)
        return out if out else None
    return None


async def _validate_order_best_effort(order_id: uuid.UUID) -> None:
    """Best-effort order validation via validation-engine; skip if down."""
    # Use VALIDATION_ENGINE_URL from settings or env
    base_url: str | None = None
    try:
        from storage.config import settings as s  # type: ignore[import-untyped]

        base_url = str(s.VALIDATION_ENGINE_URL)
    except Exception:
        base_url = os.environ.get("VALIDATION_ENGINE_URL")
    if base_url is None or base_url == "":
        return
    base_url = base_url.rstrip("/")
    url = f"{base_url}/orders/{order_id}"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                raise HTTPException(status_code=404, detail="Order not found")
            # 2xx -> order exists, other codes -> best-effort skip
    except HTTPException:
        raise
    except Exception:
        # network down -> skip validation
        return


# ---------------------------------------------------------------------------
# GET /messages/inbox
# ---------------------------------------------------------------------------
@router.get("/inbox", response_model=InboxResponse)
async def inbox(
    request: Request,
    session: SessionDep,
    user: UserDep,
    limit: int = Query(default=DEFAULT_INBOX_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
) -> InboxResponse:
    _ = request
    uid_str: str = user["user_id"]
    is_sahayak: bool = user["role"] == "sahayak"
    master_key = _master_key()

    # Count total for paging
    if is_sahayak:
        count_q = select(func.count()).select_from(MessagingThread)  # type: ignore[arg-type]
    else:
        try:
            uid = uuid.UUID(uid_str)
            count_q = (
                select(func.count())
                .select_from(MessagingThread)
                .where(or_(MessagingThread.seller_id == uid, MessagingThread.buyer_id == uid))  # type: ignore[arg-type]
            )
        except ValueError:
            # user_id not UUID -> no results
            count_q = select(func.count()).select_from(MessagingThread).where(False)  # type: ignore[arg-type]

    total_res = await session.execute(count_q)
    total: int = int(total_res.scalar_one())

    # Fetch page ordered by last_message_at desc nulls last, then created_at desc
    if is_sahayak:
        q = (
            select(MessagingThread)
            .order_by(desc(MessagingThread.last_message_at), desc(MessagingThread.created_at))
            .limit(limit)
            .offset(offset)
        )
    else:
        try:
            uid2 = uuid.UUID(uid_str)
            q = (
                select(MessagingThread)
                .where(or_(MessagingThread.seller_id == uid2, MessagingThread.buyer_id == uid2))
                .order_by(desc(MessagingThread.last_message_at), desc(MessagingThread.created_at))
                .limit(limit)
                .offset(offset)
            )
        except ValueError:
            q = select(MessagingThread).where(False).limit(limit).offset(offset)  # type: ignore[arg-type]

    result = await session.execute(q)
    threads: list[MessagingThread] = list(result.scalars().all())

    items: list[InboxItem] = []
    for t in threads:
        tid_str = str(t.id)
        preview: str | None = _decrypt_preview(tid_str, t.last_preview_encrypted, master_key)
        items.append(
            InboxItem(
                id=t.id,
                order_id=t.order_id,
                seller_id=t.seller_id,
                buyer_id=t.buyer_id,
                created_at=t.created_at,
                last_message_at=t.last_message_at,
                last_preview=preview,
                unread_count=0,
            )
        )

    return InboxResponse(items=items, total=total, limit=limit, offset=offset, mocked=True)


# ---------------------------------------------------------------------------
# POST /messages/threads
# ---------------------------------------------------------------------------
@router.post("/threads", response_model=ThreadCreateResponse, status_code=201)
async def create_thread(
    body: ThreadCreate,
    session: SessionDep,
    user: UserDep,
) -> ThreadCreateResponse:
    _ = user
    # Best-effort order validation
    await _validate_order_best_effort(body.order_id)

    # Idempotent: if order_id already exists, return existing
    existing_q = select(MessagingThread).where(MessagingThread.order_id == body.order_id)
    existing_res = await session.execute(existing_q)
    existing: MessagingThread | None = existing_res.scalar_one_or_none()
    if existing is not None:
        return ThreadCreateResponse(
            id=existing.id,
            order_id=existing.order_id,
            seller_id=existing.seller_id,
            buyer_id=existing.buyer_id,
            created_at=existing.created_at,
            last_message_at=existing.last_message_at,
            mocked=True,
        )

    # Try PG ON CONFLICT DO NOTHING for race safety; fallback to plain insert
    thread = MessagingThread(
        id=uuid.uuid4(),
        order_id=body.order_id,
        seller_id=body.seller_id,
        buyer_id=body.buyer_id,
    )
    session.add(thread)
    try:
        await session.commit()
        await session.refresh(thread)
    except Exception as exc:
        await session.rollback()
        # Handle IntegrityError (concurrent insert) -> fetch existing
        # Check if it's a unique violation; otherwise re-raise as 500
        msg = str(exc).lower()
        if "unique" in msg or "duplicate" in msg or "conflict" in msg:
            retry_res = await session.execute(existing_q)
            retry: MessagingThread | None = retry_res.scalar_one_or_none()
            if retry is not None:
                return ThreadCreateResponse(
                    id=retry.id,
                    order_id=retry.order_id,
                    seller_id=retry.seller_id,
                    buyer_id=retry.buyer_id,
                    created_at=retry.created_at,
                    last_message_at=retry.last_message_at,
                    mocked=True,
                )
        raise HTTPException(status_code=500, detail="Failed to create thread") from exc

    return ThreadCreateResponse(
        id=thread.id,
        order_id=thread.order_id,
        seller_id=thread.seller_id,
        buyer_id=thread.buyer_id,
        created_at=thread.created_at,
        last_message_at=thread.last_message_at,
        mocked=True,
    )


# ---------------------------------------------------------------------------
# GET /messages/threads/{thread_id}  (and alias GET /messages/threads/{id} for polling)
# ---------------------------------------------------------------------------
@router.get("/threads/{thread_id}", response_model=ThreadDetailResponse)
async def get_thread(
    thread_id: uuid.UUID,
    session: SessionDep,
    user: UserDep,
) -> ThreadDetailResponse:
    thread = await require_member(str(thread_id), user, session)
    master_key = _master_key()
    preview: str | None = _decrypt_preview(str(thread.id), thread.last_preview_encrypted, master_key)
    return ThreadDetailResponse(
        id=thread.id,
        order_id=thread.order_id,
        seller_id=thread.seller_id,
        buyer_id=thread.buyer_id,
        created_at=thread.created_at,
        last_message_at=thread.last_message_at,
        last_preview=preview,
        mocked=True,
    )


# ---------------------------------------------------------------------------
# GET /messages/threads/{thread_id}/messages  (paged, decrypt, total, before)
# ---------------------------------------------------------------------------
@router.get("/threads/{thread_id}/messages", response_model=MessagesPageResponse)
async def list_messages(
    thread_id: uuid.UUID,
    session: SessionDep,
    user: UserDep,
    limit: int = Query(default=DEFAULT_MSG_LIMIT, ge=1, le=MAX_LIMIT),
    offset: int = Query(default=0, ge=0),
    before: str | None = Query(default=None),
) -> MessagesPageResponse:
    await require_member(str(thread_id), user, session)

    before_dt: datetime | None = None
    if before is not None:
        try:
            # Accept ISO8601 with Z
            iso = before.replace("Z", "+00:00") if before.endswith("Z") else before
            before_dt = datetime.fromisoformat(iso)
            if before_dt.tzinfo is None:
                before_dt = before_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid before timestamp (expected ISO8601)") from None

    master_key = _master_key()

    base_filters: list[ColumnElement[bool]] = [MessagingMessage.thread_id == thread_id]
    if before_dt is not None:
        base_filters.append(MessagingMessage.created_at < before_dt)  # type: ignore[arg-type,operator]

    count_q = select(func.count()).select_from(MessagingMessage).where(*base_filters)
    total_res = await session.execute(count_q)
    total: int = int(total_res.scalar_one())

    # page ordered by created_at asc (chronological)
    q = (
        select(MessagingMessage)
        .where(*base_filters)
        .order_by(asc(MessagingMessage.created_at))
        .limit(limit)
        .offset(offset)
    )
    result = await session.execute(q)
    rows: list[MessagingMessage] = list(result.scalars().all())

    items: list[MessageItem] = []
    tid_str = str(thread_id)
    for m in rows:
        try:
            body_plain = decrypt_thread_message(m.body_ciphertext, m.enc_nonce_b64, tid_str, master_key)
        except Exception:
            body_plain = ""
        attachments = _attachments_from_jsonb(m.attachments)
        items.append(
            MessageItem(
                id=m.id,
                thread_id=m.thread_id,
                sender_id=m.sender_id,
                sender_role=m.sender_role,
                body=body_plain,
                attachments=attachments,
                created_at=m.created_at,
            )
        )

    return MessagesPageResponse(items=items, total=total, limit=limit, offset=offset, mocked=True)


# ---------------------------------------------------------------------------
# POST /messages/threads/{thread_id}/messages  (multipart, encrypt, 10MB limit)
# ---------------------------------------------------------------------------
@router.post("/threads/{thread_id}/messages", response_model=MessageCreateResponse, status_code=201)
async def post_message(
    thread_id: uuid.UUID,
    session: SessionDep,
    user: UserDep,
    body: str = Form(..., min_length=1),
    attachments: list[UploadFile] | None = File(default=None),
) -> MessageCreateResponse:
    # Member write check — sahayak 403
    thread = await require_member_for_write(str(thread_id), user, session)

    # Validate & collect attachment metadata
    metas: list[dict[str, object]] = []
    attachment_metas: list[AttachmentMeta] = []
    if attachments is not None:
        for up in attachments:
            # Read content to enforce size + store filename
            content: bytes = await up.read()
            size = len(content)
            if size > MAX_ATTACHMENT_BYTES:
                raise HTTPException(status_code=422, detail=f"Attachment {up.filename} exceeds 10MB limit")
            ctype: str = (up.content_type or "").lower()
            allowed = False
            for prefix in ALLOWED_CONTENT_PREFIXES:
                if ctype.startswith(prefix):
                    allowed = True
                    break
            if not allowed and ctype not in ALLOWED_EXACT:
                raise HTTPException(status_code=422, detail=f"Attachment content-type {ctype} not allowed")
            fname: str = up.filename or "file"
            meta_dict: dict[str, object] = {"filename": fname, "content_type": ctype, "size_bytes": size}
            metas.append(meta_dict)
            attachment_metas.append(AttachmentMeta(filename=fname, content_type=ctype, size_bytes=size))
            # Note: file bytes not persisted; metadata inline per spec (JSONB inline)

    master_key = _master_key()
    tid_str = str(thread_id)
    enc = encrypt_thread_message(body, tid_str, master_key)

    # Resolve sender_id
    sender_id_str: str = user["user_id"]
    try:
        sender_uuid = uuid.UUID(sender_id_str)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid sender user_id") from None

    sender_role: str = user["role"]

    msg = MessagingMessage(
        id=uuid.uuid4(),
        thread_id=thread_id,
        sender_id=sender_uuid,
        sender_role=sender_role,
        body_ciphertext=enc["ciphertext_b64"],
        enc_nonce_b64=enc["nonce_b64"],
        attachments=metas if metas else None,
    )
    session.add(msg)

    # Update thread preview and last_message_at
    preview_text = body[:120]
    thread.last_message_at = datetime.now(timezone.utc)
    thread.last_preview_encrypted = _encrypt_preview(tid_str, preview_text, master_key)
    session.add(thread)

    await session.commit()
    await session.refresh(msg)

    return MessageCreateResponse(
        id=msg.id,
        thread_id=msg.thread_id,
        sender_id=msg.sender_id,
        sender_role=msg.sender_role,
        body=body,
        attachments=attachment_metas if attachment_metas else None,
        created_at=msg.created_at,
        mocked=True,
    )
