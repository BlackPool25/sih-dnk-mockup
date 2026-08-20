"""Per-thread AES-256-GCM encryption with HKDF key derivation.

Key hierarchy:
  master_key (32 bytes, from ENCRYPTION_MASTER_KEY env var 64 hex)
    → HKDF-SHA256(salt=SHA256(thread_id), info="dnk-msg-v1-{thread_id}")
    → per-thread derived key (32 bytes)
      → AES-256-GCM encrypt/decrypt per-message body

Differs from storage.crypto per-user HKDF: this module is per-thread, so
cross-thread decryption is cryptographically isolated even under same master
key. Nonces are 96-bit (12 bytes) per NIST GCM spec, randomly generated per
encryption and never reused.
"""

from __future__ import annotations

import base64
import os
from hashlib import sha256
from typing import TypedDict

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.hashes import SHA256
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


class DecryptionError(Exception):
    """Raised when GCM authentication fails — wrong key, wrong thread, or corrupted data."""


class EncryptedMessage(TypedDict):
    """JSONB-safe ciphertext container for a thread message."""

    ciphertext_b64: str
    nonce_b64: str
    key_version: int


def derive_thread_key(master_key: bytes, thread_id: str) -> bytes:
    """Derive a 32-byte AES-256 key from the master key, scoped to a thread.

    Uses HKDF-SHA256 with a salt derived from the thread UUID (deterministic
    per thread) and info bound to ``dnk-msg-v1-{thread_id}`` (enables future
    rotation via version bump without lock-out).

    Args:
        master_key: 32-byte master key (from ENCRYPTION_MASTER_KEY env var).
        thread_id: Thread identifier string (UUID hex).

    Returns:
        32-byte derived AES-256 key.
    """
    salt = sha256(thread_id.encode()).digest()
    info = f"dnk-msg-v1-{thread_id}".encode()

    hkdf = HKDF(
        algorithm=SHA256(),
        length=32,
        salt=salt,
        info=info,
    )
    return hkdf.derive(master_key)


def encrypt_thread_message(
    plaintext: str,
    thread_id: str,
    master_key: bytes,
) -> EncryptedMessage:
    """Encrypt a plaintext string with AES-256-GCM under a per-thread key.

    Generates a random 96-bit (12-byte) nonce per encryption. Nonce and
    ciphertext are base64-encoded for safe storage in Text/JSONB columns.

    Args:
        plaintext: The string to encrypt.
        thread_id: Thread identifier for key derivation.
        master_key: 32-byte master key (from ENCRYPTION_MASTER_KEY env var).

    Returns:
        Dict with keys: ciphertext_b64 (str), nonce_b64 (str), key_version (int=1).
    """
    derived_key = derive_thread_key(master_key, thread_id)
    nonce = os.urandom(12)
    aesgcm = AESGCM(derived_key)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)

    return EncryptedMessage(
        ciphertext_b64=base64.b64encode(ciphertext).decode("ascii"),
        nonce_b64=base64.b64encode(nonce).decode("ascii"),
        key_version=1,
    )


def decrypt_thread_message(
    ciphertext_b64: str,
    nonce_b64: str,
    thread_id: str,
    master_key: bytes,
) -> str:
    """Decrypt a message previously encrypted with encrypt_thread_message.

    Re-derives the per-thread key and decrypts using the stored nonce.

    Args:
        ciphertext_b64: Base64-encoded ciphertext from encrypt_thread_message.
        nonce_b64: Base64-encoded nonce from encrypt_thread_message.
        thread_id: Thread identifier for key derivation.
        master_key: 32-byte master key (from ENCRYPTION_MASTER_KEY env var).

    Returns:
        Decrypted plaintext string.

    Raises:
        DecryptionError: If GCM authentication fails (wrong thread, wrong key,
            or tampered data).
    """
    derived_key = derive_thread_key(master_key, thread_id)

    nonce = base64.b64decode(nonce_b64)
    ciphertext = base64.b64decode(ciphertext_b64)

    aesgcm = AESGCM(derived_key)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext.decode("utf-8")
    except InvalidTag as exc:
        raise DecryptionError("GCM authentication failed: wrong thread key or corrupted data") from exc


# Convenience dict-based wrappers for callers that already have EncryptedMessage
def decrypt_encrypted_message(
    encrypted: EncryptedMessage,
    thread_id: str,
    master_key: bytes,
) -> str:
    """Decrypt from an EncryptedMessage dict wrapper."""
    return decrypt_thread_message(
        encrypted["ciphertext_b64"],
        encrypted["nonce_b64"],
        thread_id,
        master_key,
    )
