from __future__ import annotations

import json
import os
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import MessagingMessage, MessagingThread, PaymentMock, QuoteState, QuoteVersion
from app.services.auth import get_current_user
from app.services.crypto import encrypt_thread_message
from app.services.quote_state import QuoteStateError, next_state

router = APIRouter(prefix="/payment/mock", tags=["payment-mock"])


def _get_engine():
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        url = "postgresql+psycopg://sih_dnk:changeme@localhost:5433/sih_dnk"
    return create_async_engine(url, pool_pre_ping=True)


def _get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(_get_engine(), expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = _get_sessionmaker()
    async with factory() as session:
        yield session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


def _master_key() -> bytes:
    hex_env = os.environ.get("ENCRYPTION_MASTER_KEY")
    if hex_env is not None and hex_env != "":
        return bytes.fromhex(hex_env)
    try:
        from storage.config import settings as s  # type: ignore[import-untyped]

        hk = str(s.ENCRYPTION_MASTER_KEY)
        if hk:
            return bytes.fromhex(hk)
    except Exception:
        pass
    return bytes.fromhex("00" * 32)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _is_uuid(s: str) -> bool:
    try:
        uuid.UUID(s)
        return True
    except ValueError:
        return False


class PaymentGenerateRequest(BaseModel):
    amount_minor: int = Field(ge=0)
    order_id: uuid.UUID | None = None
    quote_id: uuid.UUID | None = None


class PaymentGenerateResponse(BaseModel):
    payment_link_id: uuid.UUID
    short_url: str
    amount: int
    amount_minor: int
    status: str
    order_id: uuid.UUID | None = None
    quote_id: uuid.UUID | None = None


class PaymentDetailResponse(BaseModel):
    payment_id: uuid.UUID
    quote_id: uuid.UUID | None = None
    order_id: uuid.UUID | None = None
    amount: int
    amount_minor: int
    status: str
    dnk_fees: int = 0
    customs_excluded: bool = True
    created_at: datetime | None = None
    updated_at: datetime | None = None


def _encrypt_preview(tid: str, preview: str, mk: bytes) -> str:
    enc = encrypt_thread_message(preview, tid, mk)
    return json.dumps({"ciphertext_b64": enc["ciphertext_b64"], "nonce_b64": enc["nonce_b64"]})


async def _find_payment_or_quote(payment_id: uuid.UUID, db: AsyncSession) -> tuple[PaymentMock | None, QuoteState | None]:
    pm_res = await db.execute(select(PaymentMock).where(PaymentMock.id == payment_id))
    pm = pm_res.scalar_one_or_none()
    if pm is not None:
        qs = None
        if pm.quote_id is not None:
            qs_res = await db.execute(select(QuoteState).where(QuoteState.quote_id == pm.quote_id))
            qs = qs_res.scalar_one_or_none()
        return pm, qs
    # fallback: payment_id may be quote_id without PaymentMock row (legacy approve)
    qs_res2 = await db.execute(select(QuoteState).where(QuoteState.quote_id == payment_id))
    qs2 = qs_res2.scalar_one_or_none()
    if qs2 is not None:
        return None, qs2
    # also try PaymentMock by quote_id alias
    pm2 = await db.execute(select(PaymentMock).where(PaymentMock.quote_id == payment_id))
    pm_alias = pm2.scalar_one_or_none()
    if pm_alias is not None:
        qs3 = None
        if pm_alias.quote_id is not None:
            qs_res3 = await db.execute(select(QuoteState).where(QuoteState.quote_id == pm_alias.quote_id))
            qs3 = qs_res3.scalar_one_or_none()
        return pm_alias, qs3
    return None, None


@router.post("/generate", response_model=PaymentGenerateResponse, status_code=201)
async def generate_payment(
    body: PaymentGenerateRequest,
    request: Request,
    db: SessionDep,
) -> PaymentGenerateResponse:
    _ = await get_current_user(request)
    now = _utcnow()
    # if quote_id provided, derive order/thread/amount from quote
    quote_id = body.quote_id
    order_id = body.order_id
    amount = body.amount_minor
    thread_id: uuid.UUID | None = None

    if quote_id is not None:
        qs_res = await db.execute(select(QuoteState).where(QuoteState.quote_id == quote_id))
        qs = qs_res.scalar_one_or_none()
        if qs is None:
            raise HTTPException(status_code=404, detail="Quote not found for quote_id")
        order_id = qs.order_id
        thread_id = qs.thread_id
        amount = qs.amount_minor + qs.shipping_minor
    elif order_id is not None:
        # try to find quote by order_id for linking
        qs_res2 = await db.execute(select(QuoteState).where(QuoteState.order_id == order_id))
        qs2 = qs_res2.scalar_one_or_none()
        if qs2 is not None:
            quote_id = qs2.quote_id
            thread_id = qs2.thread_id

    pid = uuid.uuid4()
    pm = PaymentMock(
        id=pid,
        quote_id=quote_id,
        order_id=order_id,
        thread_id=thread_id,
        amount_minor=amount,
        status="initiated",
        created_at=now,
        updated_at=now,
    )
    db.add(pm)
    await db.commit()
    await db.refresh(pm)
    return PaymentGenerateResponse(
        payment_link_id=pm.id,
        short_url=f"/payment/mock/{pm.id}",
        amount=pm.amount_minor,
        amount_minor=pm.amount_minor,
        status=pm.status,
        order_id=pm.order_id,
        quote_id=pm.quote_id,
    )


@router.get("/{payment_id}", response_model=PaymentDetailResponse)
async def get_payment(payment_id: uuid.UUID, request: Request, db: SessionDep) -> PaymentDetailResponse:
    _ = await get_current_user(request)
    pm, qs = await _find_payment_or_quote(payment_id, db)
    if pm is None and qs is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    if pm is not None:
        status = pm.status
        # sync status with quote if quote is paid_held but pm still initiated
        if qs is not None and qs.state == "paid_held" and status != "paid_held":
            status = "paid_held"
        return PaymentDetailResponse(
            payment_id=pm.id,
            quote_id=pm.quote_id,
            order_id=pm.order_id,
            amount=pm.amount_minor,
            amount_minor=pm.amount_minor,
            status=status,
            dnk_fees=0,
            customs_excluded=True,
            created_at=pm.created_at,
            updated_at=pm.updated_at,
        )
    # pm is None but qs exists (approve link without explicit PaymentMock)
    assert qs is not None
    amt = qs.amount_minor + qs.shipping_minor
    st = "paid_held" if qs.state == "paid_held" else "initiated"
    return PaymentDetailResponse(
        payment_id=qs.quote_id,
        quote_id=qs.quote_id,
        order_id=qs.order_id,
        amount=amt,
        amount_minor=amt,
        status=st,
        dnk_fees=0,
        customs_excluded=True,
        created_at=qs.created_at,
        updated_at=qs.updated_at,
    )


@router.post("/{payment_id}/pay", response_model=PaymentDetailResponse)
async def pay_payment(payment_id: uuid.UUID, request: Request, db: SessionDep) -> PaymentDetailResponse:
    user = await get_current_user(request)
    pm, qs = await _find_payment_or_quote(payment_id, db)
    if pm is None and qs is None:
        raise HTTPException(status_code=404, detail="Payment not found")
    now = _utcnow()
    target_pm: PaymentMock | None = pm
    target_qs: QuoteState | None = qs

    if target_pm is not None and target_pm.quote_id is not None and target_qs is None:
        qres = await db.execute(select(QuoteState).where(QuoteState.quote_id == target_pm.quote_id))
        target_qs = qres.scalar_one_or_none()
    if target_pm is None and target_qs is not None:
        # create PaymentMock for this quote if missing (id == quote_id)
        existing = await db.execute(select(PaymentMock).where(PaymentMock.id == target_qs.quote_id))
        if existing.scalar_one_or_none() is None:
            by_quote = await db.execute(select(PaymentMock).where(PaymentMock.quote_id == target_qs.quote_id))
            if by_quote.scalar_one_or_none() is None:
                target_pm = PaymentMock(
                    id=target_qs.quote_id,
                    quote_id=target_qs.quote_id,
                    order_id=target_qs.order_id,
                    thread_id=target_qs.thread_id,
                    amount_minor=target_qs.amount_minor + target_qs.shipping_minor,
                    status="initiated",
                    created_at=now,
                    updated_at=now,
                )
                db.add(target_pm)
                await db.flush()
            else:
                target_pm = by_quote.scalar_one_or_none()
        else:
            target_pm = existing.scalar_one_or_none()

    # idempotent: if already paid_held, return
    current_status = None
    if target_pm is not None:
        current_status = target_pm.status
    elif target_qs is not None:
        current_status = "paid_held" if target_qs.state == "paid_held" else "initiated"
    if current_status == "paid_held":
        if target_pm is not None:
            return PaymentDetailResponse(
                payment_id=target_pm.id,
                quote_id=target_pm.quote_id,
                order_id=target_pm.order_id,
                amount=target_pm.amount_minor,
                amount_minor=target_pm.amount_minor,
                status="paid_held",
                dnk_fees=0,
                customs_excluded=True,
                created_at=target_pm.created_at,
                updated_at=target_pm.updated_at,
            )
        assert target_qs is not None
        amt2 = target_qs.amount_minor + target_qs.shipping_minor
        return PaymentDetailResponse(
            payment_id=target_qs.quote_id,
            quote_id=target_qs.quote_id,
            order_id=target_qs.order_id,
            amount=amt2,
            amount_minor=amt2,
            status="paid_held",
            dnk_fees=0,
            customs_excluded=True,
            created_at=target_qs.created_at,
            updated_at=target_qs.updated_at,
        )

    # transition quote if linked
    if target_qs is not None:
        try:
            ns = next_state(target_qs.state, "pay")  # type: ignore[arg-type]
        except QuoteStateError as e:
            raise HTTPException(status_code=422, detail=str(e)) from None
        target_qs.state = ns
        target_qs.updated_at = now
        target_qs.current_version += 1
        qv = QuoteVersion(
            quote_id=target_qs.quote_id,
            version=target_qs.current_version,
            price_minor=target_qs.amount_minor,
            qty=target_qs.qty,
            shipping_minor=target_qs.shipping_minor,
            status=ns,
            created_by=uuid.UUID(user["user_id"]) if _is_uuid(user["user_id"]) else target_qs.buyer_id,
            reason=None,
            created_at=now,
        )
        db.add(qv)
        db.add(target_qs)

    # mark payment mock paid_held
    if target_pm is not None:
        target_pm.status = "paid_held"
        target_pm.updated_at = now
        db.add(target_pm)

    # system message Payment verified ✓
    thread: MessagingThread | None = None
    thread_id_val: uuid.UUID | None = None
    if target_pm is not None and target_pm.thread_id is not None:
        thread_id_val = target_pm.thread_id
    elif target_pm is not None and target_pm.order_id is not None:
        tr = await db.execute(select(MessagingThread).where(MessagingThread.order_id == target_pm.order_id))
        thread = tr.scalar_one_or_none()
    if thread is None and target_qs is not None:
        if target_qs.thread_id is not None:
            tr2 = await db.execute(select(MessagingThread).where(MessagingThread.id == target_qs.thread_id))
            thread = tr2.scalar_one_or_none()
        if thread is None:
            tr3 = await db.execute(select(MessagingThread).where(MessagingThread.order_id == target_qs.order_id))
            thread = tr3.scalar_one_or_none()
    if thread is None and thread_id_val is not None:
        tr4 = await db.execute(select(MessagingThread).where(MessagingThread.id == thread_id_val))
        thread = tr4.scalar_one_or_none()
    # also try generic order_id lookup for payment without quote
    if thread is None and target_pm is not None and target_pm.order_id is not None:
        tr5 = await db.execute(select(MessagingThread).where(MessagingThread.order_id == target_pm.order_id))
        thread = tr5.scalar_one_or_none()

    if thread is not None:
        mk = _master_key()
        tid_str = str(thread.id)
        amount_val = target_pm.amount_minor if target_pm is not None else (target_qs.amount_minor + target_qs.shipping_minor if target_qs else 0)
        body_plain = f"Payment verified ✓ — {amount_val/100:.2f} INR held. Payment {payment_id} confirmed. DNK fees included, customs excluded."
        enc = encrypt_thread_message(body_plain, tid_str, mk)
        sender_uuid = uuid.UUID(user["user_id"]) if _is_uuid(user["user_id"]) else thread.seller_id
        msg = MessagingMessage(
            id=uuid.uuid4(),
            thread_id=thread.id,
            sender_id=sender_uuid,
            sender_role="system",
            body_ciphertext=enc["ciphertext_b64"],
            enc_nonce_b64=enc["nonce_b64"],
            attachments=None,
        )
        db.add(msg)
        thread.last_message_at = now
        thread.last_preview_encrypted = _encrypt_preview(tid_str, body_plain[:120], mk)
        db.add(thread)

    await db.commit()
    if target_pm is not None:
        await db.refresh(target_pm)
        return PaymentDetailResponse(
            payment_id=target_pm.id,
            quote_id=target_pm.quote_id,
            order_id=target_pm.order_id,
            amount=target_pm.amount_minor,
            amount_minor=target_pm.amount_minor,
            status=target_pm.status,
            dnk_fees=0,
            customs_excluded=True,
            created_at=target_pm.created_at,
            updated_at=target_pm.updated_at,
        )
    assert target_qs is not None
    await db.refresh(target_qs)
    amt3 = target_qs.amount_minor + target_qs.shipping_minor
    return PaymentDetailResponse(
        payment_id=target_qs.quote_id,
        quote_id=target_qs.quote_id,
        order_id=target_qs.order_id,
        amount=amt3,
        amount_minor=amt3,
        status="paid_held" if target_qs.state == "paid_held" else target_qs.state,
        dnk_fees=0,
        customs_excluded=True,
        created_at=target_qs.created_at,
        updated_at=target_qs.updated_at,
    )
