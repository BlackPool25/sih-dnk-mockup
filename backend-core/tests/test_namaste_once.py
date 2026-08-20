"""Namaste once."""
from __future__ import annotations
import asyncio
from unittest.mock import MagicMock
from app.schemas.llm import ChatRequest
from app.services.chat import load_state, new_conversation_id, new_state, run_turn
from app.services.enricher import GeminiEnricher
from tests.fake_val_client import FakeValClient
from tests.test_chat_service import FakeRedis
def _run(coro): return asyncio.run(coro)
def test_new_state_has_greeted_false() -> None: assert new_state("u1", "hi")["has_greeted"] is False
def test_second_turn_no_namaste() -> None:
    client = FakeValClient(); redis = FakeRedis(); conv_id = new_conversation_id(); state = new_state("u1", "hi")
    body1 = ChatRequest(message="12 जूट बैग 500 ग्राम जर्मनी ₹15000", language="hi")
    _run(run_turn(user_id="u1", body=body1, conv_id=conv_id, state=state, redis=redis, val_client=client))
    assert state["has_greeted"] is True
    loaded = _run(load_state(redis, conv_id))
    assert loaded is not None and loaded["has_greeted"] is True
    fake_model = MagicMock(); fake_model.generate_content.return_value = MagicMock(text="नमस्ते! 500 ग्राम समझ गया। किस देश?")
    enricher_spy = GeminiEnricher(api_key="test-key"); enricher_spy._model = fake_model  # type: ignore[attr-defined]
    enricher_spy.enrich("hi","मैंने समझा — 500 ग्राम। किस देश में भेजना है?",{"weight_grams": 500},{},next_field="destination_country",session_state={"has_greeted": True, "iec": None})
    prompt = fake_model.generate_content.call_args.args[0]
    assert "Do NOT greet" in prompt or "already greeted" in prompt.lower()
    body2 = ChatRequest(message="बस यही है", language="hi", conversation_id=conv_id)
    resp2 = _run(run_turn(user_id="u1", body=body2, conv_id=conv_id, state=state, redis=redis, val_client=client))
    assert "नमस्ते" not in resp2.reply_text
def test_enricher_first_turn_greets() -> None:
    fake_model = MagicMock(); fake_model.generate_content.return_value = MagicMock(text="नमस्ते! बताइए...")
    enricher = GeminiEnricher(api_key="test-key"); enricher._model = fake_model  # type: ignore[attr-defined]
    enricher.enrich("hi","मैंने समझा।",{},{},next_field="product_category",session_state={"has_greeted": False})
    prompt = fake_model.generate_content.call_args.args[0]
    assert "Greet warmly" in prompt or "नमस्ते" in prompt
