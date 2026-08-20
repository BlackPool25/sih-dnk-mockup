"""Sarvam Bulbul:v2 mock TTS wrapper — per-field Hindi hints.

Live call only when SARVAM_API_KEY is set and network reachable;
otherwise returns a mocked ``mock://bulbul/{field}`` URL (best-effort,
never raises). All values mocked and labelled.
"""

from __future__ import annotations

import os
from typing import Final

import httpx

_MOCK_PREFIX: Final[str] = "mock://bulbul"
_SARVAM_TTS_URL: Final[str] = "https://api.sarvam.ai/text-to-speech"
_SARVAM_MODEL: Final[str] = "bulbul:v2"
_TIMEOUT: Final[float] = 5.0


def _is_mock_mode(api_key: str | None = None) -> bool:
    key = api_key if api_key is not None else os.getenv("SARVAM_API_KEY")
    return not bool(key and key.strip())


def tts_url_for_field(
    field: str,
    text: str,
    *,
    api_key: str | None = None,
) -> str:
    """Return a TTS URL for *field* — mocked unless a live key is configured.

    Best-effort: never raises, never blocks signup. When a key exists we
    attempt a live call but still fall back to the mock URL on any failure.
    """
    mock_url = f"{_MOCK_PREFIX}/{field}"
    if _is_mock_mode(api_key):
        return mock_url
    key = api_key or os.getenv("SARVAM_API_KEY", "")
    try:
        with httpx.Client(timeout=_TIMEOUT) as client:
            resp = client.post(
                _SARVAM_TTS_URL,
                headers={"api-subscription-key": key},
                json={
                    "text": text,
                    "model": _SARVAM_MODEL,
                    "target_language_code": "hi-IN",
                },
            )
        if resp.status_code < 400:
            data = resp.json()
            url = data.get("audio_url") or data.get("url") or data.get("tts_url")
            if isinstance(url, str) and url:
                return url
    except Exception:
        pass
    return mock_url


async def tts_url_for_field_async(
    field: str,
    text: str,
    *,
    api_key: str | None = None,
) -> str:
    mock_url = f"{_MOCK_PREFIX}/{field}"
    if _is_mock_mode(api_key):
        return mock_url
    key = api_key or os.getenv("SARVAM_API_KEY", "")
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.post(
                _SARVAM_TTS_URL,
                headers={"api-subscription-key": key},
                json={
                    "text": text,
                    "model": _SARVAM_MODEL,
                    "target_language_code": "hi-IN",
                },
            )
        if resp.status_code < 400:
            data = resp.json()
            url = data.get("audio_url") or data.get("url") or data.get("tts_url")
            if isinstance(url, str) and url:
                return url
    except Exception:
        pass
    return mock_url


__all__ = ["tts_url_for_field", "tts_url_for_field_async"]
