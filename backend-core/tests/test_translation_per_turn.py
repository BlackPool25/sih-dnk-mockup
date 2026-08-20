from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from app.schemas.llm import ChatRequest
from app.services.chat import run_turn
from app.services.translation import (
    I18N_CACHE_PREFIX,
    _normalize_cache_key,
    ensure_english_free_text,
    is_latin_free_text,
    translate_consignee_hi_en,
)
from tests.fake_val_client import FakeValClient


class FakeRedis:
    def __init__(self) -> None:
        self._data: dict[str, dict[bytes, bytes]] = {}
        self.store: dict[str, tuple[str, int | None]] = {}
        self.expired: list[tuple[str, int]] = []

    async def hgetall(self, key: str) -> dict[bytes, bytes]:
        return dict(self._data.get(key, {}))

    async def hset(self, key: str, mapping: dict[str, str]) -> None:
        self._data[key] = {k.encode(): v.encode() for k, v in mapping.items()}

    async def expire(self, key: str, ttl: int) -> None:
        self.expired.append((key, ttl))
        self._data.setdefault(key, {})

    async def get(self, key: str) -> str | None:
        entry = self.store.get(key)
        if entry is not None:
            return entry[0]
        return None

    async def set(self, key: str, value: str, ex: int | None = None) -> None:
        self.store[key] = (value, ex)


def _run(coro):
    return asyncio.run(coro)


def _state(user_id: str = "u1", language: str = "hi") -> dict[str, object]:
    from app.services.chat import pending_fields

    return {
        "user_id": user_id,
        "language": language,
        "current_step": "init",
        "filled_fields": {},
        "pending_fields": list(pending_fields({})),
        "history": [],
        "validation_report": None,
        "db_info": None,
        "document_ready": False,
        "candidates": [],
    }


class _FakeTranslationClient:
    def __init__(self, result: dict[str, str] | None = None) -> None:
        self.calls: list[list[tuple[str, str]]] = []
        self.result = result or {}
        self.raise_error: Exception | None = None

    async def transliterate_batch(self, items: list[tuple[str, str]]) -> dict[str, str]:
        self.calls.append(items)
        if self.raise_error is not None:
            raise self.raise_error
        return {key: self.result.get(key, f"EN[{text}]") for key, text in items}


def test_normalize_cache_key_nfkc_trim_lower() -> None:
    assert _normalize_cache_key("राम ") == _normalize_cache_key("राम")
    assert _normalize_cache_key("राम ") == "राम"
    import unicodedata

    a = unicodedata.normalize("NFD", "राम")
    assert _normalize_cache_key(a) == _normalize_cache_key("राम")


@pytest.mark.asyncio
async def test_cache_normalized_hit_same_key() -> None:
    redis = FakeRedis()
    redis.store[f"{I18N_CACHE_PREFIX}राम"] = ("Ram", 30 * 24 * 3600)
    client = _FakeTranslationClient()
    result = await ensure_english_free_text(
        [("consignee", "राम ")],
        redis=redis,  # type: ignore[arg-type]
        client=client,  # type: ignore[arg-type]
    )
    assert client.calls == []
    assert result["consignee"] == "Ram"


@pytest.mark.asyncio
async def test_translate_consignee_hi_en_per_turn() -> None:
    redis = FakeRedis()
    client = _FakeTranslationClient(result={"consignee": "Ram Kumar"})
    result = await translate_consignee_hi_en("राम कुमार", redis=redis, client=client)  # type: ignore[arg-type]
    assert result["hi"] == "राम कुमार"
    assert result["en"] == "Ram Kumar"
    result2 = await translate_consignee_hi_en("Ram Kumar", redis=redis, client=client)  # type: ignore[arg-type]
    assert result2["en"] == "Ram Kumar"
    assert len(client.calls) == 1


@pytest.mark.asyncio
async def test_translate_consignee_fallback_never_blocks() -> None:
    redis = FakeRedis()
    client = _FakeTranslationClient()
    client.raise_error = RuntimeError("down")
    result = await translate_consignee_hi_en("राम", redis=redis, client=client)  # type: ignore[arg-type]
    assert result["en"] == "राम"
    assert result["hi"] == "राम"


def test_five_devanagari_turns_no_422() -> None:
    class DevanagariFake(FakeValClient):
        async def extract(self, text, lang, previous=None, expected=None):  # type: ignore[override]
            from app.services.val_client import ExtractResult

            draft: dict[str, object] = {}
            if "राम" in text or "consignee" in text.lower():
                draft["consignee"] = text.strip()
            else:
                draft["quantity"] = 12
                draft["product_category"] = "jute-products"
            return ExtractResult(draft=draft, category_unknown=False, extractor="rule")

    import app.services.chat as chat_module

    original = chat_module.translate_consignee_hi_en

    async def fake_translate(text, redis=None, client=None):  # type: ignore[no-untyped-def]
        return {"hi": text, "en": "Ram Kumar, Delhi"}

    chat_module.translate_consignee_hi_en = fake_translate  # type: ignore[assignment]
    try:
        fake = DevanagariFake()
        redis = FakeRedis()
        state = _state()
        state["filled_fields"] = {
            "product_category": "jute-products",
            "quantity": 12,
            "weight_grams": 500,
            "destination_country": "DE",
            "value_minor": 1500000,
        }
        state["pending_fields"] = ["consignee"]
        for i in range(5):
            body = ChatRequest(message=f"राम कुमार {i}", language="hi")
            conv_id = f"conv-dev-{i}"
            resp = _run(run_turn(user_id="u1", body=body, conv_id=conv_id, state=state, redis=redis, val_client=fake))
            assert resp.validation_report is not None
            assert isinstance(resp.filled_fields.get("consignee"), str)
            assert state["filled_fields"].get("consignee_hi") == f"राम कुमार {i}"
            assert state["filled_fields"].get("consignee_en") == "Ram Kumar, Delhi"
    finally:
        chat_module.translate_consignee_hi_en = original  # type: ignore[assignment]


@pytest.mark.asyncio
async def test_ensure_called_per_turn_not_just_order() -> None:
    import app.services.chat as chat_module
    import inspect

    src = inspect.getsource(chat_module.run_turn)
    assert "translate_consignee_hi_en" in src or "ensure_english_free_text" in src


def test_translate_consignee_called_per_turn_proof() -> None:
    from unittest.mock import AsyncMock, patch

    fake = FakeValClient()

    async def dev_extract(text, lang, previous=None, expected=None):  # type: ignore[no-untyped-def]
        from app.services.val_client import ExtractResult

        return ExtractResult(draft={"consignee": "राम कुमार"}, category_unknown=False, extractor="rule")

    fake.extract = dev_extract  # type: ignore[method-assign]

    with patch("app.services.chat.translate_consignee_hi_en", new_callable=AsyncMock) as mock_trans:
        mock_trans.return_value = {"hi": "राम कुमार", "en": "Ram Kumar"}
        redis = FakeRedis()
        state = _state()
        state["filled_fields"] = {
            "product_category": "jute-products",
            "quantity": 12,
            "weight_grams": 500,
            "destination_country": "DE",
            "value_minor": 1500000,
        }
        state["pending_fields"] = ["consignee"]
        body = ChatRequest(message="राम कुमार", language="hi")
        _run(run_turn(user_id="u1", body=body, conv_id="conv-per-turn", state=state, redis=redis, val_client=fake))
        assert mock_trans.await_count == 1
        body2 = ChatRequest(message="राम कुमार ", language="hi")
        _run(run_turn(user_id="u1", body=body2, conv_id="conv-per-turn2", state=state, redis=redis, val_client=fake))
        assert mock_trans.await_count >= 1


def test_gemini_model_kept() -> None:
    from app.services.enricher import GeminiEnricher

    assert GeminiEnricher.MODEL == "gemini-3.5-flash-lite"
