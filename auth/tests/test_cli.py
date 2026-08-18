"""Tests for the auth.cli.__main__ seed-sahayak CLI."""

from __future__ import annotations

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Set BEFORE importing main — storage.config.settings is a module-level
# singleton that reads os.environ at import time.
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://localhost/testdb")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault(
    "ENCRYPTION_MASTER_KEY",
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
)
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-at-least-32-chars-long")
os.environ.setdefault("SAHAYAK_EMAIL", "sahayak@dnk.gov.in")
os.environ.setdefault("SAHAYAK_PASSWORD", "sahayak-secret-123")
os.environ.setdefault("DEMO_SELLER_EMAIL", "seller@test.com")
os.environ.setdefault("DEMO_SELLER_PASSWORD", "test123")
os.environ.setdefault("DEMO_BUYER_EMAIL", "buyer@test.com")
os.environ.setdefault("DEMO_BUYER_PASSWORD", "test123")

from auth.cli.__main__ import main  # noqa: I001


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_session(return_value: object | None = None) -> MagicMock:
    mock_result = MagicMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=return_value)

    mock_session = AsyncMock()
    mock_session.execute = AsyncMock(return_value=mock_result)
    mock_session.commit = AsyncMock()
    mock_session.add = MagicMock()
    return mock_session


# ---------------------------------------------------------------------------
# First run (user does not exist yet)
# ---------------------------------------------------------------------------


def test_seed_sahayak_first_run(capsys: pytest.CaptureFixture[str]) -> None:
    mock_session = _make_mock_session(return_value=None)

    with patch(
        "auth.cli.__main__.get_session",
        return_value=lambda: AsyncMock(
            __aenter__=AsyncMock(return_value=mock_session),
            __aexit__=AsyncMock(return_value=None),
        ),
    ):
        main(["seed-sahayak"])

        mock_session.add.assert_called_once()
        mock_session.commit.assert_awaited_once()

    captured = capsys.readouterr()
    from storage.config import settings

    assert f"Sahayak account created: {settings.SAHAYAK_EMAIL}" in captured.out


def test_seed_sahayak_first_run_user_fields() -> None:
    mock_session = _make_mock_session(return_value=None)

    with patch(
        "auth.cli.__main__.get_session",
        return_value=lambda: AsyncMock(
            __aenter__=AsyncMock(return_value=mock_session),
            __aexit__=AsyncMock(return_value=None),
        ),
    ):
        main(["seed-sahayak"])

    added_user = mock_session.add.call_args[0][0]
    from storage.config import settings

    assert added_user.email == settings.SAHAYAK_EMAIL
    assert added_user.role.value == "sahayak"
    assert added_user.is_active is True
    assert added_user.email_verified is True
    assert added_user.password_hash.startswith("$2")


# ---------------------------------------------------------------------------
# Idempotent second run
# ---------------------------------------------------------------------------


def test_seed_sahayak_already_exists(capsys: pytest.CaptureFixture[str]) -> None:
    mock_existing_user = MagicMock()
    mock_session = _make_mock_session(return_value=mock_existing_user)

    with patch(
        "auth.cli.__main__.get_session",
        return_value=lambda: AsyncMock(
            __aenter__=AsyncMock(return_value=mock_session),
            __aexit__=AsyncMock(return_value=None),
        ),
    ):
        main(["seed-sahayak"])

        mock_session.add.assert_not_called()
        mock_session.commit.assert_not_called()

    captured = capsys.readouterr()
    from storage.config import settings

    assert f"Sahayak account already exists: {settings.SAHAYAK_EMAIL}" in captured.out


# ---------------------------------------------------------------------------
# Missing environment variables
# ---------------------------------------------------------------------------


def test_seed_sahayak_missing_email() -> None:
    with patch("auth.cli.__main__.settings") as mock_settings:
        mock_settings.SAHAYAK_EMAIL = ""
        mock_settings.SAHAYAK_PASSWORD = "sahayak-secret-123"
        with pytest.raises(SystemExit) as exc_info:
            main(["seed-sahayak"])
        assert exc_info.value.code == 1


def test_seed_sahayak_missing_password() -> None:
    with patch("auth.cli.__main__.settings") as mock_settings:
        mock_settings.SAHAYAK_EMAIL = "sahayak@dnk.gov.in"
        mock_settings.SAHAYAK_PASSWORD = ""
        with pytest.raises(SystemExit) as exc_info:
            main(["seed-sahayak"])
        assert exc_info.value.code == 1


# ---------------------------------------------------------------------------
# Unknown subcommand
# ---------------------------------------------------------------------------


def test_unknown_subcommand() -> None:
    with pytest.raises(SystemExit):
        main(["bogus-command"])
