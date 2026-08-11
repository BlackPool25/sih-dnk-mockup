"""Tests for key rotation CLI — decrypt-and-re-encrypt with new master key."""

from __future__ import annotations

from unittest.mock import patch

import pytest
from app.cli.__main__ import (
    _looks_encrypted,
    _re_encrypt,
    _rotate_snapshot,
    _validate_hex_key,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

OLD_KEY_HEX = "aa" * 32  # 64 hex chars
NEW_KEY_HEX = "bb" * 32
OLD_KEY = bytes.fromhex(OLD_KEY_HEX)
NEW_KEY = bytes.fromhex(NEW_KEY_HEX)
USER_UUID = "00000000-0000-0000-0000-000000000001"
NEW_VERSION = 2


def _encrypt(plaintext: str, key: bytes = OLD_KEY, version: int = 1) -> dict:
    """Encrypt *plaintext* using storage.crypto.encrypt_field."""
    from storage.crypto import encrypt_field

    return encrypt_field(plaintext, USER_UUID, key, version)


# ---------------------------------------------------------------------------
# _validate_hex_key
# ---------------------------------------------------------------------------


def test_validate_hex_key_valid() -> None:
    """Valid 64-char hex key → bytes."""
    key = _validate_hex_key("TEST_KEY", "ab" * 32)
    assert key == bytes.fromhex("ab" * 32)
    assert len(key) == 32


def test_validate_hex_key_uppercase() -> None:
    """Uppercase hex chars are valid."""
    key = _validate_hex_key("TEST_KEY", "AB" * 32)
    assert key == bytes.fromhex("AB" * 32)


def test_validate_hex_key_wrong_length() -> None:
    """Wrong length → SystemExit."""
    with pytest.raises(SystemExit):
        _validate_hex_key("TEST_KEY", "ab" * 31)  # 62 chars


def test_validate_hex_key_non_hex() -> None:
    """Non-hex chars → SystemExit."""
    with pytest.raises(SystemExit):
        _validate_hex_key("TEST_KEY", "gg" * 32)


# ---------------------------------------------------------------------------
# _looks_encrypted
# ---------------------------------------------------------------------------


def test_looks_encrypted_detects_valid_dict() -> None:
    """Dict with ciphertext_b64 → True."""
    encrypted = {"ciphertext_b64": "abc", "nonce_b64": "def", "key_version": 1}
    assert _looks_encrypted(encrypted) is True


def test_looks_encrypted_rejects_plain_dict() -> None:
    """Dict without ciphertext_b64 → False."""
    assert _looks_encrypted({"foo": "bar"}) is False


def test_looks_encrypted_rejects_none() -> None:
    """None → False."""
    assert _looks_encrypted(None) is False


def test_looks_encrypted_rejects_string() -> None:
    """Plain string → False."""
    assert _looks_encrypted("hello") is False


# ---------------------------------------------------------------------------
# _re_encrypt — roundtrip
# ---------------------------------------------------------------------------


def test_re_encrypt_roundtrip() -> None:
    """Decrypt with old key, encrypt with new key → recoverable with new key."""
    original = "ABCDE1234F"
    encrypted = _encrypt(original, key=OLD_KEY, version=1)

    re_encrypted = _re_encrypt(encrypted, USER_UUID, OLD_KEY, NEW_KEY, NEW_VERSION)

    # Should decrypt with new key
    from storage.crypto import decrypt_field

    plaintext = decrypt_field(re_encrypted, USER_UUID, NEW_KEY)
    assert plaintext == original


def test_re_encrypt_bumps_key_version() -> None:
    """Re-encrypted dict carries the new key_version."""
    encrypted = _encrypt("test-data", key=OLD_KEY, version=1)

    re_encrypted = _re_encrypt(encrypted, USER_UUID, OLD_KEY, NEW_KEY, NEW_VERSION)

    assert re_encrypted["key_version"] == NEW_VERSION


def test_re_encrypt_fails_with_wrong_old_key() -> None:
    """DecryptionError when old key doesn't match."""
    encrypted = _encrypt("test-data", key=OLD_KEY, version=1)
    wrong_key = bytes.fromhex("cc" * 32)

    from storage.crypto import DecryptionError

    with pytest.raises(DecryptionError, match="GCM authentication failed"):
        _re_encrypt(encrypted, USER_UUID, wrong_key, NEW_KEY, NEW_VERSION)


# ---------------------------------------------------------------------------
# _rotate_snapshot
# ---------------------------------------------------------------------------


def test_rotate_snapshot_encrypts_all_sub_fields() -> None:
    """Encrypted sub-fields in snapshot are rotated; plain fields untouched."""
    pan_enc = _encrypt("ABCDE1234F")
    bank_enc = _encrypt("12345678901")

    snapshot = {
        "firm_name": "Test Exports",
        "iec": "1234567890",
        "pan_encrypted": pan_enc,
        "bank_account_encrypted": bank_enc,
        "ad_code_encrypted": None,
        "gstin_encrypted": None,
    }

    result = _rotate_snapshot(snapshot, USER_UUID, OLD_KEY, NEW_KEY, NEW_VERSION)

    # Plain fields unchanged
    assert result["firm_name"] == "Test Exports"
    assert result["iec"] == "1234567890"

    # Encrypted fields rotated
    assert result["pan_encrypted"]["key_version"] == NEW_VERSION
    assert result["bank_account_encrypted"]["key_version"] == NEW_VERSION
    assert result["ad_code_encrypted"] is None
    assert result["gstin_encrypted"] is None

    # Verify recoverability
    from storage.crypto import decrypt_field

    assert decrypt_field(result["pan_encrypted"], USER_UUID, NEW_KEY) == "ABCDE1234F"
    assert decrypt_field(result["bank_account_encrypted"], USER_UUID, NEW_KEY) == "12345678901"


def test_rotate_snapshot_no_encrypted_fields() -> None:
    """Snapshot with no encrypted sub-fields is returned unchanged."""
    snapshot = {"firm_name": "Test", "iec": "foo"}
    result = _rotate_snapshot(snapshot, USER_UUID, OLD_KEY, NEW_KEY, NEW_VERSION)
    assert result == snapshot


# ---------------------------------------------------------------------------
# CLI — argument parsing
# ---------------------------------------------------------------------------


def test_cli_parses_rotate_keys_command() -> None:
    """rotate-keys subcommand is recognised."""
    from app.cli.__main__ import _parse_args

    args = _parse_args(["rotate-keys"])
    assert args.command == "rotate-keys"
    assert args.dry_run is False


def test_cli_parses_dry_run_flag() -> None:
    """--dry-run flag is recognised."""
    from app.cli.__main__ import _parse_args

    args = _parse_args(["rotate-keys", "--dry-run"])
    assert args.command == "rotate-keys"
    assert args.dry_run is True


# ---------------------------------------------------------------------------
# CLI — missing env vars
# ---------------------------------------------------------------------------


def test_cli_missing_old_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing ENCRYPTION_MASTER_KEY → SystemExit."""
    from app.cli.__main__ import _async_main

    monkeypatch.delenv("ENCRYPTION_MASTER_KEY", raising=False)
    monkeypatch.setenv("NEW_ENCRYPTION_MASTER_KEY", NEW_KEY_HEX)

    with pytest.raises(SystemExit) as exc:
        import asyncio

        asyncio.run(_async_main(dry_run=True))
    assert "ENCRYPTION_MASTER_KEY" in str(exc.value)


def test_cli_missing_new_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing NEW_ENCRYPTION_MASTER_KEY → SystemExit."""
    from app.cli.__main__ import _async_main

    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", OLD_KEY_HEX)
    monkeypatch.delenv("NEW_ENCRYPTION_MASTER_KEY", raising=False)

    with pytest.raises(SystemExit) as exc:
        import asyncio

        asyncio.run(_async_main(dry_run=True))
    assert "NEW_ENCRYPTION_MASTER_KEY" in str(exc.value)


def test_cli_identical_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """Identical old and new keys → SystemExit."""
    from app.cli.__main__ import _async_main

    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", OLD_KEY_HEX)
    monkeypatch.setenv("NEW_ENCRYPTION_MASTER_KEY", OLD_KEY_HEX)

    with pytest.raises(SystemExit, match="identical"):
        import asyncio

        asyncio.run(_async_main(dry_run=True))


# ---------------------------------------------------------------------------
# CLI — dry-run integration (mocked DB)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_dry_run_reports_counts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Dry-run iterates all rows and reports counts without writing."""
    from app.cli.__main__ import (
        _async_main,
    )

    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", OLD_KEY_HEX)
    monkeypatch.setenv("NEW_ENCRYPTION_MASTER_KEY", NEW_KEY_HEX)

    async def fake_rotate_profiles(old_key, new_key, new_version, *, dry_run):
        assert dry_run is True
        return 1

    async def fake_rotate_documents(old_key, new_key, new_version, *, dry_run):
        assert dry_run is True
        return 2

    async def fake_rotate_orders(old_key, new_key, new_version, *, dry_run):
        assert dry_run is True
        return 3

    with patch(
        "app.cli.__main__._rotate_profiles", fake_rotate_profiles
    ), patch(
        "app.cli.__main__._rotate_documents", fake_rotate_documents
    ), patch(
        "app.cli.__main__._rotate_orders", fake_rotate_orders
    ):
        await _async_main(dry_run=True)
