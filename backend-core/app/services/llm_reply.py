"""Hindi/English assistant replies — template-built, optionally Gemini-polished.

The reply contract (research FR-047): vernacular-first, human-sounding, and
echoing exactly what the deterministic pipeline knows.  Values in a reply come
ONLY from the validated draft + DB research (``db_info``), never from the LLM's
memory.  ``GeminiEnricher`` (in ``app.services.enricher``) may reword a
template into more natural Hindi, but is hard-forbidden from adding figures or
facts.
"""

from __future__ import annotations

import unicodedata
from typing import Any

# Country ISO2 -> display name (romanized; the en source for the echo line).
_COUNTRY_NAMES: dict[str, str] = {
    "US": "अमेरिका",
    "GB": "इंग्लैंड",
    "AE": "यूएई",
    "AU": "ऑस्ट्रेलिया",
    "DE": "जर्मनी",
    "FR": "फ़्रांस",
    "JP": "जापान",
    "CA": "कनाडा",
}

TEMPLATES: dict[str, dict[str, str]] = {
    "hi": {
        "welcome": (
            "नमस्ते! मैं डाक घर निर्यात सहायक हूँ। बताइए, आप क्या भेजना चाहते हैं — "
            'जैसे "जूट के उत्पाद अमेरिका"।'
        ),
        "ask.destination": "किस देश में भेजना है? (अमेरिका, इंग्लैंड, यूएई…)",
        "ask.quantity": "कितने टुकड़े भेजने हैं?",
        "ask.weight": "कुल वज़न कितना है? (जैसे 400 ग्राम या 2 किलो)",
        "ask.value": "माल की घोषित कीमत क्या है? (जैसे ₹500)",
        "ask.buyer_name": "प्राप्तकर्ता (खरीदार) का नाम बताइए।",
        "ask.buyer_address": "प्राप्तकर्ता का डिलीवरी पता बताइए।",
        "ask.consignee": "प्राप्तकर्ता (खरीदार) का नाम बताइए।",
        "ask.category": "किस उत्पाद श्रेणी में भेज रहे हैं? (जैसे जूट उत्पाद, लकड़ी के सामान)",
        "disambiguate.category": "मुझे श्रेणी नहीं समझ आई। कृपया चुनें — {options}",
        "echo": "मैंने समझा — {echo_parts}।",
        "ready": "सब कुछ तैयार है! क्या मैं अब ऑर्डर बना दूँ?",
        "ack.stored": "मैंने नोट कर लिया — {stored}।",
        "error.generic": "माफ़ कीजिए, मैं समझ नहीं पाया। कृपया दोबारा बताइए।",
        "error.lane": "{message} कृपया वज़न कम करके बताइए।",
    },
    "en": {
        "welcome": "Hello! I'm the Dak Ghar Niryat assistant. Tell me what you'd like to export — e.g. \"jute products to America\".",
        "ask.destination": "Which country is this going to? (America, UK, UAE…)",
        "ask.quantity": "How many pieces are you shipping?",
        "ask.weight": "What is the total weight? (e.g. 400 grams or 2 kilos)",
        "ask.value": "What is the declared value? (e.g. ₹500)",
        "ask.buyer_name": "Please tell me the buyer's (recipient's) name.",
        "ask.buyer_address": "Please tell me the buyer's delivery address.",
        "ask.consignee": "Please tell me the buyer's (recipient's) name.",
        "ask.category": "Which product category is this? (e.g. jute products, wooden items)",
        "disambiguate.category": "I couldn't pin down the category. Please choose — {options}",
        "echo": "Got it — {echo_parts}.",
        "ready": "Everything is ready! Shall I create the order now?",
        "ack.stored": "Noted — {stored}.",
        "error.generic": "Sorry, I couldn't understand. Please try again.",
        "error.lane": "{message} Please give a lower weight.",
    },
}

ECHO_PARTS: dict[str, str] = {
    "product_category": "श्रेणी {name}",
    "quantity": "{value} टुकड़े",
    "weight_grams": "{value} ग्राम",
    "destination_country": "{value}",
    "value_minor": "{value} रुपये",
    "buyer_name": "खरीदार {value}",
    "buyer_address": "पता {value}",
    "consignee": "{value} को भेजना",
}

ECHO_PARTS_EN: dict[str, str] = {
    "product_category": "category {name}",
    "quantity": "{value} pieces",
    "weight_grams": "{value} grams",
    "destination_country": "{value}",
    "value_minor": "₹{value}",
    "buyer_name": "buyer {value}",
    "buyer_address": "address {value}",
    "consignee": "send to {value}",
}

# Draft field -> human ordering for pending_fields (category always first).
FIELD_ORDER: tuple[str, ...] = (
    "product_category",
    "destination_country",
    "quantity",
    "weight_grams",
    "value_minor",
    "consignee",
)

_SENTINELS: frozenset[object] = frozenset({-1, "unknown", None})


def _display_value(
    lang: str, field: str, value: object, db_info: dict[str, Any] | None
) -> str | None:
    """Format one draft value for the echo line; None when it is a sentinel."""
    if value in _SENTINELS:
        return None
    if field == "product_category":
        name = (db_info or {}).get("category_name")
        return str(name or value)
    if field == "destination_country" and lang == "hi":
        return _COUNTRY_NAMES.get(str(value), str(value))
    return str(value)


def echo_line(lang: str, draft: dict[str, Any], db_info: dict[str, Any] | None = None, only_fields: list[str] | None = None) -> str:
    fields = only_fields if only_fields is not None else list(FIELD_ORDER)
    parts: list[str] = []
    for field in fields:
        raw = draft.get(field)
        display = _display_value(lang, field, raw, db_info)
        if display is None:
            continue
        template = ECHO_PARTS if lang == "hi" else ECHO_PARTS_EN
        if field in template:
            parts.append(template[field].format(name=display, value=display))
    if not parts:
        return ""
    return (TEMPLATES[lang]["echo"]).format(echo_parts=", ".join(parts))


def options_line(lang: str, candidates: list[dict[str, Any]]) -> str:
    """Numbered category options from search_categories rows."""
    numbered = "  ".join(
        f"{i + 1}) {c.get('name_hi') or c.get('name') or c.get('slug')}" for i, c in enumerate(candidates[:5])
    )
    return TEMPLATES[lang]["disambiguate.category"].format(options=numbered)


# Draft field -> the template key used to ask for it.
_ASK_KEY: dict[str, str] = {
    "product_category": "ask.category",
    "destination_country": "ask.destination",
    "quantity": "ask.quantity",
    "weight_grams": "ask.weight",
    "value_minor": "ask.value",
    "buyer_name": "ask.buyer_name",
    "buyer_address": "ask.buyer_address",
    "consignee": "ask.consignee",
}


def ask_line(lang: str, next_field: str) -> str:
    """The 'ask' template for the next pending field."""
    key = _ASK_KEY.get(next_field, "error.generic")
    return TEMPLATES[lang].get(key, TEMPLATES[lang]["error.generic"])


# ---------------------------------------------------------------------------
# Filler-turn detection — polite acknowledgment turns with no extractable data
# ---------------------------------------------------------------------------

FILLER_PHRASES: frozenset[str] = frozenset({
    "अरे भाई",
    "अच्छी बात",
    "ठीक है",
    "हाँ हाँ",
    "अच्छा",
    "समझ गया",
    "जी",
    "बिल्कुल",
    "हाँ",
    "धन्यवाद",
    "शुक्रिया",
    "ok",
    "theek",
    "sahi",
})

# Word-level filler tokens (every word inside a filler phrase plus polite
# sentence-final particles) — lets multi-word discourse turns such as
# "अरे भाई अच्छी बात हुई" decompose into filler units.
_FILLER_TOKENS: frozenset[str] = frozenset({
    "अरे",
    "भाई",
    "अच्छी",
    "बात",
    "ठीक",
    "है",
    "हाँ",
    "अच्छा",
    "समझ",
    "गया",
    "जी",
    "बिल्कुल",
    "धन्यवाद",
    "शुक्रिया",
    "ok",
    "theek",
    "sahi",
    "हुई",
    "हुआ",
})

_FILLER_PHRASES_SORTED: tuple[str, ...] = tuple(sorted(FILLER_PHRASES, key=len, reverse=True))


def _normalize_filler(text: str) -> str:
    """Lowercase; drop punctuation/symbols; keep letters, digits, marks, spaces.

    ``str.isalnum()`` is not used because it rejects Devanagari vowel signs and
    other combining marks (category Mn/Mc) that are part of the letters.
    """
    return "".join(
        ch for ch in text if ch.isspace() or unicodedata.category(ch)[0] in ("L", "N", "M")
    ).strip().lower()


def is_filler(text: str) -> bool:
    """True when *text* carries only polite filler — nothing extractable.

    A normalized utterance is filler when it is itself a known phrase, or when
    it decomposes (longest-phrase-first) into at most three filler units:
    "अरे भाई अच्छी बात हुई" is filler, while "हाँ अमेरिका" (a real country) is
    not — real data with a polite prefix must still be extracted.
    """
    norm = _normalize_filler(text)
    if not norm:
        return False
    if norm in FILLER_PHRASES:
        return True
    units = 0
    i = 0
    n = len(norm)
    while i < n:
        if norm[i].isspace():
            i += 1
            continue
        for phrase in _FILLER_PHRASES_SORTED:
            if norm.startswith(phrase, i):
                units += 1
                i += len(phrase)
                break
        else:
            end = i
            while end < n and not norm[end].isspace():
                end += 1
            if norm[i:end] not in _FILLER_TOKENS:
                return False
            units += 1
            i = end
        if units > 3:
            return False
    return units >= 1


# ---------------------------------------------------------------------------
# Varied re-asks — filler / off-topic / read-back turns must not repeat the
# previous question verbatim, so each field has 2-3 phrasings to rotate through.
# ---------------------------------------------------------------------------

ASK_VARIANTS: dict[str, tuple[str, ...]] = {
    "destination_country": (
        "किस देश में भेजना है? (अमेरिका, इंग्लैंड, यूएई…)",
        "माल किस देश जाएगा?",
    ),
    "quantity": (
        "कितने टुकड़े भेजने हैं?",
        "टुकड़ों की संख्या कितनी है?",
    ),
    "weight_grams": (
        "कुल वज़न कितना है? (जैसे 400 ग्राम या 2 किलो)",
        "वज़न कितना रखें?",
    ),
    "value_minor": (
        "माल की घोषित कीमत क्या है? (जैसे ₹500)",
        "कीमत कितनी बताएँ?",
    ),
    "consignee": (
        "प्राप्तकर्ता का नाम और पता बताइए।",
        "पार्सल किसको भेजना है? नाम और पता दीजिए।",
    ),
}

_ASK_VARIANTS_EN: dict[str, tuple[str, ...]] = {
    "destination_country": (
        "Which country is this going to? (America, UK, UAE…)",
        "Where is the parcel headed?",
    ),
    "quantity": (
        "How many pieces are you shipping?",
        "What is the piece count?",
    ),
    "weight_grams": (
        "What is the total weight? (e.g. 400 grams or 2 kilos)",
        "What should the weight be?",
    ),
    "value_minor": (
        "What is the declared value? (e.g. ₹500)",
        "How much should we declare?",
    ),
    "consignee": (
        "Please tell me the recipient's name and address.",
        "Who should receive the parcel? Name and address, please.",
    ),
}


def ask_line_variants(lang: str, field: str, history_len: int) -> str:
    """A rotated 'ask' phrasing for ``field``; falls back to ``ask_line``.

    The variant is ``history_len % len(variants)`` — the caller passes a
    rotation index that advances every turn (e.g. the turn count) so repeated
    re-asks differ.  Fields without variants (``product_category``) fall back
    to the plain ask line.
    """
    options = (_ASK_VARIANTS_EN if lang == "en" else ASK_VARIANTS).get(field)
    if not options:
        return ask_line(lang, field)
    return options[history_len % len(options)]


FILLER_ACKS: dict[str, str] = {
    "hi": "ठीक है, समझ गया!",
    "en": "Okay, got it!",
}


def filler_reply(lang: str, field: str | None, history_len: int) -> str:
    """Warm filler acknowledgment plus a varied re-ask of the pending field."""
    ack = FILLER_ACKS.get(lang, FILLER_ACKS["hi"])
    if field is None:
        return ack
    return f"{ack} {ask_line_variants(lang, field, history_len)}"


def _stored_fragment(lang: str, field: str, value: object, db_info: dict[str, Any] | None) -> str:
    """One stored draft value, rendered for the off-topic 'noted' line."""
    display = _display_value(lang, field, value, db_info)
    if display is None:
        return ""
    template = ECHO_PARTS if lang == "hi" else ECHO_PARTS_EN
    return template[field].format(name=display, value=display)


def offtopic_reply(
    lang: str,
    stored_fields: list[str],
    draft: dict[str, Any],
    db_info: dict[str, Any] | None,
    next_field: str,
    history_len: int,
) -> str:
    """Acknowledge the volunteered fields, then re-ask the still-pending field.

    ``stored_fields`` names the fields that changed this turn (already merged
    into ``draft`` — the data is never lost); the pending field is re-asked
    with a rotated variant so the question is not a verbatim repeat of the
    last reply.
    """
    fragments = [_stored_fragment(lang, f, draft.get(f), db_info) for f in stored_fields]
    fragments = [f for f in fragments if f]
    parts: list[str] = []
    if fragments:
        parts.append(TEMPLATES[lang]["ack.stored"].format(stored=", ".join(fragments)))
    parts.append(ask_line_variants(lang, next_field, history_len))
    return " ".join(parts)


def consignee_readback(lang: str, value: object) -> str:
    """'शिखा, सही?' — read the stored consignee back once, folded into the ask."""
    display = _display_value(lang, "consignee", value, None)
    if display is None:
        return ""
    if lang == "hi":
        return f"{display}, सही?"
    return f"{display}, right?"


__all__ = [
    "ASK_VARIANTS",
    "FILLER_PHRASES",
    "FIELD_ORDER",
    "TEMPLATES",
    "ask_line",
    "ask_line_variants",
    "consignee_readback",
    "echo_line",
    "filler_reply",
    "is_filler",
    "offtopic_reply",
    "options_line",
]
