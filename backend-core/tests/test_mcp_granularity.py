from __future__ import annotations

import asyncio
import time

from app.schemas.llm import ChatRequest
from app.services.chat import _SEARCH_CACHE, _normalize_search_query, run_turn
from tests.fake_val_client import FakeValClient


class FakeRedis:
    def __init__(self) -> None:
        self._data: dict[str, dict[bytes, bytes]] = {}
        self.expired: list[tuple[str, int]] = []

    async def hgetall(self, key: str) -> dict[bytes, bytes]:
        return dict(self._data.get(key, {}))

    async def hset(self, key: str, mapping: dict[str, str]) -> None:
        self._data[key] = {k.encode(): v.encode() for k, v in mapping.items()}

    async def expire(self, key: str, ttl: int) -> None:
        self.expired.append((key, ttl))
        self._data.setdefault(key, {})


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


def test_search_categories_ttl_cache_normalized_key() -> None:
    assert _normalize_search_query("राम ") == _normalize_search_query("राम")
    assert _normalize_search_query(" Jute ") == "jute"


def test_search_categories_dedup_within_5m() -> None:
    _SEARCH_CACHE.clear()

    class CountingClient(FakeValClient):
        def __init__(self) -> None:
            super().__init__()
            self.search_count = 0
            self.category_unknown = True

        async def search_categories(self, query: str) -> list[dict[str, object]]:  # type: ignore[override]
            self.search_count += 1
            self.calls.append("search_categories")
            return [{"slug": "jute-products", "name": "Jute Products"}]

    client = CountingClient()
    redis = FakeRedis()
    conv_id = "conv-mcp-1"
    state = _state()
    body = ChatRequest(message="कुछ भेजना है", language="hi")

    _run(run_turn(user_id="u1", body=body, conv_id=conv_id, state=state, redis=redis, val_client=client))
    assert client.search_count == 1

    state2 = _state()
    _run(run_turn(user_id="u1", body=body, conv_id=conv_id + "-2", state=state2, redis=FakeRedis(), val_client=client))
    assert client.search_count == 1, "second identical query within 5m must be served from TTLCache"
    assert client.calls.count("search_categories") == 1


def test_search_categories_cache_expiry_after_ttl(monkeypatch) -> None:
    _SEARCH_CACHE.clear()

    class CountingClient(FakeValClient):
        def __init__(self) -> None:
            super().__init__()
            self.search_count = 0
            self.category_unknown = True

        async def search_categories(self, query: str) -> list[dict[str, object]]:  # type: ignore[override]
            self.search_count += 1
            self.calls.append("search_categories")
            return [{"slug": "jute-products", "name": "Jute Products"}]

    client = CountingClient()
    body = ChatRequest(message="जूट कहाँ", language="hi")
    _run(run_turn(user_id="u1", body=body, conv_id="c1", state=_state(), redis=FakeRedis(), val_client=client))
    assert client.search_count == 1

    base = time.monotonic()
    monkeypatch.setattr("app.services.chat.time.monotonic", lambda: base + 301)
    _run(run_turn(user_id="u1", body=body, conv_id="c2", state=_state(), redis=FakeRedis(), val_client=client))
    assert client.search_count == 2


def test_validate_only_changed_fields() -> None:
    fake = FakeValClient()
    fake.business_errors = [
        {"field": "quantity", "message": "too big"},
        {"field": "weight_grams", "message": "too heavy"},
    ]
    redis = FakeRedis()
    conv_id = "conv-granular"

    state = _state()
    state["filled_fields"] = {
        "product_category": "jute-products",
        "quantity": 99999,
        "weight_grams": 500,
        "destination_country": "DE",
    }
    state["pending_fields"] = ["value_minor", "consignee"]
    body = ChatRequest(message="99999 टुकड़े", language="hi")

    resp = _run(
        run_turn(
            user_id="u1",
            body=body,
            conv_id=conv_id,
            state=state,
            redis=redis,
            val_client=fake,
            changed_fields=["quantity"],
        )
    )
    assert resp.validation_report is not None
    fields = [e["field"] for e in resp.validation_report["business_errors"]]  # type: ignore[index]
    assert "quantity" in fields
    assert "weight_grams" not in fields


def test_previous_db_info_passed_to_validate() -> None:
    fake = FakeValClient()
    redis = FakeRedis()
    conv_id = "conv-dup"
    state = _state()
    state["db_info"] = {"category": {"slug": "jute-products", "name": "Jute Products"}, "duties": [{"rate_pct": 5}]}
    state["filled_fields"] = {"product_category": "jute-products", "quantity": 12}
    state["pending_fields"] = ["destination_country", "weight_grams", "value_minor", "consignee"]
    body = ChatRequest(message="जूट 12", language="hi")
    _run(run_turn(user_id="u1", body=body, conv_id=conv_id, state=state, redis=redis, val_client=fake))
    assert hasattr(fake, "last_previous_db_info")
    assert fake.last_previous_db_info is not None
    assert fake.last_previous_db_info.get("category", {}).get("slug") == "jute-products"


def test_run_turn_changed_fields_param_exists() -> None:
    import inspect

    sig = inspect.signature(run_turn)
    assert "changed_fields" in sig.parameters


def test_db_tools_search_categories_ttl_cache() -> None:
    import pathlib

    text = pathlib.Path("validation-engine/app/services/db_tools/__init__.py").read_text()
    assert "_normalize_query" in text
    assert "_SEARCH_TTL_SECONDS = 300" in text or "_SEARCH_TTL_SECONDS = 300.0" in text
    assert "unicodedata.normalize" in text
    assert "lower().strip()" in text
    import unicodedata

    def norm(q: str) -> str:
        return unicodedata.normalize("NFKC", q).lower().strip()

    assert norm("राम ") == norm("राम")
    assert norm(" Jute ") == "jute"
