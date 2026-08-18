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
    2. Iterates every row in ``SellerProfile`` and ``ProfileDocument`` that
       carries encrypted fields.  Orders no longer live in backend-core — the
       unified ``orders`` table is owned by validation-engine.
    3. Decrypts each field with the **old** key (using ``key_version`` embedded in
       the stored ciphertext), re-encrypts with the **new** key (bumped
       ``key_version``), and updates the row.
    4. In dry-run mode only reports counts — no writes are performed.

seed-demo
    Pre-seed a complete demo scenario (idempotent) by driving validation-engine
    over HTTP via ``val_client`` (backend-core no longer owns an Order row).

    Reads credentials from ``storage.config.settings`` (``DEMO_SELLER_*`` /
    ``DEMO_BUYER_*`` env vars or ``.env``).  Creates:

    - Seller ``sunita@handicrafts.in`` + full profile (PAN encrypted, IEC,
      SBI bank, AD code encrypted, Kanchipuram address)
    - Buyer ``weber@example.com``
    - Order in validation-engine: 5 silk sarees → Chicago, ₹10 000, profile
      auto-filled
    - Documents via ``generate_docs_all``
    - QR code PNG + ``set_qr_token``
    - Placeholder profile documents (encrypted)
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import hashlib
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
from qrcode.constants import ERROR_CORRECT_L
from sqlalchemy import select

from app.models.profile import SellerProfile
from app.models.profile_document import ProfileDocument
from app.services.val_client import (
    InvalidInputError,
    NotFoundError,
    ServiceUnavailable,
    val_client,
)
from storage.config import settings
from storage.crypto import DecryptionError, decrypt_field, encrypt_field
from storage.db import get_session

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

# Indian state name → 2-char ISO 3166-2 subdiv code (PBE state_code).
_STATE_CODES: dict[str, str] = {
    "Maharashtra": "MH",
    "Karnataka": "KA",
    "Tamil Nadu": "TN",
    "Uttar Pradesh": "UP",
    "Delhi": "DL",
    "Gujarat": "GJ",
    "Rajasthan": "RJ",
    "West Bengal": "WB",
    "Kerala": "KL",
    "Telangana": "TS",
    "Andhra Pradesh": "AP",
    "Madhya Pradesh": "MP",
    "Punjab": "PB",
    "Haryana": "HR",
    "Bihar": "BR",
    "Odisha": "OD",
    "Assam": "AS",
}

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


def _validate_hex_key(env_var: str, value: str) -> bytes:
    """Validate a 64-char hex key and return its bytes form."""
    if len(value) != 64:
        raise SystemExit(f"{env_var} must be exactly 64 hex characters, got {len(value)}")
    if not all(c in "0123456789abcdefABCDEF" for c in value):
        raise SystemExit(f"{env_var} must contain only hex characters")
    return bytes.fromhex(value)


def _decrypt_or(encrypted_value: dict | None, user_uuid: str, master_key: bytes) -> str:
    """Decrypt a field; empty string when missing or on DecryptionError."""
    if encrypted_value is None:
        return ""
    try:
        return decrypt_field(encrypted_value, user_uuid, master_key)
    except DecryptionError:
        return ""


# ---------------------------------------------------------------------------
# Core rotation logic (SellerProfile + ProfileDocument only)
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
        profiles: list[SellerProfile] = list(result.scalars().all())

    for profile in profiles:
        user_uuid = str(profile.user_id)
        row_touched = False

        for field_name in _PROFILE_ENCRYPTED_FIELDS:
            encrypted = getattr(profile, field_name)
            if not _looks_encrypted(encrypted):
                continue
            try:
                new_encrypted = _re_encrypt(encrypted, user_uuid, old_key, new_key, new_version)
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
        rows = list(result.scalars().all())

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
            pan_encrypted=encrypt_field("ABCDE1234F", user_uuid_str, _mk_key(), _KEY_VERSION),
            bank_name="State Bank of India",
            bank_account_encrypted=encrypt_field(
                "SBIN0001234567", user_uuid_str, _mk_key(), _KEY_VERSION
            ),
            ifsc="SBIN0001234",
            bank_branch="Kanchipuram Main Branch",
            iec="0123456789",
            ad_code_encrypted=encrypt_field(
                "12345678901234", user_uuid_str, _mk_key(), _KEY_VERSION
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


def _build_demo_payload(
    profile: SellerProfile,
    seller_user_id: uuid.UUID,
    buyer_user_id: uuid.UUID,
) -> dict[str, object]:
    """Build the validation-engine OrderPayload for the demo silk-saree order."""
    user_uuid_str = str(seller_user_id)
    master_key = _mk_key()

    addr_parts = [
        profile.address_line1,
        profile.address_line2,
        profile.city,
        profile.state,
        profile.pincode,
    ]
    exporter_address = ", ".join(p for p in addr_parts if p)

    # 5 silk sarees @ ₹2,000 each → ₹10,000 total = 1,000,000 paise
    return {
        "seller_id": str(seller_user_id),
        "buyer_id": str(buyer_user_id),
        "destination_country": "US",
        "value_minor": 1_000_000,
        "currency": "INR",
        "consignee": "Weber Chicago",
        "net_weight_g": 2500,
        "gross_weight_g": 3000,
        "article_id": "silk_saree",
        "line_items": [
            {
                "category_slug": "handloom-scarves-stoles",
                "quantity": 5,
                "weight_g": 2500,
                "hs_code": "6214",
                "value_minor": 1_000_000,
            }
        ],
        "iec": profile.iec or "",
        "gstin": _decrypt_or(profile.gstin_encrypted, user_uuid_str, master_key),
        "ad_code": _decrypt_or(profile.ad_code_encrypted, user_uuid_str, master_key),
        "bank_account": _decrypt_or(profile.bank_account_encrypted, user_uuid_str, master_key),
        "bank_name": profile.bank_name or "",
        "ifsc": profile.ifsc or "",
        "exporter_name": profile.firm_name,
        "exporter_address": exporter_address,
        "state_code": _STATE_CODES.get(profile.state or "", ""),
    }


async def _existing_order_id(seller_user_id: uuid.UUID) -> str:
    """Return the seller's first order id in validation-engine, or ''."""
    data = await val_client.list_orders(seller_id=str(seller_user_id), limit=1)
    orders = data.get("orders", [])
    if not isinstance(orders, list) or not orders:
        return ""
    first = orders[0]
    if isinstance(first, dict):
        inner = first.get("order")
        if isinstance(inner, dict):
            return str(inner.get("id") or "")
        return str(first.get("id") or "")
    return ""


def _write_qr_png(order_id: str, jti: str) -> tuple[str, str]:
    """Create a doc-access JWT, write the QR PNG, return (token, image_path)."""
    order_id_str = str(order_id)

    now = datetime.now(UTC)
    expiry = now + timedelta(days=30)
    payload = {
        "sub": order_id_str,
        "purpose": "doc_access",
        "iat": now,
        "exp": expiry,
        "jti": jti,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    qr_url = f"{settings.APP_BASE_URL}/orders/{order_id_str}/docs?token={token}"

    _QR_DIR.mkdir(exist_ok=True)
    image_path = _QR_DIR / f"{order_id_str}.png"
    qr_img = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr_img.add_data(qr_url)
    qr_img.make(fit=True)
    img = qr_img.make_image(fill_color="black", back_color="white")
    with image_path.open("wb") as fh:
        img.save(fh)

    print(f"  Generated QR code → {image_path}")
    print(f"  QR URL: {qr_url}")
    return token, str(image_path)


async def _seed_demo() -> None:
    """Pre-seed a complete demo scenario by driving validation-engine.  Idempotent."""
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

    print("[1/6] Seller user")
    seller_user_id = await _ensure_user(seller_email, seller_password, "seller")

    print("\n[2/6] Seller profile")
    profile_id = await _ensure_profile(seller_user_id)

    print("\n[3/6] Buyer user")
    buyer_user_id = await _ensure_user(buyer_email, buyer_password, "buyer")

    print("\n[4/6] Profile documents")
    await _ensure_profile_docs(profile_id, seller_user_id)

    print("\n[5/6] Demo order (validation-engine)")
    async with get_session()() as session:
        seller_profile = await session.get(SellerProfile, profile_id)
    if seller_profile is None:
        raise SystemExit("Seller profile not found — aborting seed")

    order_id = await _existing_order_id(seller_user_id)
    if order_id:
        print(f"  Order already exists for seller — reusing {order_id}")
    else:
        payload = _build_demo_payload(seller_profile, seller_user_id, buyer_user_id)
        try:
            report = await val_client.create_order(payload)
        except (NotFoundError, InvalidInputError, ServiceUnavailable) as exc:
            raise SystemExit(f"validation-engine create_order failed: {exc}") from exc
        order_id = str(report.get("order_id") or "")
        if not order_id:
            raise SystemExit("validation-engine did not return an order_id")
        print(f"  Created demo order: 5 Kanchipuram silk sarees → Chicago ({order_id})")

    print("\n[6/6] Documents + QR")
    docs = await val_client.get_order_documents(order_id)
    existing_docs = docs.get("documents", [])
    if not (isinstance(existing_docs, list) and existing_docs):
        try:
            result = await val_client.generate_docs_all(order_id)
            print(f"  Generated documents: {result.get('status')}")
        except (NotFoundError, InvalidInputError, ServiceUnavailable) as exc:
            raise SystemExit(f"validation-engine generate_docs_all failed: {exc}") from exc
    else:
        print("  Documents already generated — skipping")

    order_detail = await val_client.get_order(order_id)
    order = order_detail.get("order")
    order_dict = order if isinstance(order, dict) else {}
    existing_jti = order_dict.get("qr_token_jti")
    if existing_jti:
        print("  QR code already generated — skipping")
    else:
        jti = str(uuid.uuid4())
        try:
            await val_client.set_qr_token(order_id, jti)
        except (NotFoundError, InvalidInputError, ServiceUnavailable) as exc:
            raise SystemExit(f"validation-engine set_qr_token failed: {exc}") from exc
        _write_qr_png(order_id, jti)

    print(f"\n{'=' * 60}")
    print("  Seed complete. All demo data is ready.")
    print(f"  Sahayak access: {settings.APP_BASE_URL}/orders/{order_id}/docs?token=<qr_token>")
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
    profile_count = await _rotate_profiles(old_key, new_key, new_version, dry_run=dry_run)
    doc_count = await _rotate_documents(old_key, new_key, new_version, dry_run=dry_run)

    # ── Summary ────────────────────────────────────────────────────────
    total = profile_count + doc_count
    print()
    print("Key rotation summary:")
    print(f"  Seller profiles   : {profile_count}")
    print(f"  Profile documents : {doc_count}")
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

    rotate_parser = sub.add_parser("rotate-keys", help="Re-encrypt all fields with the new key")
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
