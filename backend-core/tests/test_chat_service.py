"""chat service — turn-loop orchestration.

Pins: full-turn flow (extract → validate → reply → persist), category
disambiguation path (no validation), business-error field priority, and the
reply echo/ask composition.  Uses a fake ValClient (no network) and a fake
async redis (dict-backed).
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.schemas.llm import ChatRequest
from app.services.chat import (
    build_reply,
    load_state,
    merge_draft,
    new_conversation_id,
    pending_fields,
    pick_next_field,
    run_turn,
)
from app.services.llm_reply import FIELD_ORDER
from tests.fake_val_client import FakeValClient

CATEGORY = "jute-products"


class FakeRedis:
    """Minimal async redis double (dict + expire).  ``expired`` records every
    (key, ttl) so tests can pin that the session TTL is set/refreshed."""

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


def _state(user_id: str = "u1", language: str = "hi") -> dict[str, Any]:
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


def test_pending_fields_order_category_first() -> None:
    pending = pending_fields({})
    assert pending == [
        "product_category",
        "destination_country",
        "quantity",
        "weight_grams",
        "value_minor",
        "consignee",
    ]


def test_merge_draft_never_overwrites_with_sentinel() -> None:
    merged = merge_draft(
        {"quantity": 12, "destination_country": "DE"},
        {"quantity": -1, "weight_grams": 500},
    )
    assert merged["quantity"] == 12  # previous kept — sentinel ignored
    assert merged["weight_grams"] == 500  # new non-sentinel wins


def test_pick_next_field_business_error_wins() -> None:
    draft = {"quantity": 99999}
    report = {"business_errors": [{"field": "quantity", "message": "too big"}]}
    assert pick_next_field(draft, report) == "quantity"


def test_pick_next_field_head_of_pending() -> None:
    draft = {"product_category": "jute-products"}
    assert pick_next_field(draft, None) == "destination_country"


def test_build_reply_echoes_and_asks() -> None:
    reply = build_reply(
        "hi",
        {"product_category": "jute-products", "quantity": 12},
        {"category_name": "Jute Products"},
        "destination_country",
        [],
    )
    assert "मैंने समझा" in reply
    assert "Jute Products" in reply
    assert "12" in reply
    assert "किस देश" in reply


def test_build_reply_ready_when_complete() -> None:
    draft = {
        "product_category": "jute-products",
        "quantity": 12,
        "weight_grams": 500,
        "destination_country": "DE",
        "value_minor": 1500000,
        "consignee": "John Doe, 123 Berlin Str",
    }
    reply = build_reply("hi", draft, {"category_name": "Jute Products"}, None, [])
    assert "तैयार है" in reply


def test_disambiguation_reply_with_candidates_lists_options() -> None:
    from app.services.chat import disambiguation_reply

    candidates = [{"slug": "jute-products", "name": "Jute Products"}, {"slug": "small-woodware", "name": "Small Woodware"}]
    reply = disambiguation_reply("hi", candidates)
    assert "कृपया चुनें" in reply
    assert "1) Jute Products" in reply
    assert "2) Small Woodware" in reply


def test_disambiguation_reply_without_candidates_asks_category() -> None:
    from app.services.chat import disambiguation_reply

    reply = disambiguation_reply("hi", [])
    assert "किस उत्पाद श्रेणी" in reply
    assert "तैयार है" not in reply  # never the ready message mid-collection


def test_full_turn_extract_validate_reply_persist() -> None:
    client = FakeValClient()
    redis = FakeRedis()
    conv_id = new_conversation_id()
    state = _state()
    body = ChatRequest(message="12 जूट बैग जर्मनी भेजने हैं 500 ग्राम 15000 रुपये", language="hi")

    resp = _run(run_turn(user_id="u1", body=body, conv_id=conv_id, state=state, redis=redis, val_client=client))

    assert client.calls == ["extract", "validate"]
    assert resp.filled_fields["product_category"] == CATEGORY
    assert resp.filled_fields["quantity"] == 12
    assert resp.filled_fields["destination_country"] == "DE"
    assert resp.filled_fields["value_minor"] == 1500000
    assert resp.document_ready is False  # consignee still missing
    assert resp.current_step == "consignee"
    assert "मैंने समझा" in resp.reply_text
    assert resp.tts_hint["enabled"] is True
    # Persisted to redis under the conv key
    saved = _run(redis.hgetall(f"chat_session:{conv_id}"))
    assert saved  # non-empty
    assert len(resp.history) == 2  # user + assistant


def test_turn_completes_to_ready() -> None:
    client = FakeValClient()
    redis = FakeRedis()
    conv_id = new_conversation_id()
    state = _state()

    turn1 = ChatRequest(
        message="12 जूट बैग जर्मनी भेजने हैं 500 ग्राम 15000 रुपये जॉन डो 123 बर्लिन", language="hi"
    )
    resp1 = _run(
        run_turn(user_id="u1", body=turn1, conv_id=conv_id, state=state, redis=redis, val_client=client)
    )
    assert resp1.document_ready is True
    assert resp1.current_step == "done"
    assert "तैयार है" in resp1.reply_text


def test_category_disambiguation_no_validation() -> None:
    client = FakeValClient()
    client.category_unknown = True
    redis = FakeRedis()
    conv_id = new_conversation_id()
    state = _state()
    body = ChatRequest(message="मुझे कुछ सामान भेजना है", language="hi")

    resp = _run(run_turn(user_id="u1", body=body, conv_id=conv_id, state=state, redis=redis, val_client=client))

    assert client.calls == ["extract", "search_categories"]
    assert "validate" not in client.calls
    assert resp.current_step == "category_disambiguation"
    assert "कृपया चुनें" in resp.reply_text
    assert resp.validation_report is None


def test_category_disambiguation_preserves_partial_draft() -> None:
    """Fields extracted before the category failed (country) survive the
    disambiguation turn — the caller must not drop the turn's progress."""
    class _PartialClient(FakeValClient):
        category_unknown = True

        async def extract(self, text, lang, previous=None, expected=None):
            from app.services.val_client import ExtractResult

            return ExtractResult(
                draft={"destination_country": "US", "weight_grams": 500},
                category_unknown=True,
                extractor="rule",
            )

    redis = FakeRedis()
    conv_id = new_conversation_id()
    state = _state()
    body = ChatRequest(message="मुझे कुछ सामान भेजना है अमेरिका", language="hi")

    resp = _run(
        run_turn(
            user_id="u1", body=body, conv_id=conv_id, state=state, redis=redis,
            val_client=_PartialClient(),
        )
    )
    assert resp.filled_fields["destination_country"] == "US"
    assert resp.filled_fields["weight_grams"] == 500
    assert resp.current_step == "category_disambiguation"


def test_category_pick_resolution_via_number() -> None:
    from app.services.chat import _resolve_category_pick

    candidates = [{"slug": "jute-products"}, {"slug": "small-woodware"}]
    assert _resolve_category_pick("1", candidates) == "jute-products"
    assert _resolve_category_pick("2", candidates) == "small-woodware"
    assert _resolve_category_pick("3", candidates) is None
    assert _resolve_category_pick("जूट", candidates) is None


def test_run_turn_passes_next_field_to_enricher(monkeypatch) -> None:
    """The Gemini enricher receives the pending field so it can ask exactly
    one targeted question (Wave 1 T1 persona prompt)."""
    captured: dict[str, object] = {}

    class _SpyEnricher:
        def __init__(self, api_key: str | None = None) -> None:
            pass

        def enrich(self, lang, template_text, draft, db_info, next_field=None):
            captured["lang"] = lang
            captured["next_field"] = next_field
            return "spy reply"

    monkeypatch.setattr("app.services.chat.GeminiEnricher", _SpyEnricher)
    client = FakeValClient()
    redis = FakeRedis()
    conv_id = new_conversation_id()
    state = _state()
    body = ChatRequest(message="12 जूट बैग जर्मनी भेजने हैं 500 ग्राम 15000 रुपये", language="hi")

    resp = _run(
        run_turn(user_id="u1", body=body, conv_id=conv_id, state=state, redis=redis, val_client=client)
    )
    assert resp.reply_text == "spy reply"
    assert captured["lang"] == "hi"
    assert captured["next_field"] == "consignee"  # the pending field this turn asks


def test_redis_state_round_trip_validated_only() -> None:
    """The persisted Redis state round-trips: filled_fields holds only
    validated values (unstated fields stay sentinels/absent), the
    validation_report survives, and the session TTL is set/refreshed."""
    from storage.config import settings

    client = FakeValClient()
    redis = FakeRedis()
    conv_id = new_conversation_id()
    state = _state()
    body = ChatRequest(message="12 जूट बैग जर्मनी भेजने हैं 500 ग्राम 15000 रुपये", language="hi")
    _run(run_turn(user_id="u1", body=body, conv_id=conv_id, state=state, redis=redis, val_client=client))

    # a second turn refreshes the TTL
    _run(
        run_turn(
            user_id="u1",
            body=ChatRequest(message="बस यही है", language="hi"),
            conv_id=conv_id,
            state=state,
            redis=redis,
            val_client=client,
        )
    )

    loaded = _run(load_state(redis, conv_id))
    assert loaded is not None
    # every field is a validated value or an unstated sentinel — never garbage
    sentinels = (-1, "unknown", None)
    for field in FIELD_ORDER:
        value = loaded["filled_fields"].get(field)
        assert value not in sentinels or value is None, f"{field} holds a sentinel"
    assert loaded["filled_fields"]["product_category"] == "jute-products"
    assert loaded["filled_fields"]["quantity"] == 12
    assert loaded["filled_fields"]["weight_grams"] == 500
    assert loaded["filled_fields"]["destination_country"] == "DE"
    assert loaded["filled_fields"]["value_minor"] == 1500000
    assert loaded["filled_fields"].get("consignee") is None  # unstated → absent
    # the validation_report round-trips with its PBE-keyed shape
    assert loaded["validation_report"] is not None
    assert loaded["validation_report"]["document_ready"] is False
    assert "missing_required" in loaded["validation_report"]
    # TTL set (first save) and refreshed (second save)
    key = f"chat_session:{conv_id}"
    ttl = settings.LLM_CONVERSATION_TTL_HOURS * 3600
    assert redis.expired.count((key, ttl)) == 2


def test_validation_report_reaches_reply_generator() -> None:
    """The report's db_info flows into the reply generator: the category
    display name (from the report) is echoed, not the raw slug."""
    client = FakeValClient()
    redis = FakeRedis()
    conv_id = new_conversation_id()
    state = _state()
    body = ChatRequest(message="12 लकड़ी के खिलौने 500 ग्राम जर्मनी ₹15000", language="hi")

    resp = _run(run_turn(user_id="u1", body=body, conv_id=conv_id, state=state, redis=redis, val_client=client))

    assert resp.filled_fields["product_category"] == "small-woodware"
    assert "Small Woodware" in resp.reply_text
    assert "small-woodware" not in resp.reply_text  # the name resolved, not the slug
