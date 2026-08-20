"""Tests for app.services.crypto — per-thread HKDF + AESGCM."""

from __future__ import annotations

import base64
import os

import pytest

from app.services.crypto import (
    DecryptionError,
    decrypt_thread_message,
    derive_thread_key,
    encrypt_thread_message,
)

MASTER_KEY = os.urandom(32)
OTHER_MASTER_KEY = os.urandom(32)
THREAD_A = "550e8400-e29b-41d4-a716-446655440001"
THREAD_B = "550e8400-e29b-41d4-a716-446655440002"
PLAINTEXT = "hello dnk — secret quote 42"


def test_roundtrip() -> None:
    enc = encrypt_thread_message(PLAINTEXT, THREAD_A, MASTER_KEY)
    assert enc["key_version"] == 1
    assert isinstance(enc["ciphertext_b64"], str)
    assert isinstance(enc["nonce_b64"], str)
    # nonce is 12 bytes base64 → 16 chars
    assert len(base64.b64decode(enc["nonce_b64"])) == 12
    dec = decrypt_thread_message(enc["ciphertext_b64"], enc["nonce_b64"], THREAD_A, MASTER_KEY)
    assert dec == PLAINTEXT


def test_cross_thread_fail() -> None:
    enc = encrypt_thread_message(PLAINTEXT, THREAD_A, MASTER_KEY)
    with pytest.raises(DecryptionError, match="GCM authentication failed"):
        decrypt_thread_message(enc["ciphertext_b64"], enc["nonce_b64"], THREAD_B, MASTER_KEY)


def test_wrong_master_key_fail() -> None:
    enc = encrypt_thread_message(PLAINTEXT, THREAD_A, MASTER_KEY)
    with pytest.raises(DecryptionError, match="GCM authentication failed"):
        decrypt_thread_message(enc["ciphertext_b64"], enc["nonce_b64"], THREAD_A, OTHER_MASTER_KEY)


def test_nonce_uniqueness() -> None:
    enc1 = encrypt_thread_message(PLAINTEXT, THREAD_A, MASTER_KEY)
    enc2 = encrypt_thread_message(PLAINTEXT, THREAD_A, MASTER_KEY)
    assert enc1["nonce_b64"] != enc2["nonce_b64"]
    assert enc1["ciphertext_b64"] != enc2["ciphertext_b64"]
    # both decrypt correctly
    assert decrypt_thread_message(enc1["ciphertext_b64"], enc1["nonce_b64"], THREAD_A, MASTER_KEY) == PLAINTEXT
    assert decrypt_thread_message(enc2["ciphertext_b64"], enc2["nonce_b64"], THREAD_A, MASTER_KEY) == PLAINTEXT


def test_tampered_ciphertext() -> None:
    enc = encrypt_thread_message(PLAINTEXT, THREAD_A, MASTER_KEY)
    ct = bytearray(base64.b64decode(enc["ciphertext_b64"]))
    ct[-1] ^= 0x01
    tampered = base64.b64encode(bytes(ct)).decode("ascii")
    with pytest.raises(DecryptionError, match="GCM authentication failed"):
        decrypt_thread_message(tampered, enc["nonce_b64"], THREAD_A, MASTER_KEY)


def test_derive_thread_key_deterministic() -> None:
    k1 = derive_thread_key(MASTER_KEY, THREAD_A)
    k2 = derive_thread_key(MASTER_KEY, THREAD_A)
    assert k1 == k2
    assert len(k1) == 32


def test_derive_thread_key_isolation() -> None:
    k_a = derive_thread_key(MASTER_KEY, THREAD_A)
    k_b = derive_thread_key(MASTER_KEY, THREAD_B)
    assert k_a != k_b


def test_derive_thread_key_known_vector() -> None:
    # Verify HKDF binding matches spec: salt=sha256(thread_id), info=dnk-msg-v1-{thread_id}
    master = bytes(range(32))
    tid = "vector-thread-001"
    k = derive_thread_key(master, tid)
    # recompute with same params via storage-style HKDF should be stable
    from hashlib import sha256

    from cryptography.hazmat.primitives.hashes import SHA256
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF

    hkdf = HKDF(algorithm=SHA256(), length=32, salt=sha256(tid.encode()).digest(), info=f"dnk-msg-v1-{tid}".encode())
    expected = hkdf.derive(master)
    assert k == expected
