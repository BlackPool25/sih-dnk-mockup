"""Tests for key rotation CLI — decrypt-and-re-encrypt with new master key.

Orders were deleted from backend-core (moved to validation-engine); rotation
now covers SellerProfile + ProfileDocument rows only.  The Order-specific
``_rotate_snapshot``/``_rotate_orders`` helpers no longer exist.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest
from app.cli.__main__ import (
    _async_main,
    _looks_encrypted,
    _parse_args,
    _re_encrypt,
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


def _encrypt(plaintext: str, key: bytes = OLD_KEY, version: int = 1) -> dict[str, object]:
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
# CLI — argument parsing
# ---------------------------------------------------------------------------


def test_cli_parses_rotate_keys_command() -> None:
    """rotate-keys subcommand is recognised."""

    args = _parse_args(["rotate-keys"])
    assert args.command == "rotate-keys"
    assert args.dry_run is False


def test_cli_parses_dry_run_flag() -> None:
    """--dry-run flag is recognised."""

    args = _parse_args(["rotate-keys", "--dry-run"])
    assert args.command == "rotate-keys"
    assert args.dry_run is True


# ---------------------------------------------------------------------------
# CLI — missing env vars
# ---------------------------------------------------------------------------


def test_cli_missing_old_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing ENCRYPTION_MASTER_KEY → SystemExit."""

    monkeypatch.delenv("ENCRYPTION_MASTER_KEY", raising=False)
    monkeypatch.setenv("NEW_ENCRYPTION_MASTER_KEY", NEW_KEY_HEX)

    with pytest.raises(SystemExit) as exc:
        import asyncio

        asyncio.run(_async_main(dry_run=True))
    assert "ENCRYPTION_MASTER_KEY" in str(exc.value)


def test_cli_missing_new_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing NEW_ENCRYPTION_MASTER_KEY → SystemExit."""

    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", OLD_KEY_HEX)
    monkeypatch.delenv("NEW_ENCRYPTION_MASTER_KEY", raising=False)

    with pytest.raises(SystemExit) as exc:
        import asyncio

        asyncio.run(_async_main(dry_run=True))
    assert "NEW_ENCRYPTION_MASTER_KEY" in str(exc.value)


def test_cli_identical_keys(monkeypatch: pytest.MonkeyPatch) -> None:
    """Identical old and new keys → SystemExit."""

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
    """Dry-run iterates profiles + documents and reports counts without writing."""

    monkeypatch.setenv("ENCRYPTION_MASTER_KEY", OLD_KEY_HEX)
    monkeypatch.setenv("NEW_ENCRYPTION_MASTER_KEY", NEW_KEY_HEX)

    async def fake_rotate_profiles(old_key, new_key, new_version, *, dry_run):
        assert dry_run is True
        return 1

    async def fake_rotate_documents(old_key, new_key, new_version, *, dry_run):
        assert dry_run is True
        return 2

    with (
        patch("app.cli.__main__._rotate_profiles", fake_rotate_profiles),
        patch("app.cli.__main__._rotate_documents", fake_rotate_documents),
    ):
        await _async_main(dry_run=True)


# ---------------------------------------------------------------------------
# CLI — real rotation against the live DB
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rotate_profiles_reencrypts_with_new_key(
    test_seller: dict[str, str],
) -> None:
    """A profile encrypted under the old key decrypts under the new key."""
    from app.cli.__main__ import _rotate_profiles
    from app.main import app
    from httpx import ASGITransport, AsyncClient
    from storage.crypto import decrypt_field
    from storage.db import get_session

    payload = {
        "firm_name": "Rotation Test Exports",
        "pan": "ABCDE1234F",
        "bank_account": "12345678901",
        "ad_code": "9876543",
        "gstin": "22AAAAA0000A1Z5",
        "state": "Maharashtra",
    }

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/profile",
            json=payload,
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
    assert resp.status_code == 201, resp.text

    # Encrypted with the test master key ("ab"*32) at key_version 1
    old_key = bytes.fromhex("ab" * 32)
    new_key = bytes.fromhex("cd" * 32)

    count = await _rotate_profiles(old_key, new_key, 2, dry_run=False)
    assert count >= 1

    from app.models.profile import SellerProfile
    from sqlalchemy import select
    from uuid import UUID

    async with get_session()() as session:
        result = await session.execute(
            select(SellerProfile).where(
                SellerProfile.user_id == UUID(resp.json()["user_id"])
            )
        )
        profile = result.scalar_one()

    assert profile.pan_encrypted is not None
    assert profile.ad_code_encrypted is not None
    assert profile.pan_encrypted["key_version"] == 2
    assert decrypt_field(profile.pan_encrypted, test_seller["user_id"], new_key) == "ABCDE1234F"
    assert decrypt_field(profile.ad_code_encrypted, test_seller["user_id"], new_key) == "9876543"
