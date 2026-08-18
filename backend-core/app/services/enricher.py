"""Gemini reply enrichment — the persona prompt + model call.

``GeminiEnricher`` rewrites a deterministic template reply into natural,
varied Hindi.  Persona: a warm Dak Ghar Niryat sahayak who acknowledges what is
known, then asks exactly ONE question — the next pending field.  Anti-
hallucination hard rule: no number, name, country, or figure that is not
string-identical to a value in the draft/db_info may appear in the reply.
Returns the template text unchanged when no ``GEMINI_API_KEY`` is configured
or the call fails (demo-safe).
"""

from __future__ import annotations

import os
from typing import Any

from app.services.llm_reply import FIELD_ORDER, _SENTINELS

# Draft field -> display label for the prompt's compact draft rendering.
_FIELD_LABELS: dict[str, dict[str, str]] = {
    "hi": {
        "product_category": "श्रेणी",
        "quantity": "मात्रा",
        "weight_grams": "वज़न",
        "destination_country": "देश",
        "value_minor": "मूल्य",
        "consignee": "प्राप्तकर्ता",
    },
    "en": {
        "product_category": "category",
        "quantity": "quantity",
        "weight_grams": "weight",
        "destination_country": "country",
        "value_minor": "value",
        "consignee": "recipient",
    },
}


def _render_draft(lang: str, draft: dict[str, Any]) -> str:
    """Non-sentinel draft values, rendered verbatim with per-field labels."""
    labels = _FIELD_LABELS.get(lang, _FIELD_LABELS["en"])
    parts: list[str] = []
    for field in FIELD_ORDER:
        value = draft.get(field)
        if value in _SENTINELS:
            continue
        parts.append(f"{labels.get(field, field)}: {value}")
    return ", ".join(parts) if parts else "(no values known yet)"


def _render_db_info(db_info: dict[str, Any]) -> str:
    """Compact research summary — only DB-researched values, never invented."""
    parts: list[str] = []
    category = db_info.get("category")
    if isinstance(category, dict):
        name = category.get("name") or category.get("slug")
        if name:
            parts.append(f"category_name: {name}")
    if db_info.get("category_name"):
        parts.append(f"category_name: {db_info['category_name']}")
    if db_info.get("product_description"):
        parts.append(f"product_description: {db_info['product_description']}")
    duties = db_info.get("duties") or []
    if duties:
        rate = duties[0].get("rate_pct") or duties[0].get("duty_pct")
        if rate is not None:
            parts.append(f"duty_rate_pct: {rate}")
        elif duties[0].get("hs6"):
            parts.append(f"hs6: {duties[0]['hs6']}")
    if db_info.get("landed_cost_minor") is not None:
        parts.append(f"landed_cost_minor: {db_info['landed_cost_minor']}")
    return "; ".join(parts) if parts else "(no research yet)"


class GeminiEnricher:
    """Reword a template reply into natural Hindi/English via Gemini."""

    MODEL = "gemini-3.5-flash-lite"

    def __init__(self, api_key: str | None = None) -> None:
        self._api_key = api_key or os.getenv("GEMINI_API_KEY")
        self._model: Any | None = None

    def _get_model(self) -> Any | None:
        if not self._api_key:
            return None
        if self._model is None:
            from google.generativeai.client import configure
            from google.generativeai.generative_models import GenerativeModel

            configure(api_key=self._api_key)
            self._model = GenerativeModel(self.MODEL)
        return self._model

    def enrich(
        self,
        lang: str,
        template_text: str,
        draft: dict[str, Any],
        db_info: dict[str, Any],
        next_field: str | None = None,
    ) -> str:
        """Return a polished version of *template_text*, or it unchanged."""
        try:
            model = self._get_model()
            if model is None:
                return template_text
            response = model.generate_content(
                self._persona_prompt(lang, template_text, draft, db_info, next_field)
            )
            polished = (getattr(response, "text", "") or "").strip()
            return polished if polished else template_text
        except Exception:
            return template_text

    def _persona_prompt(
        self,
        lang: str,
        template_text: str,
        draft: dict[str, Any],
        db_info: dict[str, Any],
        next_field: str | None,
    ) -> str:
        question_rule = (
            f"Ask exactly ONE question to collect the next pending field: {next_field}."
            if next_field
            else "Ask NO question — the shipment looks complete; just confirm readiness warmly."
        )
        return (
            "You are a warm, friendly Hindi Dak Ghar Niryat sahayak (export "
            "assistant) helping a small artisan export their handmade goods. "
            "Acknowledge briefly and warmly what the user has told you (from the "
            "draft values below). "
            f"{question_rule} "
            "Use natural, varied, conversational Hindi phrasing (never the same "
            "wording as the template verbatim). "
            "Reply with the message text only — no quotes, no preamble, no numbering. "
            "HARD RULE (anti-hallucination): never add any number, name, country, "
            "or figure that is not string-identical to a value in the draft or "
            "db_info below. You may only restate values that appear there.\n\n"
            f"Template reply to polish:\n{template_text}\n\n"
            f"Known draft values:\n{_render_draft(lang, draft)}\n\n"
            f"Research summary:\n{_render_db_info(db_info)}\n\n"
            f"Next pending field: {next_field or 'none'}"
        )


__all__ = ["GeminiEnricher"]
