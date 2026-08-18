"""Tests for the doc-time free-text translation orchestration.

Covers:
- is_latin_free_text: Latin passthrough vs Devanagari detection
- ensure_english_free_text: all-Latin → no API call; non-Latin → ONE batched
  call, write-through Redis cache (i18n:transliterate:{text}, 30d TTL);
  cache hit → no call; upstream failure → raw fallback, never raises.
"""

from __future__ import annotations


import pytest

from app.services.translation import (
    I18N_CACHE_PREFIX,
    ensure_english_free_text,
    is_latin_free_text,
)


class _FakeTranslationClient:
    """Records transliterate_batch calls; returns a canned mapping."""

    def __init__(self, result: dict[str, str] | None = None) -> None:
        self.calls: list[list[tuple[str, str]]] = []
        self.result = result or {}
        self.raise_error: Exception | None = None

    async def transliterate_batch(
        self, items: list[tuple[str, str]]
    ) -> dict[str, str]:
        self.calls.append(items)
        if self.raise_error is not None:
            raise self.raise_error
        return {
            key: self.result.get(key, f"EN[{text}]")
            for key, text in items
        }


class _FakeRedis:
    """Minimal async redis stand-in for cache assertions."""

    def __init__(self) -> None:
        self.store: dict[str, tuple[str, int | None]] = {}
        self.set_calls: list[tuple[str, str, int | None]] = []

    async def get(self, key: str) -> str | None:
        entry = self.store.get(key)
        return entry[0] if entry else None

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = (value, ex)
        self.set_calls.append((key, value, ex))


# ---------------------------------------------------------------------------
# is_latin_free_text
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("Acme Corp, New York", True),
        ("Shikha Sharma", True),
        ("O'Brien - LLC 123", True),
        ("शिखा", False),
        ("रमेश कुमार", False),
        ("Acme Corp, नई दिल्ली", False),
        ("", True),
        ("   ", True),
    ],
)
def test_is_latin_free_text(text: str, expected: bool) -> None:
    assert is_latin_free_text(text) is expected


# ---------------------------------------------------------------------------
# ensure_english_free_text
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_latin_items_make_no_api_call() -> None:
    client = _FakeTranslationClient()
    result = await ensure_english_free_text(
        [("consignee", "Acme Corp, New York"), ("note", "Shikha Sharma")],
        client=client,
    )
    assert result == {
        "consignee": "Acme Corp, New York",
        "note": "Shikha Sharma",
    }
    assert client.calls == []


@pytest.mark.asyncio
async def test_non_latin_items_are_batched_into_one_call() -> None:
    client = _FakeTranslationClient()
    result = await ensure_english_free_text(
        [("consignee", "शिखा"), ("note", "रमेश कुमार")],
        client=client,
    )
    assert len(client.calls) == 1
    assert client.calls[0] == [("consignee", "शिखा"), ("note", "रमेश कुमार")]
    assert result == {
        "consignee": "EN[शिखा]",
        "note": "EN[रमेश कुमार]",
    }


@pytest.mark.asyncio
async def test_mixed_items_only_batch_non_latin() -> None:
    client = _FakeTranslationClient()
    result = await ensure_english_free_text(
        [("consignee", "शिखा"), ("note", "Acme Corp, New York")],
        client=client,
    )
    assert len(client.calls) == 1
    assert client.calls[0] == [("consignee", "शिखा")]
    assert result["note"] == "Acme Corp, New York"
    assert result["consignee"] == "EN[शिखा]"


@pytest.mark.asyncio
async def test_cache_hit_skips_api_call() -> None:
    redis = _FakeRedis()
    redis.store[f"{I18N_CACHE_PREFIX}शिखा"] = ("Shikha", 30 * 24 * 3600)
    client = _FakeTranslationClient()
    result = await ensure_english_free_text(
        [("consignee", "शिखा")],
        redis=redis,
        client=client,
    )
    assert client.calls == []
    assert result == {"consignee": "Shikha"}


@pytest.mark.asyncio
async def test_cache_write_through_with_30d_ttl() -> None:
    redis = _FakeRedis()
    client = _FakeTranslationClient(result={"consignee": "Shikha"})
    result = await ensure_english_free_text(
        [("consignee", "शिखा")],
        redis=redis,
        client=client,
    )
    assert result == {"consignee": "Shikha"}
    assert redis.store[f"{I18N_CACHE_PREFIX}शिखा"] == ("Shikha", 30 * 24 * 3600)


@pytest.mark.asyncio
async def test_upstream_failure_falls_back_to_raw() -> None:
    client = _FakeTranslationClient()
    client.raise_error = RuntimeError("voice-pipeline down")
    result = await ensure_english_free_text(
        [("consignee", "शिखा")],
        client=client,
    )
    assert result == {"consignee": "शिखा"}


@pytest.mark.asyncio
async def test_empty_items_returns_empty() -> None:
    client = _FakeTranslationClient()
    result = await ensure_english_free_text([], client=client)
    assert result == {}
    assert client.calls == []
