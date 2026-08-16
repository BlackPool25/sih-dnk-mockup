"""Backend-core CLI — key rotation and demo-data seeding.

Usage::

    python -m backend-core.cli rotate-keys [--dry-run]
    python -m backend-core.cli seed-demo

Subcommands
-----------

rotate-keys
    Re-encrypt all encrypted database fields with a new master key.

    Requires two environment variables:

    - ``ENCRYPTION_MASTER_KEY`` — the **current** (old) 64-char hex key.
    - ``NEW_ENCRYPTION_MASTER_KEY`` — the **new** 64-char hex key to rotate to.

    The script:
    1. Prints a backup warning and exits immediately if confirmation is declined
       (unless ``--dry-run`` is passed).
    2. Iterates every row in ``SellerProfile``, ``ProfileDocument``, and ``Order``
       that carries encrypted fields.
    3. Decrypts each field with the **old** key (using ``key_version`` embedded in
       the stored ciphertext), re-encrypts with the **new** key (bumped
       ``key_version``), and updates the row.
    4. In dry-run mode only reports counts — no writes are performed.

seed-demo
    Pre-seed a complete demo scenario (idempotent).

    Reads credentials from ``storage.config.settings`` (``DEMO_SELLER_*`` /
    ``DEMO_BUYER_*`` env vars or ``.env``).  Creates:

    - Seller ``sunita@handicrafts.in`` + full profile (PAN encrypted, IEC,
      SBI bank, AD code encrypted, Kanchipuram address)
    - Buyer ``weber@example.com``
    - Order: 5 silk sarees → Chicago, ₹10 000, profile auto-filled,
      status ``qr_generated``
    - DocPack: CI, PL, CN, PBE
    - QR code PNG
    - Placeholder profile documents (encrypted)
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
import json
import logging
import os
import sys
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

# In production, PYTHONPATH=/opt makes auth/ and storage/ importable.
# For local dev, add the monorepo root — same pattern as tests/conftest.py.
_PROJECT_ROOT = str(Path(__file__).resolve().parent.parent.parent.parent)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import jwt
import qrcode
from sqlalchemy import Column, Table, select
from sqlalchemy.dialects.postgresql import UUID

from app.models import Base as CoreBase
from app.models import DocPack, Order, OrderStatus, ProfileDocument, SellerProfile
from storage.config import settings
from storage.crypto import DecryptionError, decrypt_field, encrypt_field
from storage.db import get_session

# Register the 'users' table from auth's DeclarativeBase into app.models.Base
# so that ForeignKey('users.id') on SellerProfile/Order resolves correctly.
Table(
    "users",
    CoreBase.metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    extend_existing=True,
)

logger = logging.getLogger("backend-core.key-rotation")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# SellerProfile encrypted fields (JSONB columns)
_PROFILE_ENCRYPTED_FIELDS: list[str] = [
    "pan_encrypted",
    "bank_account_encrypted",
    "ad_code_encrypted",
    "gstin_encrypted",
]

# Order encrypted fields (JSONB columns)
_ORDER_ENCRYPTED_FIELDS: list[str] = [
    "ad_code_encrypted",
    "bank_account_encrypted",
]

# Sub-keys inside Order.profile_snapshot_encrypted that may be encrypted dicts
_SNAPSHOT_ENCRYPTED_KEYS: list[str] = [
    "pan_encrypted",
    "bank_account_encrypted",
    "ad_code_encrypted",
    "gstin_encrypted",
]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _looks_encrypted(value: object) -> bool:
    """Return True when *value* is a dict carrying ``ciphertext_b64``."""
    return isinstance(value, dict) and "ciphertext_b64" in value


def _re_encrypt(
    encrypted_value: dict,
    user_uuid: str,
    old_key: bytes,
    new_key: bytes,
    new_key_version: int,
) -> dict:
    """Decrypt with *old_key*, then encrypt with *new_key* at *new_key_version*.

    Returns the new encrypted dict.  Raises ``DecryptionError`` on GCM failure.
    """
    plaintext: str = decrypt_field(encrypted_value, user_uuid, old_key)
    return encrypt_field(plaintext, user_uuid, new_key, new_key_version)


def _rotate_snapshot(
    snapshot: dict,
    user_uuid: str,
    old_key: bytes,
    new_key: bytes,
    new_key_version: int,
) -> dict:
    """Rotate every encrypted sub-field inside a profile snapshot dict.

    Non-encrypted keys (e.g. ``firm_name``, ``address_line1``) are left alone.
    """
    for key in _SNAPSHOT_ENCRYPTED_KEYS:
        value = snapshot.get(key)
        if not _looks_encrypted(value):
            continue
        snapshot[key] = _re_encrypt(value, user_uuid, old_key, new_key, new_key_version)
    return snapshot


def _validate_hex_key(env_var: str, value: str) -> bytes:
    """Validate a 64-char hex key and return its bytes form."""
    if len(value) != 64:
        raise SystemExit(
            f"{env_var} must be exactly 64 hex characters, got {len(value)}"
        )
    if not all(c in "0123456789abcdefABCDEF" for c in value):
        raise SystemExit(f"{env_var} must contain only hex characters")
    return bytes.fromhex(value)


# ---------------------------------------------------------------------------
# Core rotation logic
# ---------------------------------------------------------------------------


async def _rotate_profiles(
    old_key: bytes,
    new_key: bytes,
    new_version: int,
    *,
    dry_run: bool,
) -> int:
    """Rotate encrypted fields on every SellerProfile row.  Returns count."""
    count = 0

    async with get_session()() as session:
        result = await session.execute(select(SellerProfile))
        profiles: list[SellerProfile] = list((await result.scalars()).all())

    for profile in profiles:
        user_uuid = str(profile.user_id)
        row_touched = False

        for field_name in _PROFILE_ENCRYPTED_FIELDS:
            encrypted = getattr(profile, field_name)
            if not _looks_encrypted(encrypted):
                continue
            try:
                new_encrypted = _re_encrypt(
                    encrypted, user_uuid, old_key, new_key, new_version
                )
            except DecryptionError:
                logger.error(
                    "Decryption failed for SellerProfile %s field %s — skipping",
                    profile.id,
                    field_name,
                )
                continue
            setattr(profile, field_name, new_encrypted)
            row_touched = True

        if row_touched:
            count += 1
            logger.debug("Rotated SellerProfile %s (user %s)", profile.id, user_uuid)
            if not dry_run:
                async with get_session()() as session:
                    await session.merge(profile)
                    await session.commit()

    return count


async def _rotate_documents(
    old_key: bytes,
    new_key: bytes,
    new_version: int,
    *,
    dry_run: bool,
) -> int:
    """Rotate encrypted_content on every ProfileDocument row.  Returns count.

    The user_uuid for key derivation comes from the parent SellerProfile.
    """
    count = 0

    async with get_session()() as session:
        result = await session.execute(
            select(ProfileDocument).join(
                SellerProfile,
                ProfileDocument.profile_id == SellerProfile.id,
            )
        )
        rows = list((await result.scalars()).all())

    for doc in rows:
        if not _looks_encrypted(doc.encrypted_content):
            continue

        # Re-fetch to get profile.user_id (the join above loaded it)
        try:
            user_uuid = str(doc.profile.user_id)
        except AttributeError:
            logger.error("ProfileDocument %s has no parent profile — skipping", doc.id)
            continue

        try:
            new_encrypted = _re_encrypt(
                doc.encrypted_content, user_uuid, old_key, new_key, new_version
            )
        except DecryptionError:
            logger.error("Decryption failed for ProfileDocument %s — skipping", doc.id)
            continue

        doc.encrypted_content = new_encrypted
        count += 1
        logger.debug("Rotated ProfileDocument %s", doc.id)

        if not dry_run:
            async with get_session()() as session:
                await session.merge(doc)
                await session.commit()

    return count


async def _rotate_orders(
    old_key: bytes,
    new_key: bytes,
    new_version: int,
    *,
    dry_run: bool,
) -> int:
    """Rotate encrypted fields on every Order row.  Returns count."""
    count = 0

    async with get_session()() as session:
        result = await session.execute(select(Order))
        orders: list[Order] = list((await result.scalars()).all())

    for order in orders:
        user_uuid = str(order.seller_id)
        row_touched = False

        # 1. Direct encrypted fields
        for field_name in _ORDER_ENCRYPTED_FIELDS:
            encrypted = getattr(order, field_name)
            if not _looks_encrypted(encrypted):
                continue
            try:
                new_encrypted = _re_encrypt(
                    encrypted, user_uuid, old_key, new_key, new_version
                )
            except DecryptionError:
                logger.error(
                    "Decryption failed for Order %s field %s — skipping",
                    order.id,
                    field_name,
                )
                continue
            setattr(order, field_name, new_encrypted)
            row_touched = True

        # 2. Profile snapshot sub-fields
        snapshot = order.profile_snapshot_encrypted
        if isinstance(snapshot, dict):
            try:
                _rotate_snapshot(snapshot, user_uuid, old_key, new_key, new_version)
            except DecryptionError:
                logger.error(
                    "Decryption failed for Order %s profile_snapshot — skipping",
                    order.id,
                )
                continue
            order.profile_snapshot_encrypted = snapshot
            row_touched = True

        if row_touched:
            count += 1
            logger.debug("Rotated Order %s (seller %s)", order.id, user_uuid)
            if not dry_run:
                async with get_session()() as session:
                    await session.merge(order)
                    await session.commit()

    return count


# ---------------------------------------------------------------------------
# seed-demo subcommand
# ---------------------------------------------------------------------------

_QR_DIR = Path("qr_codes")
_KEY_VERSION = 1

# Tiny 1×1 white PNG (67 bytes) for placeholder profile documents
_PLACEHOLDER_PNG_BYTES = bytes(
    [
        0x89,
        0x50,
        0x4E,
        0x47,
        0x0D,
        0x0A,
        0x1A,
        0x0A,
        0x00,
        0x00,
        0x00,
        0x0D,
        0x49,
        0x48,
        0x44,
        0x52,
        0x00,
        0x00,
        0x00,
        0x01,
        0x00,
        0x00,
        0x00,
        0x01,
        0x08,
        0x02,
        0x00,
        0x00,
        0x00,
        0x90,
        0x77,
        0x53,
        0xDE,
        0x00,
        0x00,
        0x00,
        0x0C,
        0x49,
        0x44,
        0x41,
        0x54,
        0x08,
        0xD7,
        0x63,
        0xF8,
        0xCF,
        0xC0,
        0x00,
        0x00,
        0x01,
        0x01,
        0x00,
        0x05,
        0x18,
        0xD8,
        0x4D,
        0x60,
        0x00,
        0x00,
        0x00,
        0x00,
        0x49,
        0x45,
        0x4E,
        0x44,
        0xAE,
        0x42,
        0x60,
        0x82,
    ]
)


def _mk_key() -> bytes:
    return bytes.fromhex(settings.ENCRYPTION_MASTER_KEY)


def _encrypted_placeholder(user_uuid: str) -> dict:
    b64 = base64.b64encode(_PLACEHOLDER_PNG_BYTES).decode("ascii")
    return encrypt_field(b64, user_uuid, _mk_key(), _KEY_VERSION)


def _checksum_placeholder() -> str:
    return hashlib.sha256(_PLACEHOLDER_PNG_BYTES).hexdigest()


async def _ensure_user(email: str, password: str, role_str: str) -> uuid.UUID:
    """Create a user if not present; return the user_id.  Idempotent."""
    from auth.models.user import User, UserRole
    from auth.services.password import hash_password

    role = UserRole(role_str)
    async with get_session()() as session:
        result = await session.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()
        if existing is not None:
            print(f"  User already exists: {email}")
            return existing.id

        user = User(
            email=email,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
            email_verified=True,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        print(f"  Created user: {email} ({role.value})")
        return user.id


async def _ensure_profile(user_id: uuid.UUID) -> uuid.UUID:
    """Create a full SellerProfile if not present.  Returns profile.id.  Idempotent."""
    user_uuid_str = str(user_id)

    async with get_session()() as session:
        result = await session.execute(
            select(SellerProfile).where(SellerProfile.user_id == user_id),
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            print("  SellerProfile already exists")
            return existing.id

        profile = SellerProfile(
            user_id=user_id,
            firm_name="Sunita Handicrafts",
            owner_name="Sunita Devi",
            pan_encrypted=encrypt_field(
                "ABCDE1234F", user_uuid_str, _mk_key(), _KEY_VERSION
            ),
            bank_name="State Bank of India",
            bank_account_encrypted=encrypt_field(
                "SBIN0001234567", user_uuid_str, _mk_key(), _KEY_VERSION
            ),
            ifsc="SBIN0001234",
            bank_branch="Kanchipuram Main Branch",
            iec="0123456789",
            ad_code_encrypted=encrypt_field(
                "AD1234567", user_uuid_str, _mk_key(), _KEY_VERSION
            ),
            gstin_encrypted=encrypt_field(
                "33ABCDE1234F1ZP", user_uuid_str, _mk_key(), _KEY_VERSION
            ),
            address_line1="123 Gandhi Road",
            address_line2="Near Silk Temple",
            city="Kanchipuram",
            state="Tamil Nadu",
            pincode="631501",
            phone="9876543210",
            is_verified=True,
        )
        session.add(profile)
        await session.commit()
        await session.refresh(profile)
        print("  Created SellerProfile")
        return profile.id


async def _ensure_profile_docs(profile_id: uuid.UUID, user_id: uuid.UUID) -> None:
    """Create placeholder profile documents if none exist.  Idempotent."""
    from app.models.profile_document import DocumentType

    user_uuid_str = str(user_id)
    checksum = _checksum_placeholder()
    encrypted = _encrypted_placeholder(user_uuid_str)

    async with get_session()() as session:
        result = await session.execute(
            select(ProfileDocument).where(ProfileDocument.profile_id == profile_id),
        )
        existing = result.scalars().all()
        if len(existing) > 0:
            print(f"  {len(existing)} profile document(s) already exist — skipping")
            return

        doc_types = [
            DocumentType.pan_card,
            DocumentType.bank_statement,
            DocumentType.iec_certificate,
            DocumentType.gst_certificate,
        ]
        for dt in doc_types:
            doc = ProfileDocument(
                profile_id=profile_id,
                doc_type=dt,
                filename=f"{dt.value}_placeholder.png",
                mime_type="image/png",
                encrypted_content=encrypted,
                checksum_sha256=checksum,
                key_version=_KEY_VERSION,
            )
            session.add(doc)
        await session.commit()
        print(f"  Created {len(doc_types)} placeholder profile documents")


async def _ensure_order(
    seller_user_id: uuid.UUID,
    seller_profile: SellerProfile,
    buyer_user_id: uuid.UUID,
) -> Order:
    """Create a demo order if none exist for this seller.  Idempotent."""
    user_uuid_str = str(seller_user_id)

    async with get_session()() as session:
        result = await session.execute(
            select(Order).where(Order.seller_id == seller_user_id),
        )
        existing = result.scalars().all()
        if len(existing) > 0:
            print(f"  {len(existing)} order(s) already exist for seller — skipping")
            return existing[0]

        snapshot = {
            "firm_name": seller_profile.firm_name,
            "owner_name": seller_profile.owner_name,
            "pan_encrypted": seller_profile.pan_encrypted,
            "bank_name": seller_profile.bank_name,
            "bank_account_encrypted": seller_profile.bank_account_encrypted,
            "ifsc": seller_profile.ifsc,
            "bank_branch": seller_profile.bank_branch,
            "iec": seller_profile.iec,
            "ad_code_encrypted": seller_profile.ad_code_encrypted,
            "gstin_encrypted": seller_profile.gstin_encrypted,
            "address_line1": seller_profile.address_line1,
            "address_line2": seller_profile.address_line2,
            "city": seller_profile.city,
            "state": seller_profile.state,
            "pincode": seller_profile.pincode,
            "phone": seller_profile.phone,
            "is_verified": seller_profile.is_verified,
        }
        snapshot_json = json.dumps(snapshot, default=str)
        encrypted_snapshot = encrypt_field(
            snapshot_json, user_uuid_str, _mk_key(), _KEY_VERSION
        )

        addr_parts = [
            seller_profile.address_line1,
            seller_profile.address_line2,
            seller_profile.city,
            seller_profile.state,
            seller_profile.pincode,
        ]
        exporter_address = ", ".join(p for p in addr_parts if p)

        # 5 silk sarees @ ₹2,000 each → ₹10,000 total = 1,000,000 paise
        line_items: list[dict] = [
            {
                "description": "Pure Kanchipuram Silk Saree",
                "hsn_code": "500720",
                "quantity": 1,
                "unit_price_minor": 200_000,
                "total_minor": 200_000,
            }
            for _ in range(5)
        ]

        order = Order(
            seller_id=seller_user_id,
            buyer_id=buyer_user_id,
            status=OrderStatus.created,
            profile_version=seller_profile.profile_version,
            profile_snapshot_encrypted=encrypted_snapshot,
            destination_country="US",
            value_minor=1_000_000,
            currency="INR",
            consignee="Weber Chicago",
            net_weight_g=2500.0,
            gross_weight_g=3000.0,
            article_id="silk_saree",
            iec=seller_profile.iec or "",
            ad_code_encrypted=seller_profile.ad_code_encrypted or {},
            bank_name=seller_profile.bank_name or "",
            ifsc=seller_profile.ifsc or "",
            bank_account_encrypted=seller_profile.bank_account_encrypted or {},
            exporter_name=seller_profile.firm_name,
            exporter_address=exporter_address,
            state_code=(seller_profile.state or "")[:10],
            line_items=line_items,
        )
        session.add(order)
        await session.commit()
        await session.refresh(order)
        print("  Created demo order: 5 Kanchipuram silk sarees → Chicago")
        return order


async def _attach_doc_pack(order: Order, seller_user_id: uuid.UUID) -> DocPack:
    """Generate and attach a DocPack if none exists.  Idempotent."""
    if order.doc_pack_id is not None:
        print("  DocPack already attached — skipping")
        async with get_session()() as session:
            doc_pack = await session.get(DocPack, order.doc_pack_id)
            return doc_pack

    from app.services.doc_generator import (
        generate_ci,
        generate_cn,
        generate_pbe,
        generate_pl,
    )

    order_data = {
        "exporter_name": order.exporter_name,
        "exporter_address": order.exporter_address,
        "iec": order.iec,
        "consignee": order.consignee,
        "destination_country": order.destination_country,
        "currency": order.currency,
        "value_minor": order.value_minor,
        "net_weight_g": order.net_weight_g,
        "gross_weight_g": order.gross_weight_g,
        "line_items": order.line_items,
        "state_code": order.state_code,
        "article_id": order.article_id,
    }

    ci_doc = generate_ci(order_data)
    pl_doc = generate_pl(order_data)
    cn_doc = generate_cn(order_data)
    pbe_doc = generate_pbe(order_data)

    async with get_session()() as session:
        doc_pack = DocPack(
            order_id=order.id,
            ci_json=ci_doc,
            pl_json=pl_doc,
            cn_json=cn_doc,
            pbe_json=pbe_doc,
        )
        session.add(doc_pack)
        await session.flush()

        order = await session.get(Order, order.id)
        order.status = OrderStatus.docs_generated
        order.doc_pack_id = doc_pack.id

        await session.commit()
        await session.refresh(doc_pack)

    # Write a combined PDF to docs-out/{order_id}.pdf for the /pdf download route
    try:
        import weasyprint
        from pathlib import Path as _Path
        _docs_dir = _Path("docs-out")
        _docs_dir.mkdir(exist_ok=True)
        _order_id_str = str(order.id)

        def _fmt_minor(v):
            if v is None: return "—"
            return f"₹{v/100:,.2f}"

        line_items_html = "".join(
            f"<tr><td>{item.get('description','')}</td>"
            f"<td>{item.get('hsn_code','')}</td>"
            f"<td>{item.get('quantity','')}</td>"
            f"<td>{_fmt_minor(item.get('total_minor'))}</td></tr>"
            for item in (order.line_items or [])
        )

        pbe_line_item = (pbe_doc.get("line_items") or [{}])[0]
        category_val = pbe_line_item.get("description") or pbe_doc.get("category_slug") or cn_doc.get("content_description") or order.article_id or "—"
        hs_code_val = pbe_line_item.get("cth_code") or pbe_doc.get("hs_code") or ((ci_doc.get("line_items") or [{}])[0].get("hsn_code")) or "—"
        declared_value_val = _fmt_minor(cn_doc.get("total_value_minor") or cn_doc.get("declared_value_minor") or order.value_minor)

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{ font-family: sans-serif; font-size: 12px; padding: 32px; color: #111; }}
  h1 {{ font-size: 18px; color: #1a56db; border-bottom: 2px solid #1a56db; padding-bottom: 8px; }}
  h2 {{ font-size: 14px; color: #374151; margin-top: 24px; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 8px; }}
  th {{ background: #f3f4f6; text-align: left; padding: 6px 8px; font-size: 11px; }}
  td {{ padding: 5px 8px; border-bottom: 1px solid #e5e7eb; }}
  .label {{ color: #6b7280; }}
  .val {{ font-weight: bold; }}
  .grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }}
  .field {{ margin-bottom: 8px; }}
</style>
</head><body>
<h1>🇮🇳 DNK Export DocPack — Order {_order_id_str[:8].upper()}</h1>

<div class="grid">
<div>
<h2>Commercial Invoice</h2>
<div class="field"><span class="label">Exporter: </span><span class="val">{ci_doc.get('exporter_name','—')}</span></div>
<div class="field"><span class="label">Consignee: </span><span class="val">{ci_doc.get('consignee','—')}</span></div>
<div class="field"><span class="label">Destination: </span><span class="val">{ci_doc.get('destination_country','—')}</span></div>
<div class="field"><span class="label">Invoice Value: </span><span class="val">{_fmt_minor(ci_doc.get('total_value_minor'))}</span></div>
<div class="field"><span class="label">IEC: </span><span class="val">{ci_doc.get('iec','—')}</span></div>
</div>
<div>
<h2>Packing List</h2>
<div class="field"><span class="label">Net Weight: </span><span class="val">{pl_doc.get('net_weight_g','—')} g</span></div>
<div class="field"><span class="label">Gross Weight: </span><span class="val">{pl_doc.get('gross_weight_g','—')} g</span></div>
<div class="field"><span class="label">Total Qty: </span><span class="val">{pl_doc.get('total_quantity','—')}</span></div>
</div>
</div>

<h2>Line Items</h2>
<table>
<tr><th>Description</th><th>HSN Code</th><th>Qty</th><th>Total Value</th></tr>
{line_items_html}
</table>

<h2>Customs / CN22 / PBE-IV</h2>
<div class="field"><span class="label">CN Type: </span><span class="val">{cn_doc.get('cn_type','—')}</span></div>
<div class="field"><span class="label">Declared Value: </span><span class="val">{declared_value_val}</span></div>
<div class="field"><span class="label">Category: </span><span class="val">{category_val}</span></div>
<div class="field"><span class="label">HS Code: </span><span class="val">{hs_code_val}</span></div>

<p style="margin-top:32px;font-size:10px;color:#9ca3af;">
  Generated by DNK Export Assistant · {ci_doc.get('invoice_date','')[:10]} · Order ID: {_order_id_str}
</p>
</body></html>"""

        _pdf_path = _docs_dir / f"{_order_id_str}.pdf"
        weasyprint.HTML(string=html).write_pdf(target=str(_pdf_path))

        # Also store path in DocPack if the column exists
        try:
            async with get_session()() as session:
                _dp = await session.get(DocPack, doc_pack.id)
                if _dp and hasattr(_dp, 'rendered_pdf_path'):
                    _dp.rendered_pdf_path = str(_pdf_path)
                    await session.commit()
        except Exception:
            pass

        print(f"  Generated PDF → {_pdf_path}")
    except Exception as _pdf_err:
        print(f"  PDF render skipped: {_pdf_err}")

    print("  Generated DocPack: CI, PL, CN22, PBE-IV")
    return doc_pack


async def _attach_qr(order: Order) -> None:
    """Generate a QR code and attach to the order if none exists.  Idempotent."""
    if order.qr_token_jti is not None:
        print("  QR code already generated — skipping")
        return

    order_id_str = str(order.id)

    now = datetime.now(UTC)
    expiry = now + timedelta(days=30)
    jti = str(uuid.uuid4())

    payload = {
        "sub": order_id_str,
        "purpose": "doc_access",
        "iat": now,
        "exp": expiry,
        "jti": jti,
    }
    token = jwt.encode(
        payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    qr_url = f"{settings.APP_BASE_URL}/orders/{order_id_str}/docs?token={token}"

    _QR_DIR.mkdir(exist_ok=True)
    image_path = _QR_DIR / f"{order_id_str}.png"
    qr_img = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr_img.add_data(qr_url)
    qr_img.make(fit=True)
    img = qr_img.make_image(fill_color="black", back_color="white")
    img.save(str(image_path), dpi=(300, 300))

    async with get_session()() as session:
        order = await session.get(Order, order.id)
        order.qr_token_jti = jti
        order.status = OrderStatus.qr_generated
        await session.commit()

    print(f"  Generated QR code → {image_path}")
    print(f"  QR URL: {qr_url}")


async def _seed_demo() -> None:
    """Pre-seed a complete demo scenario.  Idempotent."""
    seller_email = settings.DEMO_SELLER_EMAIL
    seller_password = settings.DEMO_SELLER_PASSWORD
    buyer_email = settings.DEMO_BUYER_EMAIL
    buyer_password = settings.DEMO_BUYER_PASSWORD

    if not all([seller_email, seller_password, buyer_email, buyer_password]):
        missing = []
        for name in [
            "DEMO_SELLER_EMAIL",
            "DEMO_SELLER_PASSWORD",
            "DEMO_BUYER_EMAIL",
            "DEMO_BUYER_PASSWORD",
        ]:
            if not getattr(settings, name, None):
                missing.append(name)
        raise SystemExit(
            f"Missing required env vars: {', '.join(missing)}.  "
            "Check your .env file or environment."
        )

    print(f"\n{'=' * 60}")
    print("  DNK Demo Data Seed")
    print(f"{'=' * 60}\n")

    print("[1/7] Seller user")
    seller_user_id = await _ensure_user(seller_email, seller_password, "seller")

    print("\n[2/7] Seller profile")
    profile_id = await _ensure_profile(seller_user_id)

    print("\n[3/7] Buyer user")
    buyer_user_id = await _ensure_user(buyer_email, buyer_password, "buyer")

    print("\n[4/7] Profile documents")
    await _ensure_profile_docs(profile_id, seller_user_id)

    print("\n[5/7] Demo order")
    async with get_session()() as session:
        seller_profile = await session.get(SellerProfile, profile_id)
    order = await _ensure_order(seller_user_id, seller_profile, buyer_user_id)

    print("\n[6/7] Document pack")
    await _attach_doc_pack(order, seller_user_id)

    print("\n[7/7] QR code")
    await _attach_qr(order)

    print(f"\n{'=' * 60}")
    print("  Seed complete. All demo data is ready.")
    print(
        f"  Sahayak access: {settings.APP_BASE_URL}/orders/{order.id}/docs?token=<qr_token>"
    )
    print(f"{'=' * 60}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


async def _async_main(dry_run: bool) -> None:
    """Run key rotation across all models."""

    old_key_hex = os.environ.get("ENCRYPTION_MASTER_KEY")
    new_key_hex = os.environ.get("NEW_ENCRYPTION_MASTER_KEY")

    if not old_key_hex:
        raise SystemExit("ENCRYPTION_MASTER_KEY (current key) not set in environment")
    if not new_key_hex:
        raise SystemExit("NEW_ENCRYPTION_MASTER_KEY (new key) not set in environment")

    old_key = _validate_hex_key("ENCRYPTION_MASTER_KEY", old_key_hex)
    new_key = _validate_hex_key("NEW_ENCRYPTION_MASTER_KEY", new_key_hex)

    if old_key == new_key:
        raise SystemExit("Old and new master keys are identical — nothing to rotate")

    # Use the new-key-version as 1 by convention (or bump from first record).
    new_version = 2

    # ── Backup warning ─────────────────────────────────────────────────
    print()
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║  ⚠️  BACKUP WARNING                                          ║")
    print("║                                                              ║")
    print("║  Key rotation is DESTRUCTIVE.  If the new key is lost or     ║")
    print("║  incorrect, encrypted data cannot be recovered.              ║")
    print("║                                                              ║")
    print("║  Ensure you have a FULL DATABASE BACKUP before proceeding.   ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    if dry_run:
        print(">>> DRY RUN MODE — no writes will be performed. <<<\n")

    # ── Rotate ─────────────────────────────────────────────────────────
    profile_count = await _rotate_profiles(
        old_key, new_key, new_version, dry_run=dry_run
    )
    doc_count = await _rotate_documents(old_key, new_key, new_version, dry_run=dry_run)
    order_count = await _rotate_orders(old_key, new_key, new_version, dry_run=dry_run)

    # ── Summary ────────────────────────────────────────────────────────
    total = profile_count + doc_count + order_count
    print()
    print("Key rotation summary:")
    print(f"  Seller profiles   : {profile_count}")
    print(f"  Profile documents : {doc_count}")
    print(f"  Orders            : {order_count}")
    print("  ───────────────────────────")
    print(f"  Total rows rotated: {total}")
    print()

    if dry_run:
        print("Dry run complete — no changes were made.")
    else:
        print("Key rotation complete.")
        print("Update ENCRYPTION_MASTER_KEY env var to the new key.")


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Backend-core administration CLI",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    rotate_parser = sub.add_parser(
        "rotate-keys", help="Re-encrypt all fields with the new key"
    )
    rotate_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report counts without making any changes",
    )

    sub.add_parser("seed-demo", help="Pre-seed a complete demo scenario (idempotent)")

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    if args.command == "rotate-keys":
        asyncio.run(_async_main(dry_run=args.dry_run))
    elif args.command == "seed-demo":
        asyncio.run(_seed_demo())
    else:
        _parse_args(["-h"])


if __name__ == "__main__":
    main()
