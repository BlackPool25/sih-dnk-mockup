"""Quote lifecycle router — prefix /quotes, full guards, versioned history."""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import QuoteState, QuoteVersion
from app.schemas.quote import (
    MockPaymentOut,
    QuoteCreateRequest,
    QuoteDetailOut,
    QuoteRejectRequest,
    QuoteReviseRequest,
    QuoteStateOut,
    QuoteVersionOut,
)
from app.services.auth import AuthUser, get_current_user
from app.services.quote_state import QuoteStateError, QuoteStateLiteral, next_state

router = APIRouter(prefix="/quotes", tags=["quotes"])

# --- DB dependency (in-process, no external storage import required) ---


def _get_engine():
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        url = "postgresql+psycopg://sih_dnk:changeme@localhost:5433/sih_dnk"
    return create_async_engine(url, pool_pre_ping=True)


def _get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(_get_engine(), expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = _get_sessionmaker()
    async with factory() as session:
        yield session


# --- Role helpers — exhaustive match ---


def _require_role(user: AuthUser, required: str) -> None:
    match user["role"]:
        case "seller" if required == "seller":
            return
        case "buyer" if required == "buyer":
            return
        case "seller" | "buyer" | "sahayak" | _:
            raise HTTPException(status_code=403, detail=f"Role '{user['role']}' not allowed — requires {required}")


def _is_member_of_quote(user: AuthUser, qs: QuoteState) -> bool:
    match user["role"]:
        case "sahayak":
            return True
        case _:
            uid = user["user_id"]
            return uid == str(qs.seller_id) or uid == str(qs.buyer_id)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# --- Helpers ---


async def _get_quote_or_404(quote_id: uuid.UUID, db: AsyncSession) -> QuoteState:
    result = await db.execute(select(QuoteState).where(QuoteState.quote_id == quote_id))
    qs = result.scalar_one_or_none()
    if qs is None:
        raise HTTPException(status_code=404, detail="Quote not found")
    return qs


async def _get_versions(quote_id: uuid.UUID, db: AsyncSession) -> list[QuoteVersion]:
    result = await db.execute(
        select(QuoteVersion).where(QuoteVersion.quote_id == quote_id).order_by(QuoteVersion.version)
    )
    return list(result.scalars().all())


def _mock_payment_link(quote_id: uuid.UUID, amount_minor: int) -> MockPaymentOut:
    return MockPaymentOut(
        mocked=True,
        payment_link=f"https://pay.mock/quote/{quote_id}?amount={amount_minor}",
        quote_id=quote_id,
        amount_minor=amount_minor,
    )


# --- Routes ---


@router.post("", response_model=QuoteDetailOut, status_code=201)
async def create_quote(
    body: QuoteCreateRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> QuoteDetailOut:
    user = await get_current_user(request)
    _require_role(user, "seller")

    existing = await db.execute(select(QuoteState).where(QuoteState.order_id == body.order_id))
    if existing.scalar_one_or_none() is not None:
        raise HTTPException(status_code=409, detail="Quote already exists for this order_id")

    seller_uuid = uuid.UUID(user["user_id"])
    buyer_id_str = request.headers.get("X-Buyer-Id") or request.query_params.get("buyer_id")
    if buyer_id_str:
        try:
            buyer_uuid = uuid.UUID(buyer_id_str)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid buyer_id") from None
    else:
        buyer_uuid = uuid.uuid4()

    quote_id = uuid.uuid4()
    now = _utcnow()
    qs = QuoteState(
        quote_id=quote_id,
        order_id=body.order_id,
        thread_id=body.thread_id or body.order_id,
        seller_id=seller_uuid,
        buyer_id=buyer_uuid,
        current_version=1,
        state="sent",
        amount_minor=body.price_minor,
        currency="INR",
        qty=body.qty,
        shipping_minor=body.shipping_minor,
        created_at=now,
        updated_at=now,
    )
    db.add(qs)
    qv = QuoteVersion(
        quote_id=quote_id,
        version=1,
        price_minor=body.price_minor,
        qty=body.qty,
        shipping_minor=body.shipping_minor,
        status="sent",
        created_by=seller_uuid,
        reason=body.notes,
        created_at=now,
    )
    db.add(qv)
    await db.commit()
    await db.refresh(qs)
    versions = await _get_versions(quote_id, db)
    return QuoteDetailOut(
        current=QuoteStateOut.model_validate(qs),
        versions=[QuoteVersionOut.model_validate(v) for v in versions],
    )


@router.get("/by-order/{order_id}", response_model=list[QuoteStateOut])
async def list_by_order(
    order_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> list[QuoteStateOut]:
    user = await get_current_user(request)
    result = await db.execute(select(QuoteState).where(QuoteState.order_id == order_id))
    quotes = list(result.scalars().all())
    visible: list[QuoteStateOut] = []
    for qs in quotes:
        if _is_member_of_quote(user, qs):
            visible.append(QuoteStateOut.model_validate(qs))
    if not visible and quotes:
        raise HTTPException(status_code=403, detail="Not a member of this quote")
    return visible


@router.get("/{quote_id}", response_model=QuoteDetailOut)
async def get_quote(
    quote_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> QuoteDetailOut:
    user = await get_current_user(request)
    qs = await _get_quote_or_404(quote_id, db)
    if not _is_member_of_quote(user, qs):
        raise HTTPException(status_code=403, detail="Not a member of this quote")
    versions = await _get_versions(quote_id, db)
    return QuoteDetailOut(
        current=QuoteStateOut.model_validate(qs),
        versions=[QuoteVersionOut.model_validate(v) for v in versions],
    )


@router.post("/{quote_id}/approve", response_model=dict[str, object])
async def approve_quote(
    quote_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, object]:
    user = await get_current_user(request)
    _require_role(user, "buyer")
    qs = await _get_quote_or_404(quote_id, db)
    if str(qs.buyer_id) != user["user_id"]:
        raise HTTPException(status_code=403, detail="Only the buyer of this quote can approve")
    try:
        ns: QuoteStateLiteral = next_state(qs.state, "approve")  # type: ignore[arg-type]
    except QuoteStateError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None

    now = _utcnow()
    qs.state = ns
    qs.updated_at = now
    new_ver = qs.current_version + 1
    qs.current_version = new_ver
    qv = QuoteVersion(
        quote_id=quote_id,
        version=new_ver,
        price_minor=qs.amount_minor,
        qty=qs.qty,
        shipping_minor=qs.shipping_minor,
        status=ns,
        created_by=uuid.UUID(user["user_id"]),
        reason=None,
        created_at=now,
    )
    db.add(qv)
    await db.commit()
    await db.refresh(qs)
    payment = _mock_payment_link(quote_id, qs.amount_minor + qs.shipping_minor)
    return {
        "current": QuoteStateOut.model_validate(qs).model_dump(mode="json"),
        "payment": payment.model_dump(mode="json"),
        "mocked": True,
        "payment_link": payment.payment_link,
    }


@router.post("/{quote_id}/reject", response_model=QuoteDetailOut)
async def reject_quote(
    quote_id: uuid.UUID,
    body: QuoteRejectRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> QuoteDetailOut:
    user = await get_current_user(request)
    _require_role(user, "buyer")
    qs = await _get_quote_or_404(quote_id, db)
    if str(qs.buyer_id) != user["user_id"]:
        raise HTTPException(status_code=403, detail="Only the buyer can reject")
    try:
        ns: QuoteStateLiteral = next_state(qs.state, "reject")  # type: ignore[arg-type]
    except QuoteStateError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None

    now = _utcnow()
    qs.state = ns
    qs.updated_at = now
    new_ver = qs.current_version + 1
    qs.current_version = new_ver
    qv = QuoteVersion(
        quote_id=quote_id,
        version=new_ver,
        price_minor=qs.amount_minor,
        qty=qs.qty,
        shipping_minor=qs.shipping_minor,
        status=ns,
        created_by=uuid.UUID(user["user_id"]),
        reason=body.reason,
        created_at=now,
    )
    db.add(qv)
    await db.commit()
    await db.refresh(qs)
    versions = await _get_versions(quote_id, db)
    return QuoteDetailOut(
        current=QuoteStateOut.model_validate(qs),
        versions=[QuoteVersionOut.model_validate(v) for v in versions],
    )


@router.post("/{quote_id}/revise", response_model=QuoteDetailOut)
async def revise_quote(
    quote_id: uuid.UUID,
    body: QuoteReviseRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> QuoteDetailOut:
    user = await get_current_user(request)
    _require_role(user, "seller")
    qs = await _get_quote_or_404(quote_id, db)
    if str(qs.seller_id) != user["user_id"]:
        raise HTTPException(status_code=403, detail="Only the seller of this quote can revise")
    try:
        ns: QuoteStateLiteral = next_state(qs.state, "revise")  # type: ignore[arg-type]
    except QuoteStateError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None

    now = _utcnow()
    qs.state = ns
    qs.amount_minor = body.price_minor
    qs.qty = body.qty
    qs.shipping_minor = body.shipping_minor
    qs.updated_at = now
    new_ver = qs.current_version + 1
    qs.current_version = new_ver
    qv = QuoteVersion(
        quote_id=quote_id,
        version=new_ver,
        price_minor=body.price_minor,
        qty=body.qty,
        shipping_minor=body.shipping_minor,
        status=ns,
        created_by=uuid.UUID(user["user_id"]),
        reason=None,
        created_at=now,
    )
    db.add(qv)
    await db.commit()
    await db.refresh(qs)
    versions = await _get_versions(quote_id, db)
    return QuoteDetailOut(
        current=QuoteStateOut.model_validate(qs),
        versions=[QuoteVersionOut.model_validate(v) for v in versions],
    )


@router.post("/{quote_id}/mock-pay", response_model=QuoteDetailOut)
async def mock_pay(
    quote_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> QuoteDetailOut:
    user = await get_current_user(request)
    qs = await _get_quote_or_404(quote_id, db)
    if not _is_member_of_quote(user, qs):
        raise HTTPException(status_code=403, detail="Not a member of this quote")
    try:
        ns: QuoteStateLiteral = next_state(qs.state, "pay")  # type: ignore[arg-type]
    except QuoteStateError as e:
        raise HTTPException(status_code=422, detail=str(e)) from None

    now = _utcnow()
    qs.state = ns
    qs.updated_at = now
    new_ver = qs.current_version + 1
    qs.current_version = new_ver
    qv = QuoteVersion(
        quote_id=quote_id,
        version=new_ver,
        price_minor=qs.amount_minor,
        qty=qs.qty,
        shipping_minor=qs.shipping_minor,
        status=ns,
        created_by=uuid.UUID(user["user_id"]),
        reason=None,
        created_at=now,
    )
    db.add(qv)
    await db.commit()
    await db.refresh(qs)
    versions = await _get_versions(quote_id, db)
    return QuoteDetailOut(
        current=QuoteStateOut.model_validate(qs),
        versions=[QuoteVersionOut.model_validate(v) for v in versions],
    )


@router.post("/{quote_id}/webhook", response_model=QuoteDetailOut)
async def webhook_pay(
    quote_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> QuoteDetailOut:
    """Optional webhook — same as mock-pay."""
    return await mock_pay(quote_id, request, db)
