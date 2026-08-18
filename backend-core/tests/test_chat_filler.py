"""Conversational filler + off-topic answer handling in run_turn (Wave 2).

Pins the acceptance contract for a demo-quality chat loop:

- Filler turns ("अरे भाई अच्छी बात हुई") that extract NOTHING new must NOT
  re-emit the previous turn's robotic echo — they get a warm varied
  acknowledgment plus a re-ask of the still-pending field.
- Two consecutive filler turns must produce DIFFERENT replies (variation).
- A filler-looking prefix carrying real data ("हाँ अमेरिका") is a data turn.
- An off-topic answer ("दो हज़ार पे" while weight is pending) keeps the
  volunteered field (never loses data) and re-asks the still-pending field
  with different phrasing.
- A consignee set this turn is read back once ("शिखा, सही?") folded into the
  next pending ask — the read-back is a single reply, not a blocking turn.

Mirrors test_chat_service.py: a fake ValClient + fake async redis, no network.
"""

from __future__ import annotations

import asyncio
from typing import Any

from app.schemas.llm import ChatRequest
from app.services.chat import new_conversation_id, run_turn

from tests.fake_val_client import FakeValClient
from tests.test_chat_service import FakeRedis

CATEGORY = "jute-products"


def _run(coro):
    return asyncio.run(coro)


def _state() -> dict[str, Any]:
    return {
        "user_id": "u1",
        "language": "hi",
        "current_step": "init",
        "filled_fields": {},
        "pending_fields": [],
        "history": [],
        "validation_report": None,
        "db_info": None,
        "document_ready": False,
        "candidates": [],
    }


def _turn(client: FakeValClient, redis: FakeRedis, conv_id: str, state: dict[str, Any], message: str):
    body = ChatRequest(message=message, conversation_id=conv_id, language="hi")
    return _run(
        run_turn(user_id="u1", body=body, conv_id=conv_id, state=state, redis=redis, val_client=client)
    )


def test_filler_turn_acks_and_reasks_varied() -> None:
    """Given a turn that extracts nothing new and a filler message, the reply
    is a warm varied acknowledgment + a re-ask of the pending country — NOT an
    identical robotic echo of the previous reply."""
    client = FakeValClient()
    redis = FakeRedis()
    conv_id = new_conversation_id()
    state = _state()

    resp1 = _turn(client, redis, conv_id, state, "जूट भेजना है")
    assert resp1.filled_fields["product_category"] == CATEGORY
    assert resp1.pending_fields[0] == "destination_country"

    resp2 = _turn(client, redis, conv_id, state, "अरे भाई अच्छी बात हुई")

    # the filler turn extracted nothing new
    assert resp2.filled_fields == resp1.filled_fields
    assert resp2.pending_fields == resp1.pending_fields
    # validation is skipped on a pure-filler turn (nothing to re-check)
    assert client.calls == ["extract", "validate", "extract"]
    # the reply is warm, acknowledges, still asks about the country, and is
    # NOT the previous robotic echo
    assert "समझ गया" in resp2.reply_text
    assert "देश" in resp2.reply_text
    assert resp2.reply_text != resp1.reply_text
    assert "मैंने समझा" not in resp2.reply_text
    # normal history + persist flow is preserved
    assert len(resp2.history) == 4  # user, assistant, user, assistant


def test_two_filler_turns_differ() -> None:
    """Two consecutive filler turns must get DIFFERENT phrasings — the exact
    bug being fixed is an identical robotic echo every turn."""
    client = FakeValClient()
    redis = FakeRedis()
    conv_id = new_conversation_id()
    state = _state()

    _turn(client, redis, conv_id, state, "जूट भेजना है")
    resp2 = _turn(client, redis, conv_id, state, "अरे भाई अच्छी बात हुई")
    resp3 = _turn(client, redis, conv_id, state, "अच्छा ठीक है")

    assert resp2.reply_text != resp3.reply_text
    assert "समझ गया" in resp2.reply_text
    assert "समझ गया" in resp3.reply_text
    assert "देश" in resp2.reply_text
    assert "देश" in resp3.reply_text
    assert resp2.filled_fields == resp3.filled_fields == {"product_category": CATEGORY}


def test_filler_with_real_data_not_flagged() -> None:
    """'हाँ अमेरिका' is filler + real country: extraction runs first and the
    turn is a normal DATA turn (country stored, next field asked), never the
    filler path."""

    class _USClient(FakeValClient):
        async def extract(self, text, lang, previous=None, expected=None):
            result = await super().extract(text, lang, previous, expected)
            if "अमेरिका" in text or "america" in text.lower():
                result.draft["destination_country"] = "US"
            return result

    client = _USClient()
    redis = FakeRedis()
    conv_id = new_conversation_id()
    state = _state()

    _turn(client, redis, conv_id, state, "जूट भेजना है")
    resp2 = _turn(client, redis, conv_id, state, "हाँ अमेरिका")

    # the country is stored and validation ran (a real data turn)
    assert resp2.filled_fields["destination_country"] == "US"
    assert client.calls.count("validate") == 2
    # normal echo + next-field ask, not the filler acknowledgment
    assert "मैंने समझा" in resp2.reply_text
    assert "अमेरिका" in resp2.reply_text
    assert "कितने टुकड़े" in resp2.reply_text  # asks quantity next


def test_offtopic_answer_stored_and_pending_reasked() -> None:
    """Weight is pending but the seller volunteers the value ('दो हज़ार पे'):
    the volunteered field is stored (never lost) and the STILL-pending weight
    is re-asked with different phrasing than the previous turn."""

    class _OfftopicClient(FakeValClient):
        async def extract(self, text, lang, previous=None, expected=None):
            result = await super().extract(text, lang, previous, expected)
            if "अमेरिका" in text or "america" in text.lower():
                result.draft["destination_country"] = "US"
            if "दो हज़ार" in text:
                result.draft["value_minor"] = 200000
            return result

    client = _OfftopicClient()
    redis = FakeRedis()
    conv_id = new_conversation_id()
    state = _state()

    resp1 = _turn(client, redis, conv_id, state, "जूट 12 अमेरिका भेजना है")
    assert resp1.pending_fields[0] == "weight_grams"  # weight is what we asked
    assert "कुल वज़न" in resp1.reply_text  # previous turn asked with the base phrasing

    resp2 = _turn(client, redis, conv_id, state, "दो हज़ार पे")

    # the volunteered value is kept — never lost
    assert resp2.filled_fields["value_minor"] == 200000
    # the reply acknowledges the stored field and re-asks the pending weight
    assert "नोट कर लिया" in resp2.reply_text
    assert "200000" in resp2.reply_text
    assert "वज़न" in resp2.reply_text
    # ... with DIFFERENT phrasing than the previous turn's question
    assert resp2.reply_text != resp1.reply_text
    assert "कुल वज़न" not in resp2.reply_text
    assert resp2.pending_fields[0] == "weight_grams"  # still pending


def test_consignee_readback_folded() -> None:
    """A consignee set THIS turn is read back once ('शिखा, सही?') folded into
    the next pending ask — one reply only; the next weight answer still
    advances the transcript normally."""

    class _ConsigneeClient(FakeValClient):
        async def extract(self, text, lang, previous=None, expected=None):
            result = await super().extract(text, lang, previous, expected)
            if "अमेरिका" in text or "america" in text.lower():
                result.draft["destination_country"] = "US"
            if "शिखा" in text:
                result.draft["consignee"] = "शिखा गुप्ता, 12 मुंबई"
            return result

    client = _ConsigneeClient()
    redis = FakeRedis()
    conv_id = new_conversation_id()
    state = _state()

    resp1 = _turn(client, redis, conv_id, state, "जूट 12 अमेरिका भेजना है")
    assert resp1.pending_fields[0] == "weight_grams"

    resp2 = _turn(client, redis, conv_id, state, "शिखा गुप्ता भेजना है")

    # consignee stored as spoken (Devanagari kept, no romanization)
    assert resp2.filled_fields["consignee"] == "शिखा गुप्ता, 12 मुंबई"
    # the read-back is folded into the reply exactly once
    assert "शिखा" in resp2.reply_text
    assert "सही?" in resp2.reply_text
    assert resp2.reply_text.count("सही?") == 1
    # and the still-pending field is still asked
    assert "वज़न" in resp2.reply_text
    assert resp2.pending_fields[0] == "weight_grams"
    assert resp2.reply_text != resp1.reply_text
