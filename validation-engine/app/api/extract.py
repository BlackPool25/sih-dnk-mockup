"""POST /api/extract — rule-first draft extraction with optional Gemini gap-fill.

The rule engine runs first (deterministic, free); when the result still has a
sentinel field AND a GEMINI_API_KEY is set, the Gemini draft extractor fills
the gaps.  The merge (Wave 1 T1) relaxes the old "gemini fills only" rule per
the user design decision "if the seller clarifies some information that changes
previously added details, it should be allowed":

1. a deterministic rule value from this turn always wins;
2. a SANE gemini value corrects a previously-stored field (the current turn
   restated/clarified it) or gap-fills an unstated one;
3. else the previous stored value; else the sentinel.

A gemini value outside the sanity bounds is never adopted.  A category that the
rules cannot map is a 200 with ``category_unknown: true`` — the chat must ask,
never a 4xx.  No DB values are ever returned.
"""

from __future__ import annotations

import os
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.schemas.shipment import (
    CONSIGNEE_UNSTATED,
    DESTINATION_UNSTATED,
    QUANTITY_UNSTATED,
    VALUE_UNSTATED,
    WEIGHT_UNSTATED,
    ShipmentDraft,
)
from app.services.extract import (
    CategoryUnknownError,
    GeminiDraftExtractor,
    RuleDraftExtractor,
    category_candidates,
    draft_confidence,
)
from app.services.sanity import sanity_ok

router = APIRouter(prefix="/api/extract", tags=["extract"])


def _llm_api_errors() -> tuple[type[Exception], ...]:
    """The google.api_core base exception for every LLM API failure (quota 429,
    403, 5xx). Lazily imported so the rule-only path never needs the SDK."""
    try:
        from google.api_core.exceptions import GoogleAPICallError
    except ImportError:  # pragma: no cover — google-api-core ships with genai
        return ()
    return (GoogleAPICallError,)


class ExtractRequest(BaseModel):
    """One turn of spoken text, optionally with the accumulated draft.

    ``expected`` is the pending field the chat is asking about (e.g.
    ``"consignee"``) — the rule engine uses it for the Case-B heuristic that
    treats a plain name+address answer as the consignee.
    """

    text: str
    lang: str = "hi"
    previous: ShipmentDraft | None = None
    expected: str | None = None


class ExtractResponse(BaseModel):
    """The accumulated draft after this turn + which extractor produced it.

    ``category_unknown`` + ``candidates`` together drive the chat's
    disambiguation question when the rule engine could not resolve a category:
    the candidate slugs come from the extractor's own keyword vocabulary, so
    they work for Hindi/Kannada utterances even though the DB stores English
    names.
    """

    draft: ShipmentDraft
    category_unknown: bool
    extractor: Literal["rule", "gemini"]
    candidates: list[str] = []


@router.post("", response_model=ExtractResponse)
def post_extract(payload: ExtractRequest) -> ExtractResponse:
    """Extract a draft from the turn; 200 even when the category is unknown.

    The rule engine runs first (deterministic); when it cannot map the
    category (``CategoryUnknownError``) AND a GEMINI_API_KEY is set, Gemini
    still runs with the partial draft and its ``search_categories`` tool so it
    can resolve the category from the seeded catalog — the hardcoded rule gate
    never blocks the model from seeing the utterance.  ``category_unknown``
    flips true only when the model ALSO cannot decide (or no key), so the chat
    asks the user with candidates.
    """
    try:
        draft = RuleDraftExtractor().extract_from_text(
            payload.text, payload.lang, payload.previous, expected=payload.expected
        )
        rule_unknown = False
    except CategoryUnknownError as exc:
        draft = exc.partial_draft or payload.previous or ShipmentDraft()
        rule_unknown = True
    extractor = "rule"
    if os.environ.get("GEMINI_API_KEY") and (rule_unknown or _has_sentinel(draft)):
        try:
            filled = GeminiDraftExtractor().extract(payload.text, draft, payload.lang)
            draft = _merge_filled(draft, filled, payload.previous)
            extractor = "gemini"
        except (ImportError, RuntimeError, ValueError, *_llm_api_errors()):
            # no package/key, reprompt exhaustion, or LLM API error (quota 429 /
            # 5xx) — keep the rule draft, never 500 the call.
            extractor = "rule"
    category_unknown = rule_unknown and draft.product_category is None
    return ExtractResponse(
        draft=draft,
        category_unknown=category_unknown,
        extractor=extractor,
        candidates=category_candidates(payload.text) if category_unknown else [],
    )


def _has_sentinel(draft: ShipmentDraft) -> bool:
    """True iff any of the six draft fields is still unstated."""
    return any(
        (
            draft.product_category is None,
            draft.quantity == QUANTITY_UNSTATED,
            draft.weight_grams == WEIGHT_UNSTATED,
            draft.destination_country == DESTINATION_UNSTATED,
            draft.consignee == CONSIGNEE_UNSTATED,
            draft.value_minor == VALUE_UNSTATED,
        )
    )


# (draft attribute, sentinel, sanity field name) for the six mergeable fields.
_FIELD_SPECS: tuple[tuple[str, object, str], ...] = (
    ("product_category", None, "product_category"),
    ("quantity", QUANTITY_UNSTATED, "quantity"),
    ("weight_grams", WEIGHT_UNSTATED, "weight_grams"),
    ("destination_country", DESTINATION_UNSTATED, "destination_country"),
    ("consignee", CONSIGNEE_UNSTATED, "consignee"),
    ("value_minor", VALUE_UNSTATED, "value_minor"),
)


def _merge_filled(
    rule_draft: ShipmentDraft, gemini_draft: ShipmentDraft, previous: ShipmentDraft | None
) -> ShipmentDraft:
    """Merge the gemini gap-fill/correction draft over the rule draft.

    Per-field precedence (see the module docstring): rule value this turn >
    sane gemini value (correction of a stored field OR gap-fill) > previous
    stored value > sentinel.
    """
    category = rule_draft.product_category or gemini_draft.product_category
    prev = previous
    merged = ShipmentDraft.model_validate(
        {
            attr: _merge_field(
                getattr(rule_draft, attr),
                getattr(gemini_draft, attr),
                getattr(prev, attr) if prev else sentinel,
                sentinel,
                field,
                category,
            )
            for attr, sentinel, field in _FIELD_SPECS
        }
    )
    return merged.model_copy(update={"confidence": draft_confidence(merged)})


def _merge_field(rule_value, gemini_value, previous_value, sentinel, field, category):
    """One field's merge precedence — see ``_merge_filled``.

    Six independent inputs (four candidate values + the sanity discriminator
    + the field name) are genuinely required for the four-tier decision; the
    field specs tuple above is the single call site.
    """
    if rule_value != sentinel:
        return rule_value
    if gemini_value != sentinel and sanity_ok(gemini_value, field, category):
        return gemini_value
    if previous_value != sentinel:
        return previous_value
    return sentinel


__all__ = ["ExtractRequest", "ExtractResponse", "router"]
