"""LLM chat schemas — request/response models for the conversation state API."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Payload for ``POST /api/llm/chat``.

    When ``conversation_id`` is omitted a new conversation is created.
    """

    conversation_id: str | None = Field(
        default=None,
        description="Existing conversation ID to continue; omit to start a new one",
    )
    message: str = Field(..., min_length=1, description="User message text")
    language: str = Field(
        ..., min_length=1, description="Preferred language code (e.g. 'en', 'hi')"
    )


class ChatResponse(BaseModel):
    """Returned after a chat interaction — full conversation state snapshot."""

    conversation_id: str
    user_id: str
    language: str
    current_step: str = Field(
        default="init",
        description="Current step in the multi-step order-creation flow",
    )
    filled_fields: dict[str, object] = Field(
        default_factory=dict,
        description="Fields the LLM has already extracted and confirmed",
    )
    pending_fields: list[str] = Field(
        default_factory=list,
        description="Fields the LLM still needs to ask about",
    )
    history: list[dict[str, str]] = Field(
        default_factory=list,
        description="The message history (role/content pairs)",
    )

    # Turn-loop extras (defaults keep the legacy state-only path valid).
    validation_report: dict[str, object] | None = Field(
        default=None,
        description="The deterministic ValidationTurnReport from validation-engine",
    )
    db_info: dict[str, object] | None = Field(
        default=None,
        description="Derived DB research (category, HS codes, duties, lane, landed cost)",
    )
    reply_text: str | None = Field(
        default=None,
        description="The assistant's reply for this turn (echo + next question)",
    )
    document_ready: bool = Field(
        default=False,
        description="True when validation passed and every required field is filled",
    )
    tts_hint: dict[str, object] = Field(
        default_factory=lambda: {"enabled": False, "language": ""},
        description="Hint for the frontend to play the reply via /api/voice/tts",
    )


class SessionResponse(ChatResponse):
    """Returned by GET /api/llm/session/{session_id} — same shape as ChatResponse."""
