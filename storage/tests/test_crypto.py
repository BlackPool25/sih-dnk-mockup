"""Tests for storage.crypto — AES-256-GCM encryption with HKDF key derivation."""

import base64
import os

import pytest

from storage.crypto import (
    DecryptionError,
    decrypt_field,
    derive_user_key,
    encrypt_field,
)

# ── Shared test fixtures ────────────────────────────────────────────────

MASTER_KEY = os.urandom(32)
OTHER_MASTER_KEY = os.urandom(32)
USER_UUID = "test-user-001"
ALT_USER_UUID = "test-user-002"
KEY_VERSION = 21
ALT_KEY_VERSION = 22
PLAINTEXT = "sensitive-field-value-123"


# ── Deterministic test vector (HKDF-SHA256 with known inputs) ────────────
# master_key = bytes(range(32))  # 0x00..0x1f
# user_uuid = "vector-user"
# key_version = 1
# Expected derived key (pre-computed, verifiable independently):
EXPECTED_DERIVED_KEY_HEX = "e29a3d0a16001e0aed4f0185f453636f54c4c82de059e46560a4f457af0d1da3"


# ── Test: roundtrip ──────────────────────────────────────────────────────


def test_roundtrip():
    """encrypt(plaintext) then decrypt → identical plaintext."""
    encrypted = encrypt_field(PLAINTEXT, USER_UUID, MASTER_KEY, KEY_VERSION)
    assert encrypted["key_version"] == KEY_VERSION
    assert isinstance(encrypted["ciphertext_b64"], str)
    assert isinstance(encrypted["nonce_b64"], str)

    decrypted = decrypt_field(encrypted, USER_UUID, MASTER_KEY)
    assert decrypted == PLAINTEXT


# ── Test: key isolation (different users) ────────────────────────────────


def test_key_isolation():
    """Different user_uuids → different derived keys → decryption fails."""
    encrypted = encrypt_field(PLAINTEXT, USER_UUID, MASTER_KEY, KEY_VERSION)

    with pytest.raises(DecryptionError, match="GCM authentication failed"):
        decrypt_field(encrypted, ALT_USER_UUID, MASTER_KEY)


# ── Test: key version isolation ──────────────────────────────────────────


def test_key_version_isolation():
    """Different key_versions → different derived keys → decryption fails."""
    encrypted = encrypt_field(PLAINTEXT, USER_UUID, MASTER_KEY, KEY_VERSION)

    # Tamper the stored key_version so the wrong key is derived
    tampered = dict(encrypted)
    tampered["key_version"] = ALT_KEY_VERSION

    with pytest.raises(DecryptionError, match="GCM authentication failed"):
        decrypt_field(tampered, USER_UUID, MASTER_KEY)


# ── Test: wrong master key ───────────────────────────────────────────────


def test_wrong_key():
    """Encrypt with one master_key, decrypt with another → DecryptionError."""
    encrypted = encrypt_field(PLAINTEXT, USER_UUID, MASTER_KEY, KEY_VERSION)

    with pytest.raises(DecryptionError, match="GCM authentication failed"):
        decrypt_field(encrypted, USER_UUID, OTHER_MASTER_KEY)


# ── Test: tampered ciphertext ────────────────────────────────────────────


def test_tampered_ciphertext():
    """Modifying the ciphertext → GCM auth fails → DecryptionError."""
    encrypted = encrypt_field(PLAINTEXT, USER_UUID, MASTER_KEY, KEY_VERSION)

    # Flip a bit in the base64-decoded ciphertext
    ciphertext_bytes = bytearray(base64.b64decode(encrypted["ciphertext_b64"]))
    ciphertext_bytes[-1] ^= 0x01  # flip last bit

    tampered = dict(encrypted)
    tampered["ciphertext_b64"] = base64.b64encode(bytes(ciphertext_bytes)).decode("ascii")

    with pytest.raises(DecryptionError, match="GCM authentication failed"):
        decrypt_field(tampered, USER_UUID, MASTER_KEY)


# ── Test: nonce randomness ───────────────────────────────────────────────


def test_nonce_randomness():
    """Same plaintext encrypted twice → different ciphertexts (random nonce)."""
    enc1 = encrypt_field(PLAINTEXT, USER_UUID, MASTER_KEY, KEY_VERSION)
    enc2 = encrypt_field(PLAINTEXT, USER_UUID, MASTER_KEY, KEY_VERSION)

    # Both should decrypt correctly
    assert decrypt_field(enc1, USER_UUID, MASTER_KEY) == PLAINTEXT
    assert decrypt_field(enc2, USER_UUID, MASTER_KEY) == PLAINTEXT

    # Ciphertexts must differ (random nonce)
    assert enc1["ciphertext_b64"] != enc2["ciphertext_b64"]
    assert enc1["nonce_b64"] != enc2["nonce_b64"]


# ── Test: deterministic test vector ──────────────────────────────────────


def test_test_vector_deterministic():
    """HKDF-SHA256 with known inputs → known derived key (deterministic)."""
    master_key = bytes(range(32))  # 0x00..0x1f
    user_uuid = "vector-user"
    key_version = 1

    derived = derive_user_key(master_key, user_uuid, key_version)
    assert derived.hex() == EXPECTED_DERIVED_KEY_HEX
    assert len(derived) == 32
