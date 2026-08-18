"""Chat turn-loop orchestration.

The turn contract (research FR-047 + the design directive):

    LLM proposes (extraction) → deterministic engine disposes (validation)
    → the engine's report feeds the LLM's human reply → told to the user.

Every turn:
1. hydrate the conversation state (Redis ``chat_session:{id}``);
2. call validation-engine ``/api/extract`` (RuleDraft first, Gemini fills gaps);
3. if the category is unknown → ask with ``search_categories`` candidates
   (disambiguation) and persist WITHOUT validating;
4. call ``/api/validate/shipment`` → the deterministic per-turn report
   (business_errors, missing_required, document_rules, db_info);
5. pick the next pending field, build the human Hindi/English reply
   (template + optional Gemini enrichment) echoing what is known;
6. persist the updated state (draft, report, db_info, history) and return.
"""

from __future__ import annotations

import json
import uuid
from typing import Any

from app.schemas.llm import ChatRequest, ChatResponse
from app.services.enricher import GeminiEnricher
from app.services.llm_reply import (
    FIELD_ORDER,
    TEMPLATES,
    ask_line,
    consignee_readback,
    echo_line,
    filler_reply,
    is_filler,
    offtopic_reply,
    options_line,
)
from app.services.val_client import ServiceUnavailable, ValClient
_REDIS_KEY_PREFIX = "chat_session"
_SENTINELS: frozenset[object] = frozenset({-1, "unknown", None})


def _sentinel(value: object) -> bool:
    return value in _SENTINELS


def _get_settings():
    from storage.config import settings as s

    return s


# ---------------------------------------------------------------------------
# State (de)serialisation — Redis hash, JSON-encoded fields, TTL 24h
# ---------------------------------------------------------------------------


def new_state(user_id: str, language: str) -> dict[str, Any]:
    return {
        "user_id": user_id,
        "language": language,
        "current_step": "init",
        "filled_fields": {},
        "pending_fields": list(FIELD_ORDER),
        "history": [],
        "validation_report": None,
        "db_info": None,
        "document_ready": False,
        "candidates": [],
    }


async def load_state(redis, conv_id: str) -> dict[str, Any] | None:
    """Hydrate a conversation state from Redis; None when absent/expired."""
    raw: dict[bytes, bytes] = await redis.hgetall(f"{_REDIS_KEY_PREFIX}:{conv_id}")
    if not raw:
        return None
    flat = {
        k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
        for k, v in raw.items()
    }
    state = new_state(flat.get("user_id", ""), flat.get("language", "hi"))

    def _load_json(key: str, fallback: object) -> object:
        val = flat.get(key)
        if not val:
            return fallback
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return fallback

    state["current_step"] = flat.get("current_step", "init")
    state["filled_fields"] = _load_json("filled_fields", {})
    state["pending_fields"] = _load_json("pending_fields", list(FIELD_ORDER))
    state["history"] = _load_json("history", [])
    state["validation_report"] = _load_json("validation_report", None)
    db_info = _load_json("db_info", None)
    state["db_info"] = db_info if isinstance(db_info, dict) else None
    state["document_ready"] = flat.get("document_ready") == "true"
    state["candidates"] = _load_json("candidates", [])
    return state


async def save_state(redis, conv_id: str, state: dict[str, Any]) -> None:
    """Persist a conversation state hash and (re)set its TTL."""
    key = f"{_REDIS_KEY_PREFIX}:{conv_id}"
    flat: dict[str, str] = {
        "user_id": str(state["user_id"]),
        "language": str(state["language"]),
        "current_step": str(state["current_step"]),
        "filled_fields": json.dumps(state["filled_fields"]),
        "pending_fields": json.dumps(state["pending_fields"]),
        "history": json.dumps(state["history"]),
        "validation_report": json.dumps(state["validation_report"]),
        "db_info": json.dumps(state["db_info"]),
        "document_ready": "true" if state["document_ready"] else "false",
        "candidates": json.dumps(state["candidates"]),
    }
    await redis.hset(key, mapping=flat)
    ttl_seconds = _get_settings().LLM_CONVERSATION_TTL_HOURS * 3600
    await redis.expire(key, ttl_seconds)


# ---------------------------------------------------------------------------
# Turn-loop helpers
# ---------------------------------------------------------------------------


def merge_draft(previous: dict[str, Any], extracted: dict[str, Any]) -> dict[str, Any]:
    """Merge extracted draft values over previous; sentinels never overwrite."""
    merged = dict(previous)
    for field in FIELD_ORDER:
        value = extracted.get(field)
        if not _sentinel(value):
            merged[field] = value
    return merged


def _filled_snapshot(filled_fields: dict[str, Any]) -> tuple[object, ...]:
    """The six FIELD_ORDER values — the turn-over-turn diff basis."""
    return tuple(filled_fields.get(f) for f in FIELD_ORDER)


def _newly_filled_fields(before: tuple[object, ...], after: dict[str, Any]) -> list[str]:
    """Field names whose value changed this turn and is now non-sentinel."""
    now = _filled_snapshot(after)
    return [f for f, old, new in zip(FIELD_ORDER, before, now) if old != new and not _sentinel(new)]


def pending_fields(draft: dict[str, Any]) -> list[str]:
    """The six draft fields still at sentinel, in the fixed ask order."""
    return [f for f in FIELD_ORDER if _sentinel(draft.get(f))]


def pick_next_field(draft: dict[str, Any], report: dict[str, Any] | None) -> str | None:
    """A business-error field wins, else the head of the pending list."""
    if report:
        for err in report.get("business_errors") or []:
            field = err.get("field")
            if field in FIELD_ORDER:
                return field
    pending = pending_fields(draft)
    return pending[0] if pending else None


def build_reply(
    lang: str,
    draft: dict[str, Any],
    db_info: dict[str, Any] | None,
    next_field: str | None,
    candidates: list[dict[str, Any]],
) -> str:
    """The template reply: disambiguation options, else echo + next question."""
    if candidates:
        return options_line(lang, candidates)
    if next_field is None:
        return f"{echo_line(lang, draft, db_info)} {TEMPLATES[lang]['ready']}".strip()
    echo = echo_line(lang, draft, db_info)
    question = ask_line(lang, next_field)
    if echo:
        return f"{echo} {question}"
    return question


def disambiguation_reply(lang: str, candidates: list[dict[str, Any]]) -> str:
    """The category-ask reply when extraction could not resolve a category.

    With candidates → numbered options; without → the plain category question
    (never the 'ready' message — the draft is incomplete until a category is
    chosen).
    """
    if candidates:
        return options_line(lang, candidates)
    return TEMPLATES[lang]["ask.category"]


def article_id_for(category_slug: str | None) -> str | None:
    """Deterministic demo article id from the category slug (e.g. JUT-001)."""
    if not category_slug:
        return None
    prefix = "".join(part[:3] for part in category_slug.split("-")[:2]).upper()
    return f"{prefix}-001"


def new_conversation_id() -> str:
    return uuid.uuid4().hex


def _resolve_category_pick(message: str, candidates: list[dict[str, Any]]) -> str | None:
    """A 1-based number maps to the matching candidate's slug; else None."""
    stripped = message.strip()
    if not stripped.isdigit():
        return None
    index = int(stripped) - 1
    if 0 <= index < len(candidates):
        slug = candidates[index].get("slug")
        return str(slug) if slug else None
    return None


def _expected_field(state: dict[str, Any]) -> str | None:
    """The head of the pending fields — the field this turn is answering."""
    pending = state.get("pending_fields") or []
    return str(pending[0]) if pending else None


async def run_turn(
    *,
    user_id: str,
    body: ChatRequest,
    conv_id: str,
    state: dict[str, Any],
    redis,
    iec: str | None = None,
    val_client: ValClient | None = None,
) -> ChatResponse:
    """Execute one chat turn; returns the extended ChatResponse."""
    if val_client is None:
        from app.services.val_client import val_client as _default_client

        val_client = _default_client
    client = val_client
    lang = body.language if body.language in ("hi", "en") else "hi"

    state["history"].append({"role": "user", "content": body.message})

    # 0. Category-pick resolution --------------------------------------------
    # When we asked for disambiguation and the user answers with a number,
    # resolve it against the offered candidates before re-running extraction.
    if state["candidates"]:
        picked = _resolve_category_pick(body.message, state["candidates"])
        if picked is not None:
            state["filled_fields"]["product_category"] = picked
            state["candidates"] = []

    # 1. Extraction ----------------------------------------------------------
    expected_field = _expected_field(state)
    try:
        result = await client.extract(
            body.message, lang, previous=state["filled_fields"] or None, expected=expected_field
        )
    except ServiceUnavailable as exc:
        return _error_response(conv_id, user_id, lang, state, f"सेवा उपलब्ध नहीं — {exc}")

    filled_before = _filled_snapshot(state["filled_fields"])
    state["filled_fields"] = merge_draft(state["filled_fields"], dict(result.draft))
    state["candidates"] = []
    newly_filled = _newly_filled_fields(filled_before, state["filled_fields"])

    # 2. Filler acknowledgment ------------------------------------------------
    # Nothing new was extracted AND the message is pure filler: acknowledge
    # warmly and re-ask the pending field with a rotated variant instead of
    # re-emitting the previous turn's robotic echo.  The rotation index is the
    # turn count — len(history) // 2, since every turn appends exactly one user
    # and one assistant message — so consecutive filler turns alternate variants
    # (the raw history length modulo an even variant count would repeat forever).
    if (
        not newly_filled
        and not result.category_unknown
        and not state["candidates"]
        and is_filler(body.message)
    ):
        reply = filler_reply(lang, expected_field, len(state["history"]) // 2)
        state["current_step"] = expected_field or (
            "done" if state["document_ready"] else "collecting"
        )
        state["history"].append({"role": "assistant", "content": reply})
        await save_state(redis, conv_id, state)
        return build_state_response(conv_id, user_id, lang, state, reply)

    # 3. Category disambiguation ---------------------------------------------
    if result.category_unknown:
        candidates: list[dict[str, object]] = []
        for slug in result.candidates:
            candidates.append({"slug": slug, "name": slug.replace("-", " ").title()})
        if not candidates:
            try:
                candidates = await client.search_categories(body.message)
            except ServiceUnavailable:
                candidates = []
        state["candidates"] = candidates
        state["current_step"] = "category_disambiguation"
        state["pending_fields"] = pending_fields(state["filled_fields"])
        reply = disambiguation_reply(lang, candidates)
        # When no candidates exist the plain ask is the robotic template the
        # user complained about — enrich it through Gemini for a warm, varied
        # question.  With candidates the numbered options are kept verbatim
        # (the chat parses the "1)"/"2)" picks; the enricher's no-new-numbers
        # rule could drop them).
        if not candidates:
            enricher = GeminiEnricher()
            reply = enricher.enrich(
                lang,
                reply,
                state["filled_fields"],
                state["db_info"] or {},
                next_field="product_category",
            )
        state["history"].append({"role": "assistant", "content": reply})
        await save_state(redis, conv_id, state)
        return build_state_response(conv_id, user_id, lang, state, reply)

    # 4. Deterministic validation ---------------------------------------------
    try:
        report = await client.validate_shipment(
            state["filled_fields"],
            form_type="PBE_IV",
            iec=iec,
        )
    except ServiceUnavailable as exc:
        return _error_response(conv_id, user_id, lang, state, f"सेवा उपलब्ध नहीं — {exc}")

    state["validation_report"] = report
    db_info = report.get("db_info")
    state["db_info"] = db_info if isinstance(db_info, dict) else None
    state["document_ready"] = bool(report.get("document_ready"))
    state["pending_fields"] = pending_fields(state["filled_fields"])

    # 5. Reply ----------------------------------------------------------------
    next_field = pick_next_field(state["filled_fields"], report)
    state["current_step"] = next_field or ("done" if state["document_ready"] else "collecting")

    rotation = len(state["history"]) // 2
    if newly_filled and expected_field not in newly_filled and next_field is not None:
        # Off-topic acceptance: the seller volunteered a field we were not
        # asking for — the merge already kept it (never lose data); acknowledge
        # it and re-ask the STILL-pending field with a different phrasing.
        volunteered = [f for f in newly_filled if f != "consignee"]
        reply = offtopic_reply(
            lang, volunteered, state["filled_fields"], state["db_info"], next_field, rotation
        )
        if "consignee" in newly_filled:
            readback = consignee_readback(lang, state["filled_fields"].get("consignee"))
            reply = f"{readback} {reply}"
    elif "consignee" in newly_filled and next_field is not None:
        # Consignee answered this turn while another field is still pending:
        # read the name back once, folded into the normal next ask.
        readback = consignee_readback(lang, state["filled_fields"].get("consignee"))
        reply = f"{readback} {build_reply(lang, state['filled_fields'], state['db_info'], next_field, [])}"
    else:
        reply = build_reply(lang, state["filled_fields"], state["db_info"], next_field, [])

    enricher = GeminiEnricher()
    reply = enricher.enrich(
        lang, reply, state["filled_fields"], state["db_info"] or {}, next_field
    )
    state["history"].append({"role": "assistant", "content": reply})

    await save_state(redis, conv_id, state)
    return build_state_response(conv_id, user_id, lang, state, reply)


def _error_response(
    conv_id: str, user_id: str, lang: str, state: dict[str, Any], message: str
) -> ChatResponse:
    state["history"].append({"role": "assistant", "content": message})
    return build_state_response(conv_id, user_id, lang, state, message)


def build_state_response(
    conv_id: str, user_id: str, lang: str, state: dict[str, Any], reply: str
) -> ChatResponse:
    return ChatResponse(
        conversation_id=conv_id,
        user_id=user_id,
        language=lang,
        current_step=state["current_step"],
        filled_fields=state["filled_fields"],
        pending_fields=state["pending_fields"],
        history=state["history"],
        validation_report=state["validation_report"],
        db_info=state["db_info"],
        reply_text=reply,
        document_ready=state["document_ready"],
        tts_hint={"enabled": lang == "hi", "language": lang},
    )


__all__ = [
    "article_id_for",
    "build_state_response",
    "build_reply",
    "load_state",
    "merge_draft",
    "new_conversation_id",
    "new_state",
    "pending_fields",
    "pick_next_field",
    "run_turn",
    "save_state",
]
