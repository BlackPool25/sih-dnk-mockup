"""Profile-field encryption service.

Wraps ``storage.crypto`` for profile-specific encryption of sensitive fields
(pan, bank_account, ad_code, gstin).  Delegates all cryptographic operations
to ``storage.crypto`` — no primitives are redefined here.
"""

from __future__ import annotations

from storage.config import settings
from storage.crypto import DecryptionError, decrypt_field, encrypt_field

__all__ = [
    "ENCRYPTED_FIELDS",
    "DecryptionError",
    "decrypt_profile_fields",
    "encrypt_profile_fields",
]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ENCRYPTED_FIELDS: list[str] = ["pan", "bank_account", "ad_code", "gstin"]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _master_key() -> bytes:
    """Hex-decode the master key from settings (64-char hex → 32 bytes)."""
    return bytes.fromhex(settings.ENCRYPTION_MASTER_KEY)


def _looks_encrypted(value: object) -> bool:
    """Return True when *value* is a dict carrying ``ciphertext_b64``."""
    return isinstance(value, dict) and "ciphertext_b64" in value


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def encrypt_profile_fields(
    profile_data: dict,
    user_uuid: str,
    *,
    key_version: int = 1,
) -> dict:
    """Encrypt sensitive profile fields in-place.

    For each field in ``ENCRYPTED_FIELDS`` that is **present and not None**,
    replaces the plaintext value with the encrypted dict returned by
    ``storage.crypto.encrypt_field()``.

    Args:
        profile_data: Profile dict with potentially sensitive fields.
        user_uuid:   User UUID for key derivation.
        key_version: Encryption key version (default 1).

    Returns:
        The same *profile_data* dict (mutated in-place) for convenience.
    """
    master_key = _master_key()
    for field in ENCRYPTED_FIELDS:
        plaintext = profile_data.get(field)
        if plaintext is None:
            continue
        profile_data[field] = encrypt_field(
            str(plaintext),
            user_uuid,
            master_key,
            key_version,
        )
    return profile_data


def decrypt_profile_fields(profile_data: dict, user_uuid: str) -> dict:
    """Decrypt previously encrypted profile fields in-place.

    For each field in ``ENCRYPTED_FIELDS`` whose value looks like an encrypted
    dict (i.e. carries ``ciphertext_b64``), replaces it with the decrypted
    plaintext string.

    Args:
        profile_data: Profile dict with encrypted field values.
        user_uuid:    User UUID for key derivation.

    Returns:
        The same *profile_data* dict (mutated in-place) for convenience.

    Raises:
        DecryptionError: If GCM authentication fails for any field.
    """
    master_key = _master_key()
    for field in ENCRYPTED_FIELDS:
        value = profile_data.get(field)
        if not _looks_encrypted(value):
            continue
        profile_data[field] = decrypt_field(value, user_uuid, master_key)
    return profile_data
