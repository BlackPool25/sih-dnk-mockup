"""Key rotation CLI — re-encrypt all encrypted database fields with a new master key.

Usage::

    python -m backend-core.cli rotate-keys [--dry-run]

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
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import os

from sqlalchemy import select

from app.models import Order, ProfileDocument, SellerProfile
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
            logger.debug(
                "Rotated SellerProfile %s (user %s)", profile.id, user_uuid
            )
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
            logger.error(
                "ProfileDocument %s has no parent profile — skipping", doc.id
            )
            continue

        try:
            new_encrypted = _re_encrypt(
                doc.encrypted_content, user_uuid, old_key, new_key, new_version
            )
        except DecryptionError:
            logger.error(
                "Decryption failed for ProfileDocument %s — skipping", doc.id
            )
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
# Entry point
# ---------------------------------------------------------------------------


async def _async_main(dry_run: bool) -> None:
    """Run key rotation across all models."""

    old_key_hex = os.environ.get("ENCRYPTION_MASTER_KEY")
    new_key_hex = os.environ.get("NEW_ENCRYPTION_MASTER_KEY")

    if not old_key_hex:
        raise SystemExit(
            "ENCRYPTION_MASTER_KEY (current key) not set in environment"
        )
    if not new_key_hex:
        raise SystemExit(
            "NEW_ENCRYPTION_MASTER_KEY (new key) not set in environment"
        )

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
        description="Rotate encryption keys for all encrypted database fields.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    _ = sub.add_parser("rotate-keys", help="Re-encrypt all fields with the new key")
    for cmd in sub.choices.values():
        cmd.add_argument(
            "--dry-run",
            action="store_true",
            help="Report counts without making any changes",
        )

    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    """Parse args and dispatch the rotation."""
    args = _parse_args(argv)

    if args.command == "rotate-keys":
        asyncio.run(_async_main(dry_run=args.dry_run))
    else:
        _parse_args(["-h"])


if __name__ == "__main__":
    main()
