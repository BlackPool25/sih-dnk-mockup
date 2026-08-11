"""Tests for profile_crypto — field-level encryption/decryption of profile data."""

from __future__ import annotations

import pytest
from storage.config import Settings
from storage.crypto import DecryptionError

from app.services.profile_crypto import (
    ENCRYPTED_FIELDS,
    decrypt_profile_fields,
    encrypt_profile_fields,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TEST_HEX_KEY = "ab" * 32  # 64 hex chars = 32 bytes
TEST_USER_UUID = "test-user-uuid-1234"

MAKE_SETTINGS: dict = {
    "DATABASE_URL": "postgresql://test",
    "REDIS_URL": "redis://test",
    "ENCRYPTION_MASTER_KEY": TEST_HEX_KEY,
    "JWT_SECRET_KEY": "a" * 32,
    "SAHAYAK_EMAIL": "s@test.com",
    "SAHAYAK_PASSWORD": "p",
    "DEMO_SELLER_EMAIL": "s@test.com",
    "DEMO_SELLER_PASSWORD": "p",
    "DEMO_BUYER_EMAIL": "b@test.com",
    "DEMO_BUYER_PASSWORD": "p",
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _patch_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    """Replace the global settings singleton with a deterministic test instance."""
    test_settings = Settings(**MAKE_SETTINGS)
    monkeypatch.setattr(
        "app.services.profile_crypto.settings",
        test_settings,
    )


def _profile(*, gstin: str | None = "22AAAAA0000A1Z5") -> dict:
    """Build a minimal profile dict for testing."""
    data: dict = {
        "firm_name": "Test Exports Ltd",
        "address": "123 Shipping Lane",
        "iec": "1234567890",
        "pan": "ABCDE1234F",
        "bank_account": "12345678901",
        "ad_code": "9876543",
    }
    if gstin is not None:
        data["gstin"] = gstin
    return data


# ---------------------------------------------------------------------------
# 1. Roundtrip
# ---------------------------------------------------------------------------


def test_roundtrip() -> None:
    """Encrypt then decrypt should recover original values."""
    profile = _profile()

    encrypted = encrypt_profile_fields(profile, TEST_USER_UUID)
    decrypted = decrypt_profile_fields(encrypted, TEST_USER_UUID)

    assert decrypted["pan"] == "ABCDE1234F"
    assert decrypted["bank_account"] == "12345678901"
    assert decrypted["ad_code"] == "9876543"
    assert decrypted["gstin"] == "22AAAAA0000A1Z5"


# ---------------------------------------------------------------------------
# 2. Only encrypts sensitive fields
# ---------------------------------------------------------------------------


def test_only_encrypts_sensitive_fields() -> None:
    """Non-sensitive fields must remain untouched plaintext."""
    profile = _profile()

    encrypted = encrypt_profile_fields(profile, TEST_USER_UUID)

    # Sensitive fields → encrypted dicts
    for field in ENCRYPTED_FIELDS:
        val = encrypted[field]
        assert isinstance(val, dict), f"{field} should be encrypted dict"
        assert "ciphertext_b64" in val

    # Non-sensitive fields → unchanged
    assert encrypted["firm_name"] == "Test Exports Ltd"
    assert encrypted["address"] == "123 Shipping Lane"
    assert encrypted["iec"] == "1234567890"


# ---------------------------------------------------------------------------
# 3. Different users isolation
# ---------------------------------------------------------------------------


def test_different_users_isolation() -> None:
    """Decryption with a different user_uuid must raise DecryptionError."""
    profile = _profile()

    encrypted = encrypt_profile_fields(profile, TEST_USER_UUID)

    with pytest.raises(DecryptionError, match="GCM authentication failed"):
        decrypt_profile_fields(encrypted, "other-user-uuid")


# ---------------------------------------------------------------------------
# 4. Wrong master key
# ---------------------------------------------------------------------------


def test_wrong_master_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Decryption with a different master key must raise DecryptionError."""
    profile = _profile()

    # Encrypt with the test key (autouse fixture set it)
    encrypted = encrypt_profile_fields(profile, TEST_USER_UUID)

    # Swap in a different master key for decryption
    alt_key_hex = "cd" * 32
    alt_settings = Settings(**{**MAKE_SETTINGS, "ENCRYPTION_MASTER_KEY": alt_key_hex})
    monkeypatch.setattr(
        "app.services.profile_crypto.settings",
        alt_settings,
    )

    with pytest.raises(DecryptionError, match="GCM authentication failed"):
        decrypt_profile_fields(encrypted, TEST_USER_UUID)


# ---------------------------------------------------------------------------
# 5. GSTIN optional
# ---------------------------------------------------------------------------


def test_gstin_present_encrypted() -> None:
    """GSTIN is encrypted when present in profile data."""
    profile = _profile(gstin="22AAAAA0000A1Z5")
    encrypted = encrypt_profile_fields(profile, TEST_USER_UUID)
    assert isinstance(encrypted["gstin"], dict)
    assert "ciphertext_b64" in encrypted["gstin"]


def test_gstin_absent_skipped() -> None:
    """Encryption skips GSTIN when absent (not present in dict)."""
    profile = _profile(gstin=None)
    encrypted = encrypt_profile_fields(profile, TEST_USER_UUID)
    assert "gstin" not in encrypted


def test_gstin_roundtrip() -> None:
    """Roundtrip works with GSTIN present."""
    profile = _profile(gstin="22AAAAA0000A1Z5")
    encrypted = encrypt_profile_fields(profile, TEST_USER_UUID)
    decrypted = decrypt_profile_fields(encrypted, TEST_USER_UUID)
    assert decrypted["gstin"] == "22AAAAA0000A1Z5"
