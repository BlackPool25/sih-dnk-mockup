"""LLM Enricher carry."""
from __future__ import annotations
import asyncio
from unittest.mock import MagicMock
from app.schemas.llm import ChatRequest
from app.services.chat import load_state, new_conversation_id, new_state, run_turn
from app.services.enricher import GeminiEnricher
from tests.test_chat_service import FakeRedis
from tests.fake_val_client import FakeValClient
def _run(coro): return asyncio.run(coro)
def test_model_pinned_gemini_35_flash_lite() -> None: assert GeminiEnricher.MODEL == "gemini-3.5-flash-lite"
def test_field_hint_hook_exists_noop() -> None:
    from app.services.enricher import _field_hint
    assert _field_hint("hi", "quantity") == ""
    assert _field_hint("en", None) == ""
def test_turn2_state_still_contains_iec() -> None:
    client = FakeValClient(); redis = FakeRedis(); conv_id = new_conversation_id(); state = new_state("u1", "hi")
    body1 = ChatRequest(message="12 जूट बैग 500 ग्राम", language="hi")
    _run(run_turn(user_id="u1", body=body1, conv_id=conv_id, state=state, redis=redis, iec="ABC1234567", val_client=client))
    assert state["iec"] == "ABC1234567"
    body2 = ChatRequest(message="जर्मनी ₹15000", language="hi", conversation_id=conv_id)
    _run(run_turn(user_id="u1", body=body2, conv_id=conv_id, state=state, redis=redis, val_client=client))
    assert state["iec"] == "ABC1234567"
    loaded = _run(load_state(redis, conv_id))
    assert loaded is not None and loaded["iec"] == "ABC1234567"
def test_gstin_and_state_code_carry() -> None:
    client = FakeValClient(); redis = FakeRedis(); conv_id = new_conversation_id(); state = new_state("u1", "hi")
    body1 = ChatRequest(message="12 जूट बैग", language="hi")
    _run(run_turn(user_id="u1", body=body1, conv_id=conv_id, state=state, redis=redis, iec="IEC001", gstin="29ABCDE1234F1Z5", state_code="KA", val_client=client))
    assert state["gstin"] == "29ABCDE1234F1Z5" and state["state_code"] == "KA"
    body2 = ChatRequest(message="500 ग्राम जर्मनी", language="hi", conversation_id=conv_id)
    _run(run_turn(user_id="u1", body=body2, conv_id=conv_id, state=state, redis=redis, val_client=client))
    assert state["gstin"] == "29ABCDE1234F1Z5" and state["state_code"] == "KA"
def test_enricher_prompt_injects_session_identifiers() -> None:
    fake_model = MagicMock(); fake_model.generate_content.return_value = MagicMock(text="नमस्ते — polished")
    enricher = GeminiEnricher(api_key="test-key"); enricher._model = fake_model  # type: ignore[attr-defined]
    out = enricher.enrich("hi","मैंने समझा — 12 टुकड़े।",{"quantity": 12},{},next_field="destination_country",session_state={"iec": "IEC999", "gstin": "GSTIN999", "state_code": "MH", "has_greeted": False})
    assert out == "नमस्ते — polished"
    prompt: str = fake_model.generate_content.call_args.args[0]
    assert "IEC999" in prompt and "GSTIN999" in prompt and "MH" in prompt
