"""Idempotent demo seed for messaging-service — threads, encrypted messages, quote lifecycle.

Creates (if absent):
  - One demo thread (order_id = deterministic or random on first run) with
    seller 11111111-1111-1111-1111-111111111111 and buyer 22222222-2222-2222-2222-222222222222
  - Sahayak observer 33333333-3333-3333-3333-333333333333 is referenced for JWT mocking
  - Two encrypted messages (seller hello, buyer reply) in that thread
  - One quote lifecycle: sent (v1) -> counter (reject v2) -> sent (revise v3) -> approved (v4) -> paid_held (v5)

All writes are idempotent — re-running prints existing ids without duplicates.

Usage:
  uv run python scripts/seed_demo.py
  DATABASE_URL=postgresql+psycopg://... uv run python scripts/seed_demo.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Ensure repo root + service root on path for `app.*` imports
SERVICE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = SERVICE_DIR.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(SERVICE_DIR))

try:
    from dotenv import load_dotenv  # noqa: E402

    load_dotenv(REPO_ROOT / ".env")
except Exception:
    pass

from sqlalchemy import select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # noqa: E402

from app.models import MessagingMessage, MessagingThread, QuoteState, QuoteVersion  # noqa: E402
from app.services.crypto import encrypt_thread_message  # noqa: E402

# ---------------------------------------------------------------------------
# Demo identity constants — mocked JWT subjects, not auth DB rows
# ---------------------------------------------------------------------------
SELLER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
BUYER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
SAHAYAK_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")

# Deterministic demo order_id so the seed is idempotent across runs.
# Derived via UUID5 from a fixed namespace + name so it is stable yet a valid UUID.
DEMO_ORDER_ID = uuid.uuid5(uuid.NAMESPACE_DNS, "sih-dnk-demo-order-v1")

SELLER_HELLO = "Hello, I have a quote ready for your inquiry."
BUYER_REPLY = "Thanks! Please revise the shipping cost, then I can approve."

# Quote amounts (minor units, INR)
V1_PRICE = 10000
V1_SHIPPING = 500
V2_REVISE_PRICE = 9000
V2_REVISE_SHIPPING = 400


def _database_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if url:
        return url
    # fallback for local dev
    return "postgresql+psycopg://sih_dnk:changeme@localhost:5433/sih_dnk"


def _master_key() -> bytes:
    # Try storage.config first, then env, then env.example fallback
    try:
        from storage.config import settings as s  # type: ignore[import-untyped]

        hex_key: str = str(s.ENCRYPTION_MASTER_KEY)
        if hex_key:
            return bytes.fromhex(hex_key)
    except Exception:
        pass
    hex_env: str | None = os.environ.get("ENCRYPTION_MASTER_KEY")
    if hex_env is None or hex_env == "":
        # dev fallback — 32 zero bytes hex
        hex_env = "00" * 32
    return bytes.fromhex(hex_env)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


async def _ensure_thread(session: AsyncSession) -> MessagingThread:
    """Fetch existing demo thread or create one idempotently."""
    # Idempotency key: the deterministic DEMO_ORDER_ID
    result = await session.execute(
        select(MessagingThread).where(MessagingThread.order_id == DEMO_ORDER_ID)
    )
    existing: MessagingThread | None = result.scalar_one_or_none()
    if existing is not None:
        return existing

    # Also guard on seller+buyer combo in case order_id was randomised previously
    # (legacy): if any thread with seller 1111 buyer 2222 exists, reuse it.
    alt = await session.execute(
        select(MessagingThread).where(
            MessagingThread.seller_id == SELLER_ID,
            MessagingThread.buyer_id == BUYER_ID,
        )
    )
    alt_existing: MessagingThread | None = alt.scalar_one_or_none()
    if alt_existing is not None:
        return alt_existing

    thread = MessagingThread(
        id=uuid.uuid4(),
        order_id=DEMO_ORDER_ID,
        seller_id=SELLER_ID,
        buyer_id=BUYER_ID,
    )
    session.add(thread)
    await session.flush()
    # Ensure the row is persisted before callers use thread.id for encryption
    await session.refresh(thread)
    return thread


async def _ensure_messages(
    session: AsyncSession, thread: MessagingThread, master_key: bytes
) -> list[MessagingMessage]:
    """Create two encrypted messages if absent; return messages in chronological order."""
    result = await session.execute(
        select(MessagingMessage)
        .where(MessagingMessage.thread_id == thread.id)
        .order_by(MessagingMessage.created_at)
    )
    existing: list[MessagingMessage] = list(result.scalars().all())
    if len(existing) >= 2:
        return existing[:2]

    tid_str = str(thread.id)
    # If exactly one exists, only create the missing second one
    if len(existing) == 1:
        enc = encrypt_thread_message(BUYER_REPLY, tid_str, master_key)
        msg = MessagingMessage(
            id=uuid.uuid4(),
            thread_id=thread.id,
            sender_id=BUYER_ID,
            sender_role="buyer",
            body_ciphertext=enc["ciphertext_b64"],
            enc_nonce_b64=enc["nonce_b64"],
            attachments=None,
        )
        session.add(msg)
        thread.last_message_at = _utcnow()
        thread.last_preview_encrypted = json.dumps(
            {"ciphertext_b64": enc["ciphertext_b64"][:0] or enc["ciphertext_b64"], "nonce_b64": enc["nonce_b64"]}
        )
        # Proper preview encryption
        preview_enc = encrypt_thread_message(BUYER_REPLY[:120], tid_str, master_key)
        thread.last_preview_encrypted = json.dumps(
            {"ciphertext_b64": preview_enc["ciphertext_b64"], "nonce_b64": preview_enc["nonce_b64"]}
        )
        session.add(thread)
        await session.flush()
        await session.refresh(msg)
        return [existing[0], msg]

    # Zero existing — create both
    enc1 = encrypt_thread_message(SELLER_HELLO, tid_str, master_key)
    msg1 = MessagingMessage(
        id=uuid.uuid4(),
        thread_id=thread.id,
        sender_id=SELLER_ID,
        sender_role="seller",
        body_ciphertext=enc1["ciphertext_b64"],
        enc_nonce_b64=enc1["nonce_b64"],
        attachments=None,
        created_at=_utcnow(),
    )
    session.add(msg1)

    enc2 = encrypt_thread_message(BUYER_REPLY, tid_str, master_key)
    msg2 = MessagingMessage(
        id=uuid.uuid4(),
        thread_id=thread.id,
        sender_id=BUYER_ID,
        sender_role="buyer",
        body_ciphertext=enc2["ciphertext_b64"],
        enc_nonce_b64=enc2["nonce_b64"],
        attachments=None,
        created_at=_utcnow(),
    )
    session.add(msg2)

    # Update thread preview to buyer reply
    preview_enc2 = encrypt_thread_message(BUYER_REPLY[:120], tid_str, master_key)
    thread.last_message_at = _utcnow()
    thread.last_preview_encrypted = json.dumps(
        {"ciphertext_b64": preview_enc2["ciphertext_b64"], "nonce_b64": preview_enc2["nonce_b64"]}
    )
    session.add(thread)
    await session.flush()
    # Refresh to get server defaults
    await session.refresh(msg1)
    await session.refresh(msg2)
    return [msg1, msg2]


async def _ensure_quote(session: AsyncSession, order_id: uuid.UUID) -> QuoteState:
    """Create or return existing quote covering the demo lifecycle.

    Target lifecycle (mocked, no payment gateway):
      v1 sent (create) -> v2 counter (buyer reject) -> v3 sent (seller revise)
      -> v4 approved (buyer approve) -> v5 paid_held (mock-pay)

    Idempotent: if a quote already exists for this order_id, return it.
    """
    result = await session.execute(select(QuoteState).where(QuoteState.order_id == order_id))
    existing: QuoteState | None = result.scalar_one_or_none()
    if existing is not None:
        return existing

    quote_id = uuid.uuid4()
    now = _utcnow()

    # Current state is terminal paid_held after full flow; we insert versions for each step.
    # To keep history honest, we create QuoteState at paid_held with current_version=5
    # and insert immutable QuoteVersion rows for v1..v5.
    qs = QuoteState(
        quote_id=quote_id,
        order_id=order_id,
        thread_id=order_id,
        seller_id=SELLER_ID,
        buyer_id=BUYER_ID,
        current_version=5,
        state="paid_held",
        amount_minor=V2_REVISE_PRICE,
        currency="INR",
        qty=2,
        shipping_minor=V2_REVISE_SHIPPING,
        created_at=now,
        updated_at=now,
    )
    session.add(qs)

    # v1 sent — seller creates
    v1 = QuoteVersion(
        quote_id=quote_id,
        version=1,
        price_minor=V1_PRICE,
        qty=2,
        shipping_minor=V1_SHIPPING,
        status="sent",
        created_by=SELLER_ID,
        reason="initial quote",
        created_at=now,
    )
    # v2 counter — buyer reject
    v2 = QuoteVersion(
        quote_id=quote_id,
        version=2,
        price_minor=V1_PRICE,
        qty=2,
        shipping_minor=V1_SHIPPING,
        status="counter",
        created_by=BUYER_ID,
        reason="shipping too high, please revise",
        created_at=now,
    )
    # v3 sent — seller revise
    v3 = QuoteVersion(
        quote_id=quote_id,
        version=3,
        price_minor=V2_REVISE_PRICE,
        qty=2,
        shipping_minor=V2_REVISE_SHIPPING,
        status="sent",
        created_by=SELLER_ID,
        reason=None,
        created_at=now,
    )
    # v4 approved — buyer approve
    v4 = QuoteVersion(
        quote_id=quote_id,
        version=4,
        price_minor=V2_REVISE_PRICE,
        qty=2,
        shipping_minor=V2_REVISE_SHIPPING,
        status="approved",
        created_by=BUYER_ID,
        reason=None,
        created_at=now,
    )
    # v5 paid_held — mock-pay
    v5 = QuoteVersion(
        quote_id=quote_id,
        version=5,
        price_minor=V2_REVISE_PRICE,
        qty=2,
        shipping_minor=V2_REVISE_SHIPPING,
        status="paid_held",
        created_by=BUYER_ID,
        reason=None,
        created_at=now,
    )
    session.add_all([v1, v2, v3, v4, v5])
    await session.flush()
    await session.refresh(qs)
    return qs


async def main() -> None:
    url = _database_url()
    master_key = _master_key()
    engine = create_async_engine(url, pool_pre_ping=True)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as session:
        thread = await _ensure_thread(session)
        messages = await _ensure_messages(session, thread, master_key)
        quote = await _ensure_quote(session, thread.order_id)
        await session.commit()
        # Re-fetch to print stable ids
        await session.refresh(thread)
        await session.refresh(quote)

        # Gather versions for printing
        vres = await session.execute(
            select(QuoteVersion).where(QuoteVersion.quote_id == quote.quote_id).order_by(QuoteVersion.version)
        )
        versions: list[QuoteVersion] = list(vres.scalars().all())

        print("=== messaging-service seed_demo (idempotent) ===")
        print(f"seller_id : {SELLER_ID}  (mock JWT sub, role=seller)")
        print(f"buyer_id  : {BUYER_ID}  (mock JWT sub, role=buyer)")
        print(f"sahayak_id: {SAHAYAK_ID}  (mock JWT sub, role=sahayak, read-only observer)")
        print(f"order_id  : {thread.order_id}")
        print(f"thread_id : {thread.id}")
        print(f"messages  : {len(messages)} (encrypted per-thread AES-GCM)")
        for m in messages:
            print(f"  - {m.id} sender={m.sender_role} ({m.sender_id})")
        print(f"quote_id  : {quote.quote_id}")
        print(f"quote_state: {quote.state} v{quote.current_version} amount={quote.amount_minor} shipping={quote.shipping_minor}")
        print(f"quote_versions: {len(versions)}")
        for v in versions:
            print(f"  v{v.version} {v.status} price={v.price_minor} ship={v.shipping_minor} by={v.created_by} reason={v.reason!r}")
        print(f"thread last_preview_encrypted: {'set' if thread.last_preview_encrypted else 'null'}")
        print("Flow: seller creates v1 sent -> buyer reject counter -> seller revise v2 sent -> buyer approve -> mock-pay paid_held (mocked)")
        print("Done. Re-run is safe — existing rows are reused.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
