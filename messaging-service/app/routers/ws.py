"""Mocked WS + polling — no Redis, DB is offline queue."""

from __future__ import annotations

import json
import os
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from sqlalchemy import asc, func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import MessagingMessage, MessagingThread
from app.schemas.message import AttachmentMeta, MessageItem, MessagesPageResponse
from app.services.auth import AuthUser, get_current_user, get_current_user_ws, require_member
from app.services.crypto import decrypt_thread_message, encrypt_thread_message

router = APIRouter(prefix="/messages", tags=["ws-poll"])
MAX_LIMIT = 50
DEFAULT_POLL_LIMIT = 20


def _get_engine():
    url = os.environ.get("DATABASE_URL") or "postgresql+psycopg://sih_dnk:changeme@localhost:5433/sih_dnk"
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
    try:
        from storage.config import settings as s  # type: ignore[import-untyped]

        hk = str(s.ENCRYPTION_MASTER_KEY)
        if hk:
            return bytes.fromhex(hk)
    except Exception:
        pass
    hex_env = os.environ.get("ENCRYPTION_MASTER_KEY") or "00" * 32
    return bytes.fromhex(hex_env)


def _encrypt_preview(tid: str, preview: str, mk: bytes) -> str:
    enc = encrypt_thread_message(preview, tid, mk)
    return json.dumps({"ciphertext_b64": enc["ciphertext_b64"], "nonce_b64": enc["nonce_b64"]})


def _attachment_meta_list(raw: object | None) -> list[AttachmentMeta] | None:
    if not isinstance(raw, list):
        return None
    out: list[AttachmentMeta] = []
    for it in raw:
        if isinstance(it, dict):
            fn, ct, sz = it.get("filename"), it.get("content_type"), it.get("size_bytes")
            if isinstance(fn, str) and isinstance(ct, str) and isinstance(sz, int):
                out.append(AttachmentMeta(filename=fn, content_type=ct, size_bytes=sz))
    return out if out else None


@router.get("/ws", tags=["ws-poll"], summary="WebSocket info — documents ws endpoint")
async def ws_info() -> dict[str, object]:
    """Describe the WebSocket endpoint for OpenAPI visibility (real WS is at /messages/ws/threads/{thread_id})."""
    return {
        "mocked": True,
        "ws_endpoint": "/messages/ws/threads/{thread_id}?token=<JWT>",
        "poll_endpoint": "/messages/threads/{thread_id}/poll?since=ISO8601",
        "auth": "Bearer JWT or ?token= query param; sahayak is read-only observer",
    }


@router.get("/threads/{thread_id}/poll", response_model=MessagesPageResponse)
async def poll_messages(
    thread_id: uuid.UUID,
    request: Request,
    session: SessionDep,
    user: UserDep,
    since: str | None = Query(default=None, description="ISO8601 — return created_at > since"),
    limit: int = Query(default=DEFAULT_POLL_LIMIT, ge=1, le=MAX_LIMIT),
) -> MessagesPageResponse:
    _ = request
    await require_member(str(thread_id), user, session)
    since_dt: datetime | None = None
    if since and since.strip():
        try:
            iso = since.replace("Z", "+00:00") if since.endswith("Z") else since
            since_dt = datetime.fromisoformat(iso)
            if since_dt.tzinfo is None:
                since_dt = since_dt.replace(tzinfo=timezone.utc)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid since timestamp (expected ISO8601)") from None
    mk = _master_key()
    filters = [MessagingMessage.thread_id == thread_id]
    if since_dt is not None:
        filters.append(MessagingMessage.created_at > since_dt)  # type: ignore[arg-type]
    total = int((await session.execute(select(func.count()).select_from(MessagingMessage).where(*filters))).scalar_one())
    rows: list[MessagingMessage] = list((await session.execute(select(MessagingMessage).where(*filters).order_by(asc(MessagingMessage.created_at)).limit(limit).offset(0))).scalars().all())
    tid_str = str(thread_id)
    items: list[MessageItem] = []
    for m in rows:
        try:
            body = decrypt_thread_message(m.body_ciphertext, m.enc_nonce_b64, tid_str, mk)
        except Exception:
            body = ""
        items.append(MessageItem(id=m.id, thread_id=m.thread_id, sender_id=m.sender_id, sender_role=m.sender_role, body=body, attachments=_attachment_meta_list(m.attachments), created_at=m.created_at))
    return MessagesPageResponse(items=items, total=total, limit=limit, offset=0, mocked=True)


async def _ws_close(ws: WebSocket, code: int = 1008) -> None:
    try:
        await ws.close(code=code)
    except Exception:
        pass


@router.websocket("/ws/threads/{thread_id}")
async def ws_thread(websocket: WebSocket, thread_id: uuid.UUID) -> None:
    try:
        user: AuthUser = await get_current_user_ws(websocket)
    except Exception:
        await _ws_close(websocket)
        return
    factory = _get_sessionmaker()
    try:
        async with factory() as session:
            try:
                await require_member(str(thread_id), user, session)
            except Exception:
                await _ws_close(websocket)
                return
    except Exception:
        await _ws_close(websocket)
        return
    try:
        await websocket.accept()
        await websocket.send_json({"type": "connected", "thread_id": str(thread_id)})
    except Exception:
        return
    tid_str = str(thread_id)
    while True:
        try:
            text = await websocket.receive_text()
        except (WebSocketDisconnect, Exception):
            break
        try:
            payload = json.loads(text)
        except Exception:
            try:
                await websocket.send_json({"type": "error", "detail": "Invalid JSON"})
            except Exception:
                break
            continue
        if not isinstance(payload, dict) or payload.get("type") != "send":
            try:
                await websocket.send_json({"type": "error", "detail": "Invalid payload"})
            except Exception:
                break
            continue
        body_val = payload.get("body")
        if not isinstance(body_val, str) or not body_val.strip():
            try:
                await websocket.send_json({"type": "error", "detail": "Missing or empty body"})
            except Exception:
                break
            continue
        body: str = body_val
        if user["role"] == "sahayak":
            try:
                await websocket.send_json({"type": "error", "detail": "Sahayak observer cannot send messages"})
            except Exception:
                break
            continue
        attachments_raw = payload.get("attachments")
        metas: list[dict[str, object]] | None = None
        if isinstance(attachments_raw, list):
            tmp: list[dict[str, object]] = []
            for it in attachments_raw:
                if isinstance(it, dict):
                    fn, ct, sz = it.get("filename"), it.get("content_type"), it.get("size_bytes")
                    if isinstance(fn, str) and isinstance(ct, str) and isinstance(sz, int):
                        tmp.append({"filename": fn, "content_type": ct, "size_bytes": sz})
            if tmp:
                metas = tmp
        mk = _master_key()
        enc = encrypt_thread_message(body, tid_str, mk)
        try:
            sender_uuid = uuid.UUID(user["user_id"])
        except ValueError:
            try:
                await websocket.send_json({"type": "error", "detail": "Invalid sender user_id"})
            except Exception:
                break
            continue
        msg_factory = _get_sessionmaker()
        try:
            async with msg_factory() as msg_session:
                thread_res = await msg_session.execute(select(MessagingThread).where(MessagingThread.id == thread_id))
                thread_row = thread_res.scalar_one_or_none()
                if thread_row is None:
                    try:
                        await websocket.send_json({"type": "error", "detail": "Thread not found"})
                    except Exception:
                        break
                    continue
                if user["role"] == "sahayak":
                    try:
                        await websocket.send_json({"type": "error", "detail": "Sahayak observer cannot send messages"})
                    except Exception:
                        break
                    continue
                msg = MessagingMessage(id=uuid.uuid4(), thread_id=thread_id, sender_id=sender_uuid, sender_role=user["role"], body_ciphertext=enc["ciphertext_b64"], enc_nonce_b64=enc["nonce_b64"], attachments=metas)  # type: ignore[arg-type]
                msg_session.add(msg)
                thread_row.last_message_at = datetime.now(timezone.utc)
                thread_row.last_preview_encrypted = _encrypt_preview(tid_str, body[:120], mk)
                msg_session.add(thread_row)
                await msg_session.commit()
                await msg_session.refresh(msg)
                attachment_metas: list[AttachmentMeta] | None = None
                if metas is not None:
                    attachment_metas = [AttachmentMeta(filename=str(d["filename"]), content_type=str(d["content_type"]), size_bytes=int(d["size_bytes"])) for d in metas]  # type: ignore[arg-type]
                data = {"id": str(msg.id), "thread_id": str(msg.thread_id), "sender_id": str(msg.sender_id), "sender_role": msg.sender_role, "body": body, "attachments": [a.model_dump() for a in attachment_metas] if attachment_metas else None, "created_at": msg.created_at.isoformat(), "mocked": True}
                try:
                    await websocket.send_json({"type": "message", "data": data})
                except Exception:
                    break
        except Exception as exc:
            try:
                await websocket.send_json({"type": "error", "detail": f"Failed to persist: {exc}"})
            except Exception:
                break
            continue
