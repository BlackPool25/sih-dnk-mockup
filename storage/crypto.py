"""
AES-256-GCM encryption with HKDF key derivation and key versioning.

Key hierarchy:
  master_key (32 bytes, from ENCRYPTION_MASTER_KEY env var)
    → HKDF-SHA256(salt=SHA256(user_uuid), info="dnk-export-v{key_version}")
    → per-user per-version derived key (32 bytes)
      → AES-256-GCM encrypt/decrypt field-level data

Nonces are 96-bit (12 bytes) per NIST GCM spec, randomly generated per encryption.
Ciphertexts and nonces are base64-encoded for JSONB-safe storage.
"""

import base64
import os
from hashlib import sha256

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class DecryptionError(Exception):
    """Raised when GCM authentication fails — wrong key or corrupted data."""


def derive_user_key(master_key: bytes, user_uuid: str, key_version: int) -> bytes:
    """Derive a 32-byte AES-256 key from the master key, scoped to a user + version.

    Uses HKDF-SHA256 with a salt derived from the user UUID (deterministic per user)
    and info bound to the key version (enables rotation without lock-out).

    Args:
        master_key: 32-byte master key (from ENCRYPTION_MASTER_KEY env var).
        user_uuid: User identifier string.
        key_version: Integer key version for rotation.

    Returns:
        32-byte derived AES-256 key.
    """
    salt = sha256(user_uuid.encode()).digest()
    info = f"dnk-export-v{key_version}".encode()

    hkdf = HKDF(
        algorithm=SHA256(),
        length=32,
        salt=salt,
        info=info,
    )
    return hkdf.derive(master_key)


def encrypt_field(plaintext: str, user_uuid: str, master_key: bytes, key_version: int) -> dict:
    """Encrypt a plaintext string with AES-256-GCM, returning a JSONB-safe dict.

    Generates a random 96-bit (12-byte) nonce per encryption. Nonce and ciphertext
    are base64-encoded for safe storage in JSONB columns.

    Args:
        plaintext: The string to encrypt.
        user_uuid: User identifier for key derivation.
        master_key: 32-byte master key (from ENCRYPTION_MASTER_KEY env var).
        key_version: Integer key version (stored alongside ciphertext for decryption).

    Returns:
        dict with keys: ciphertext_b64 (str), nonce_b64 (str), key_version (int).
    """
    derived_key = derive_user_key(master_key, user_uuid, key_version)
    nonce = os.urandom(12)  # 96-bit nonce per NIST GCM spec
    aesgcm = AESGCM(derived_key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

    return {
        "ciphertext_b64": base64.b64encode(ciphertext).decode("ascii"),
        "nonce_b64": base64.b64encode(nonce).decode("ascii"),
        "key_version": key_version,
    }


def decrypt_field(encrypted: dict, user_uuid: str, master_key: bytes) -> str:
    """Decrypt a field previously encrypted with encrypt_field.

    Reads key_version from the encrypted dict, re-derives the key, and decrypts
    using the stored nonce.

    Args:
        encrypted: Dict with ciphertext_b64, nonce_b64, key_version keys.
        user_uuid: User identifier for key derivation.
        master_key: 32-byte master key (from ENCRYPTION_MASTER_KEY env var).

    Returns:
        Decrypted plaintext string.

    Raises:
        DecryptionError: If GCM authentication fails (wrong key or tampered data).
    """
    key_version = encrypted["key_version"]
    derived_key = derive_user_key(master_key, user_uuid, key_version)

    nonce = base64.b64decode(encrypted["nonce_b64"])
    ciphertext = base64.b64decode(encrypted["ciphertext_b64"])

    aesgcm = AESGCM(derived_key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except InvalidTag:
        raise DecryptionError("GCM authentication failed: wrong key or corrupted data")
