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
import time
import unicodedata
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
from app.services.translation import (
    ensure_english_free_text,
    is_latin_free_text,
    translate_consignee_hi_en,
)
from app.services.val_client import ServiceUnavailable, ValClient

_REDIS_KEY_PREFIX = "chat_session"
_SENTINELS: frozenset[object] = frozenset({-1, "unknown", None})

_SEARCH_CACHE: dict[str, tuple[float, list[dict[str, Any]]]] = {}
_SEARCH_TTL_SECONDS = 300.0


def _normalize_search_query(query: str) -> str:
    return unicodedata.normalize("NFKC", query).lower().strip()


def _search_cache_get(query: str) -> list[dict[str, Any]] | None:
    key = _normalize_search_query(query)
    entry = _SEARCH_CACHE.get(key)
    if entry is None:
        return None
    ts, value = entry
    if time.monotonic() - ts > _SEARCH_TTL_SECONDS:
        _SEARCH_CACHE.pop(key, None)
        return None
    return value


def _search_cache_set(query: str, value: list[dict[str, Any]]) -> None:
    key = _normalize_search_query(query)
    _SEARCH_CACHE[key] = (time.monotonic(), value)


def _sentinel(value: object) -> bool:
    return value in _SENTINELS


def _get_settings():
    from storage.config import settings as s

    return s


# ---------------------------------------------------------------------------
# State (de)serialisation — Redis hash, JSON-encoded fields, TTL 24h
# ---------------------------------------------------------------------------


def _call_enricher(enricher, lang, template_text, draft, db_info, next_field, session_state):
    try:
        return enricher.enrich(lang, template_text, draft, db_info, next_field, session_state=session_state)
    except TypeError:
        return enricher.enrich(lang, template_text, draft, db_info, next_field)


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
        "iec": None,
        "gstin": None,
        "state_code": None,
        "state_iso2": None,
        "has_greeted": False,
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
    state["iec"] = flat.get("iec") or None
    state["gstin"] = flat.get("gstin") or None
    state["state_code"] = flat.get("state_code") or None
    state["state_iso2"] = flat.get("state_iso2") or None
    state["has_greeted"] = flat.get("has_greeted") == "true"
    return state


async def save_state(redis, conv_id: str, state: dict[str, Any]) -> None:
    """Persist a conversation state hash and (re)set its TTL."""
    key = f"{_REDIS_KEY_PREFIX}:{conv_id}"
    flat: dict[str, str] = {
        "user_id": str(state["user_id"]),
        "language": str(state["language"]),
        "current_step": str(state["current_step"]),
        "filled_fields": json.dumps(state["filled_fields"], ensure_ascii=False),
        "pending_fields": json.dumps(state["pending_fields"]),
        "history": json.dumps(state["history"], ensure_ascii=False),
        "validation_report": json.dumps(state["validation_report"], ensure_ascii=False),
        "db_info": json.dumps(state["db_info"], ensure_ascii=False),
        "document_ready": "true" if state["document_ready"] else "false",
        "candidates": json.dumps(state["candidates"], ensure_ascii=False),
        "iec": str(state["iec"]) if state.get("iec") else "",
        "gstin": str(state["gstin"]) if state.get("gstin") else "",
        "state_code": str(state.get("state_code") or state.get("state_iso2") or ""),
        "state_iso2": str(state.get("state_iso2") or state.get("state_code") or ""),
        "has_greeted": "true" if state.get("has_greeted") else "false",
    }
    await redis.hset(key, mapping=flat)
    ttl_seconds = _get_settings().LLM_CONVERSATION_TTL_HOURS * 3600
    await redis.expire(key, ttl_seconds)


def _clean_field_prefix(text: str, prefixes: list[str]) -> str:
    cleaned = text.strip()
    lower = cleaned.lower()
    for p in sorted(prefixes, key=len, reverse=True):
        if lower.startswith(p.lower()):
            cleaned = cleaned[len(p):].strip(" :,।-\n\r\t")
            lower = cleaned.lower()
    return cleaned


def _process_buyer_name_and_address(
    message: str,
    extracted_consignee: object,
    expected_field: str | None,
    filled_fields: dict[str, Any],
) -> None:
    """Handle separate buyer name and delivery address extraction."""
    name_prefixes = [
        "buyer name is", "buyer is", "my buyer is", "buyer name:", "buyer:",
        "recipient name is", "recipient is", "recipient name:", "recipient:", "recipient",
        "consignee is", "consignee name is", "consignee:", "send to",
        "name is", "name:", "buyer",
        "खरीदार का नाम", "खरीदार है", "खरीदार:", "खरीदार",
        "प्राप्तकर्ता का नाम", "प्राप्तकर्ता है", "प्राप्तकर्ता:", "प्राप्तकर्ता",
        "नाम है", "नाम:", "को भेजना है", "को भेजना",
    ]
    addr_prefixes = [
        "address is", "delivery address is", "delivery address:", "address:",
        "location is", "delivery address", "street is", "street:",
        "पता है", "पता:", "डिलीवरी पता है", "डिलीवरी पता:", "डिलीवरी पता", "स्थान है",
    ]

    has_buyer_name = not _sentinel(filled_fields.get("buyer_name"))

    # Case 1: Answering address when expected_field is buyer_address
    if expected_field == "buyer_address":
        cleaned_addr = _clean_field_prefix(message, addr_prefixes)
        if cleaned_addr:
            filled_fields["buyer_address"] = cleaned_addr
            b_name = filled_fields.get("buyer_name", "")
            filled_fields["consignee"] = f"{b_name}, {cleaned_addr}" if b_name else cleaned_addr
        return

    # Case 2: User explicitly provided address via address prefix
    has_addr_prefix = any(message.lower().strip().startswith(p) for p in addr_prefixes)
    if has_addr_prefix and has_buyer_name:
        cleaned_addr = _clean_field_prefix(message, addr_prefixes)
        if cleaned_addr:
            filled_fields["buyer_address"] = cleaned_addr
            b_name = filled_fields.get("buyer_name", "")
            filled_fields["consignee"] = f"{b_name}, {cleaned_addr}" if b_name else cleaned_addr
        return

    # Case 3: Answering buyer name
    has_name_prefix = any(message.lower().strip().startswith(p) for p in name_prefixes)
    is_extracted = not _sentinel(extracted_consignee) and isinstance(extracted_consignee, str)

    if expected_field in ("buyer_name", "consignee") or has_name_prefix or is_extracted:
        candidate = extracted_consignee if is_extracted else message

        # Check if the user provided BOTH name and address in one message
        has_comma = "," in candidate
        has_addr_marker = any(
            kw in candidate.lower()
            for kw in (
                "street", "road", "strasse", "str.", "rd.", "ave", "lane", "box", "nagar",
                "block", "apt", "flat", "house", "बर्लिन", "मार्ग", "रोड", "गली", "मकान"
            )
        )
        has_digits = any(c.isdigit() for c in candidate)

        if (has_comma and has_addr_marker) or (has_digits and has_addr_marker):
            if has_comma:
                parts = [p.strip() for p in candidate.split(",", 1) if p.strip()]
                filled_fields["buyer_name"] = _clean_field_prefix(parts[0], name_prefixes)
                filled_fields["buyer_address"] = parts[1]
                filled_fields["consignee"] = f"{filled_fields['buyer_name']}, {filled_fields['buyer_address']}"
            else:
                filled_fields["consignee"] = candidate
                filled_fields["buyer_name"] = candidate
                filled_fields["buyer_address"] = candidate
        else:
            cleaned_name = _clean_field_prefix(candidate, name_prefixes)
            if cleaned_name:
                filled_fields["buyer_name"] = cleaned_name
                filled_fields["consignee"] = "unknown"


def merge_draft(previous: dict[str, Any], extracted: dict[str, Any]) -> dict[str, Any]:
    """Merge extracted draft values over previous; sentinels never overwrite."""
    merged = dict(previous)
    for field in FIELD_ORDER:
        value = extracted.get(field)
        if not _sentinel(value):
            merged[field] = value
    return merged


def _filled_snapshot(filled_fields: dict[str, Any]) -> tuple[object, ...]:
    """The FIELD_ORDER values plus buyer_name and buyer_address."""
    return tuple(filled_fields.get(f) for f in (*FIELD_ORDER, "buyer_name", "buyer_address"))


def _newly_filled_fields(before: tuple[object, ...], after: dict[str, Any]) -> list[str]:
    """Field names whose value changed this turn and is now non-sentinel."""
    now = _filled_snapshot(after)
    all_fields = (*FIELD_ORDER, "buyer_name", "buyer_address")
    return [f for f, old, new in zip(all_fields, before, now) if old != new and not _sentinel(new)]


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
    if not pending:
        return None
    field = pending[0]
    if field == "consignee":
        if _sentinel(draft.get("buyer_name")):
            return "buyer_name"
        if _sentinel(draft.get("buyer_address")):
            return "buyer_address"
        return "consignee"
    return field


def build_reply(
    lang: str,
    draft: dict[str, Any],
    db_info: dict[str, Any] | None,
    next_field: str | None,
    candidates: list[dict[str, Any]],
    changed_fields: list[str] | None = None,
    has_greeted: bool = True,
) -> str:
    if candidates:
        return options_line(lang, candidates)
    if next_field is None:
        echo = echo_line(lang, draft, db_info, only_fields=changed_fields)
        return f"{echo} {TEMPLATES[lang]['ready']}".strip()
    echo = echo_line(lang, draft, db_info, only_fields=changed_fields)
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
    """The field this turn is answering."""
    step = state.get("current_step")
    if step and step not in ("init", "collecting", "done", "category_disambiguation"):
        return str(step)
    pending = state.get("pending_fields") or []
    if pending:
        field = pending[0]
        if field == "consignee":
            if _sentinel(state.get("filled_fields", {}).get("buyer_name")):
                return "buyer_name"
            if _sentinel(state.get("filled_fields", {}).get("buyer_address")):
                return "buyer_address"
            return "consignee"
        return str(field)
    return None


async def _maybe_translate_consignee(
    state: dict[str, Any], redis
) -> dict[str, str] | None:
    raw = state["filled_fields"].get("consignee")
    if not isinstance(raw, str) or not raw.strip():
        return None
    if is_latin_free_text(raw):
        return None
    existing_en = state["filled_fields"].get("consignee_en")
    existing_hi = state["filled_fields"].get("consignee_hi")
    if existing_hi == raw and isinstance(existing_en, str) and existing_en:
        return {"hi": str(existing_hi), "en": str(existing_en)}
    try:
        hi_en = await translate_consignee_hi_en(raw, redis=redis)
        state["filled_fields"]["consignee_hi"] = hi_en["hi"]
        state["filled_fields"]["consignee_en"] = hi_en["en"]
        return hi_en
    except Exception:
        return None


async def _cached_search_categories(client: ValClient, query: str) -> list[dict[str, Any]]:
    cached = _search_cache_get(query)
    if cached is not None:
        return cached
    result = await client.search_categories(query)
    typed: list[dict[str, Any]] = [dict(r) for r in result]
    _search_cache_set(query, typed)
    return typed


async def run_turn(
    *,
    user_id: str,
    body: ChatRequest,
    conv_id: str,
    state: dict[str, Any],
    redis,
    iec: str | None = None,
    gstin: str | None = None,
    state_code: str | None = None,
    state_iso2: str | None = None,
    val_client: ValClient | None = None,
    changed_fields: list[str] | None = None,
) -> ChatResponse:
    """Execute one chat turn; returns the extended ChatResponse."""
    if val_client is None:
        from app.services.val_client import val_client as _default_client

        val_client = _default_client
    client = val_client
    lang = body.language if body.language in ("hi", "en") else "hi"
    if iec is not None and iec.strip():
        state["iec"] = iec.strip()
    if gstin is not None and gstin.strip():
        state["gstin"] = gstin.strip()
    _sc = state_code or state_iso2
    if _sc is not None and str(_sc).strip():
        state["state_code"] = str(_sc).strip()
        state["state_iso2"] = str(_sc).strip()
    if state.get("state_code") and not state.get("state_iso2"):
        state["state_iso2"] = state["state_code"]
    if state.get("state_iso2") and not state.get("state_code"):
        state["state_code"] = state["state_iso2"]
    is_first_turn = not bool(state.get("has_greeted"))
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
    _process_buyer_name_and_address(
        body.message,
        result.draft.get("consignee"),
        expected_field,
        state["filled_fields"],
    )
    state["candidates"] = []
    newly_filled = _newly_filled_fields(filled_before, state["filled_fields"])

    previous_db_info = state.get("db_info") if isinstance(state.get("db_info"), dict) else None
    await _maybe_translate_consignee(state, redis)

    effective_changed: list[str] | None = changed_fields
    if effective_changed is None:
        effective_changed = newly_filled if newly_filled else ([expected_field] if expected_field else None)

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
                candidates = await _cached_search_categories(client, body.message)
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
    validation_draft: dict[str, Any] = dict(state["filled_fields"])
    consignee_en = state["filled_fields"].get("consignee_en")
    if isinstance(consignee_en, str) and consignee_en.strip():
        validation_draft["consignee"] = consignee_en
    elif isinstance(validation_draft.get("consignee"), str) and not is_latin_free_text(str(validation_draft.get("consignee"))):
        try:
            eng = await ensure_english_free_text(
                [("consignee", str(validation_draft["consignee"]))], redis=redis
            )
            validation_draft["consignee"] = eng.get("consignee", validation_draft["consignee"])
        except Exception:
            pass

    _iec = state.get("iec") or iec
    _gstin = state.get("gstin") or gstin
    _state_iso2 = state.get("state_iso2") or state.get("state_code") or state_iso2 or state_code
    try:
        report = await client.validate_shipment(
            validation_draft,
            form_type="PBE_IV",
            iec=_iec,
            gstin=_gstin,
            state_iso2=_state_iso2,
            previous_db_info=previous_db_info,
            changed_fields=effective_changed,
        )
    except ServiceUnavailable as exc:
        return _error_response(conv_id, user_id, lang, state, f"सेवा उपलब्ध नहीं — {exc}")

    if effective_changed is not None and effective_changed:
        allowed = set(effective_changed)
        if expected_field:
            allowed.add(expected_field)
        raw_errors = report.get("business_errors")
        if isinstance(raw_errors, list):
            filtered = [
                e for e in raw_errors if isinstance(e, dict) and e.get("field") in allowed
            ]
            report = {**report, "business_errors": filtered}

    state["validation_report"] = report
    db_info = report.get("db_info")
    if isinstance(db_info, dict) and db_info:
        state["db_info"] = db_info
    elif previous_db_info is not None and not db_info:
        state["db_info"] = previous_db_info
        report["db_info"] = previous_db_info
    else:
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
        volunteered = [f for f in newly_filled if f not in ("consignee", "buyer_name", "buyer_address")]
        reply = offtopic_reply(
            lang, volunteered, state["filled_fields"], state["db_info"], next_field, rotation
        )
        if "consignee" in newly_filled or "buyer_name" in newly_filled:
            val = state["filled_fields"].get("buyer_name") or state["filled_fields"].get("consignee")
            readback = consignee_readback(lang, val)
            reply = f"{readback} {reply}"
    elif ("consignee" in newly_filled or "buyer_name" in newly_filled) and next_field is not None:
        # Consignee / buyer name answered this turn while another field is still pending:
        # read the name back once, folded into the normal next ask.
        val = state["filled_fields"].get("buyer_name") or state["filled_fields"].get("consignee")
        readback = consignee_readback(lang, val)
        reply = f"{readback} {build_reply(lang, state['filled_fields'], state['db_info'], next_field, [], changed_fields=newly_filled, has_greeted=bool(state.get('has_greeted')))}"
    else:
        reply = build_reply(lang, state["filled_fields"], state["db_info"], next_field, [], changed_fields=newly_filled, has_greeted=bool(state.get('has_greeted')))

    enricher = GeminiEnricher()
    reply = _call_enricher(enricher, lang, reply, state["filled_fields"], state["db_info"] or {}, next_field, state)
    if not is_first_turn:
        if lang == "en":
            for g in ("Hello!", "Hello,", "Hello", "Hi!", "Hi,", "Hi", "Welcome!", "Welcome"):
                if reply.startswith(g):
                    reply = reply[len(g):].strip()
                    reply = reply.lstrip(" ,.!-").strip()
        else:
            if "नमस्ते" in reply:
                reply = reply.replace("नमस्ते!", "").replace("नमस्ते", "").strip()
                reply = reply.lstrip(" ,।!").strip()
    state["has_greeted"] = True
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
        tts_hint={"enabled": True, "language": lang},
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
