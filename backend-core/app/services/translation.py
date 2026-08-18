"""Doc-time free-text translation orchestration.

Every free-text value that reaches the validation engine and the generated
documents MUST be English (Latin script).  Session state stays Hindi-first;
English is derived here, at the boundary where an order is created.

Strategy:
- ``is_latin_free_text`` — cheap script check; Latin values pass through
  untouched (no API call).
- ``ensure_english_free_text`` — non-Latin values are transliterated through
  the voice-pipeline /translate/text endpoint in ONE batched call, cached in
  Redis under ``i18n:transliterate:{text}`` for 30 days (write-through).
  Any failure falls back to the raw value and logs — translation NEVER blocks
  order creation.
"""

from __future__ import annotations

import logging
import re
from typing import Any

import redis.asyncio as redis

import httpx

from storage.config import settings

logger = logging.getLogger(__name__)

_READ_TIMEOUT = 60.0

# Latin-script free-text guard: letters, digits, spaces and common punctuation.
_LATIN_FREE_TEXT_RE = re.compile(r"^[A-Za-z0-9 ,.'-]+$")

# Cache namespace for transliterated free-text values (kind=transliterate).
I18N_CACHE_PREFIX = "i18n:transliterate:"
I18N_CACHE_TTL_SECONDS = 30 * 24 * 3600  # 30 days


def is_latin_free_text(text: str | None) -> bool:
    """True when the text is already Latin-script English (or empty)."""
    if not text:
        return True
    stripped = text.strip()
    if not stripped:
        return True
    return bool(_LATIN_FREE_TEXT_RE.match(stripped))


class TranslationError(Exception):
    """Base for voice-pipeline translation client errors."""


class TranslationUnavailable(TranslationError):
    """voice-pipeline unreachable or errored."""


class TranslationClient:
    """Thin async httpx wrapper over the voice-pipeline /translate/text API."""

    def __init__(
        self,
        base_url: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = (base_url or settings.VOICE_PIPELINE_URL).rstrip("/")
        self._transport = transport

    async def transliterate_batch(
        self, items: list[tuple[str, str]]
    ) -> dict[str, str]:
        """POST /translate/text — batch transliteration, key → English text."""
        payload = {
            "items": [
                {"key": key, "text": text, "kind": "transliterate"}
                for key, text in items
            ]
        }
        client_kwargs: dict[str, Any] = {"timeout": _READ_TIMEOUT}
        if self._transport is not None:
            client_kwargs["transport"] = self._transport
        try:
            async with httpx.AsyncClient(**client_kwargs) as client:
                resp = await client.post(
                    f"{self._base_url}/translate/text", json=payload
                )
        except httpx.ConnectError as exc:
            raise TranslationUnavailable(f"voice-pipeline unreachable: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise TranslationUnavailable(f"voice-pipeline timed out: {exc}") from exc
        if resp.status_code >= 400:
            raise TranslationUnavailable(
                f"voice-pipeline error {resp.status_code}"
            )
        data = resp.json()
        items_out = data.get("items", [])
        return {
            item["key"]: item["english"] for item in items_out
        }


async def _cache_get(
    redis: redis.Redis | None, text: str
) -> str | None:
    """Read a cached transliteration; None on miss or any redis failure."""
    if redis is None:
        return None
    try:
        value = await redis.get(f"{I18N_CACHE_PREFIX}{text}")
        return value if isinstance(value, str) else None
    except Exception:  # noqa: BLE001 — cache must never block doc flow
        logger.warning("i18n cache read failed, skipping", exc_info=True)
        return None


async def _cache_set(redis: redis.Redis | None, text: str, english: str) -> None:
    """Write-through a transliteration; never raises."""
    if redis is None:
        return
    try:
        await redis.set(
            f"{I18N_CACHE_PREFIX}{text}", english, ex=I18N_CACHE_TTL_SECONDS
        )
    except Exception:  # noqa: BLE001 — cache must never block doc flow
        logger.warning("i18n cache write failed, skipping", exc_info=True)


async def ensure_english_free_text(
    items: list[tuple[str, str]],
    *,
    redis: redis.Redis | None = None,
    client: TranslationClient | None = None,
) -> dict[str, str]:
    """Map free-text (key, value) pairs to English.

    Latin values pass through.  Non-Latin values are transliterated in one
    batched call and cached.  On ANY failure the raw value is returned — order
    creation and doc generation are never blocked by translation.
    """
    client = client or _default_client()
    english: dict[str, str] = {}
    needs_transliteration: list[tuple[str, str]] = []

    for key, text in items:
        if is_latin_free_text(text):
            english[key] = text
            continue
        cached = await _cache_get(redis, text)
        if cached is not None:
            english[key] = cached
        else:
            needs_transliteration.append((key, text))

    if not needs_transliteration:
        return english

    try:
        translated = await client.transliterate_batch(needs_transliteration)
    except Exception as exc:  # noqa: BLE001 — translation never blocks doc flow
        logger.warning("transliteration failed (%s); using raw values", exc)
        for key, text in needs_transliteration:
            english[key] = text
        return english

    for key, text in needs_transliteration:
        value = translated.get(key)
        if value is None:
            logger.warning("no transliteration for %r; using raw value", key)
            english[key] = text
        else:
            english[key] = value
            await _cache_set(redis, text, value)
    return english


_default_client_instance: TranslationClient | None = None


def _default_client() -> TranslationClient:
    global _default_client_instance
    if _default_client_instance is None:
        _default_client_instance = TranslationClient()
    return _default_client_instance


__all__ = [
    "I18N_CACHE_PREFIX",
    "I18N_CACHE_TTL_SECONDS",
    "TranslationClient",
    "TranslationError",
    "TranslationUnavailable",
    "ensure_english_free_text",
    "is_latin_free_text",
]
