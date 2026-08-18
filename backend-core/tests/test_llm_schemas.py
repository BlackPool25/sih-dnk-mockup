"""LLM chat schemas — the extended turn-loop response shape.

Pins: ChatResponse accepts the new turn-loop fields with their defaults, the
legacy state-only shape still validates (no new required fields), and the
tts_hint default is a dict with enabled=False.
"""

from __future__ import annotations

from app.schemas.llm import ChatRequest, ChatResponse, SessionResponse


def test_chat_request_requires_message_and_language() -> None:
    req = ChatRequest(message="नमस्ते", language="hi")
    assert req.conversation_id is None
    assert req.message == "नमस्ते"
    assert req.language == "hi"


def test_chat_response_defaults_for_legacy_path() -> None:
    resp = ChatResponse(
        conversation_id="abc",
        user_id="user-1",
        language="hi",
    )
    assert resp.current_step == "init"
    assert resp.filled_fields == {}
    assert resp.pending_fields == []
    assert resp.history == []
    assert resp.validation_report is None
    assert resp.db_info is None
    assert resp.reply_text is None
    assert resp.document_ready is False
    assert resp.tts_hint == {"enabled": False, "language": ""}


def test_chat_response_accepts_turn_loop_fields() -> None:
    resp = ChatResponse(
        conversation_id="abc",
        user_id="user-1",
        language="hi",
        current_step="consignee",
        filled_fields={"product_category": "jute-products"},
        pending_fields=["consignee"],
        history=[{"role": "user", "content": "नमस्ते"}],
        validation_report={"document_ready": False},
        db_info={"category_name": "Jute Products"},
        reply_text="मैंने समझा — 12 टुकड़े।",
        document_ready=True,
        tts_hint={"enabled": True, "language": "hi"},
    )
    assert resp.document_ready is True
    assert resp.reply_text.startswith("मैंने समझा")
    assert resp.tts_hint["language"] == "hi"


def test_session_response_inherits_extended_shape() -> None:
    resp = SessionResponse(conversation_id="abc", user_id="u", language="en")
    assert resp.validation_report is None
    assert isinstance(resp.tts_hint, dict)
