"""Shared test fixtures — deterministic env and module caches for the voice-pipeline suite."""

import pytest

from app import sarvam


@pytest.fixture(autouse=True)
def _isolated_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear the API key env var and Sarvam client cache so tests opt in explicitly."""
    monkeypatch.delenv("SARVAM_API_KEY", raising=False)
    sarvam._sarvam_client = None
