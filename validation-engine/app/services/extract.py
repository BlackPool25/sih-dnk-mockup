"""Extraction contract — Extractor protocol + the two implementations.

USER REQUIREMENTS (2026-08-09), encoded here:

1. **The model NEVER receives the conversation transcript.** The model-facing
   contract is ``Extractor.extract(previous, lang)`` — it takes ONLY the prior
   Shipment object (on a re-prompt) and a language tag.  ``raw_transcript`` on
   a prior Shipment is stripped before anything is handed back to the model.
   Only the demo rule engine takes the spoken text, and it is not an LLM.

2. **Verification is NEVER done by the model.** Parsing a model response and
   re-prompting happens in ``GeminiExtractor`` only on a *schema* error
   (``Shipment.model_validate``).  Business validation (ISO2, quantity/weight
   bounds, required fields) lives exclusively in ``app.services.validate``.

3. **No invented values.** Both extractors return the partial Shipment with
   sentinels (-1 / "unknown") for fields they could not determine, so the
   CALLER asks the user.  ``RuleExtractor`` raises ``CategoryUnknownError``
   rather than guessing a category; ``GeminiExtractor`` re-prompts rather than
   hallucinating.

``GeminiExtractor`` is NEVER called with a real client in this plan: there is
no API key and no network path.  Tests inject a mock client object.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Callable, Literal, Protocol

from pydantic import ValidationError

from app.schemas.shipment import (
    CATEGORY_SLUGS,
    CONSIGNEE_UNSTATED,
    DESTINATION_UNSTATED,
    QUANTITY_UNSTATED,
    VALUE_UNSTATED,
    WEIGHT_UNSTATED,
    Shipment,
    ShipmentDraft,
)
from app.services.mcp_tools import MCPTool


class Extractor(Protocol):
    """Model-facing extraction contract.

    ``extract`` deliberately takes NO transcript argument: the model is given
    ONLY the prior Shipment object (optionally) and a language tag.
    """

    def extract(self, previous: Shipment | None, lang: str) -> Shipment: ...


class CategoryUnknownError(ValueError):
    """Raised by ``RuleExtractor`` when no category keyword matches the text.

    The rule engine does not invent a category — the caller catches this and
    asks the user which of the 8 seeded categories applies.  ``partial_draft``
    carries any OTHER fields already extracted from the same utterance (the
    caller must not discard them when it re-asks).
    """

    def __init__(self, message: str, partial_draft: "ShipmentDraft | None" = None) -> None:
        super().__init__(message)
        self.partial_draft = partial_draft


# ---------------------------------------------------------------------------
# Number parsing (deterministic; English + Hindi + Kannada word numbers).
# ---------------------------------------------------------------------------

# Devanagari and Kannada digit characters -> ASCII, so "६" and "೬" parse as 6.
_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")
_KANNADA_DIGITS = str.maketrans("೦೧೨೩೪೫೬೭೮೯", "0123456789")

# number word -> value.  Values < 100 accumulate additively, 100/1000 act as
# multipliers (["four", 100] -> 400, ["twenty", "five"] -> 25).
_NUMBER_WORDS: dict[str, int] = {
    # English
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
    "hundred": 100,
    "thousand": 1000,
    # Hindi
    "शून्य": 0,
    "एक": 1,
    "दो": 2,
    "तीन": 3,
    "चार": 4,
    "पाँच": 5,
    "पांच": 5,
    "छह": 6,
    "छः": 6,
    "सात": 7,
    "आठ": 8,
    "नौ": 9,
    "दस": 10,
    "ग्यारह": 11,
    "बारह": 12,
    "तेरह": 13,
    "चौदह": 14,
    "पंद्रह": 15,
    "पन्द्रह": 15,
    "सोलह": 16,
    "सत्रह": 17,
    "अठारह": 18,
    "उन्नीस": 19,
    "बीस": 20,
    "तीस": 30,
    "चालीस": 40,
    "पचास": 50,
    "साठ": 60,
    "सत्तर": 70,
    "अस्सी": 80,
    "नब्बे": 90,
    "सौ": 100,
    "हज़ार": 1000,
    "हजार": 1000,
    # Kannada
    "ಸೊನ್ನೆ": 0,
    "ಒಂದು": 1,
    "ಎರಡು": 2,
    "ಮೂರು": 3,
    "ನಾಲ್ಕು": 4,
    "ಐದು": 5,
    "ಆರು": 6,
    "ಏಳು": 7,
    "ಎಂಟು": 8,
    "ಒಂಬತ್ತು": 9,
    "ಹತ್ತು": 10,
    "ನೂರು": 100,
    "ಸಾವಿರ": 1000,
}

# weight unit word -> multiplier to grams.
_WEIGHT_UNITS: dict[str, int] = {
    "g": 1,
    "gm": 1,
    "gram": 1,
    "grams": 1,
    "kg": 1000,
    "kgs": 1000,
    "kilo": 1000,
    "kilos": 1000,
    "kilogram": 1000,
    "kilograms": 1000,
    # Hindi
    "ग्राम": 1,
    "ग्राम्स": 1,
    "किलो": 1000,
    "किलोग्राम": 1000,
}

# Time-unit words: a number run before one of these is a clock/calendar
# reference ("दो बजे", "2 hours"), NEVER a quantity.
_TIME_UNITS: frozenset[str] = frozenset(
    {
        "hour",
        "hours",
        "minute",
        "minutes",
        "day",
        "days",
        "week",
        "weeks",
        "year",
        "years",
        "h",
        "m",
        "d",
        # Hindi
        "घंटे",
        "बजे",
        "दिन",
        "मिनट",
        "सप्ताह",
        "साल",
    }
)

# Quantity-unit words: a number run next to one of these is a COUNT, never a
# value utterance (used to gate the "पर"/"पे" price markers).
_QUANTITY_UNITS: frozenset[str] = frozenset(
    {
        "piece",
        "pieces",
        "pcs",
        "pc",
        # Hindi
        "टुकड़े",
        "टुकड़ा",
        "पीस",
        "नग",
    }
)

# A token is a run of word characters — \w covers ASCII + Unicode letters but
# NOT the Devanagari/Kannada combining marks (virama ्, matra ा) that join
# conjuncts like ग्राम into one word.  Include the full Indic script blocks
# so Hindi/Kannada weight units and number words tokenize as single tokens.
_INDIC_BLOCKS = "\u0900-\u097F\u0C80-\u0CFF"  # Devanagari + Kannada
_TOKEN_RE = re.compile(rf"[\w{_INDIC_BLOCKS}]+", re.UNICODE)


def _normalize(text: str) -> str:
    """ASCII digits for Indic numeral systems; lowercase for matching."""
    return text.translate(_DEVANAGARI_DIGITS).translate(_KANNADA_DIGITS).lower()


def _tokenize(text: str) -> list[tuple[str, int, int]]:
    """Return [(token, start, end), ...] over the normalized text."""
    return [(m.group(0), m.start(), m.end()) for m in _TOKEN_RE.finditer(text)]


def _number_value(token: str) -> int | None:
    if token.isdigit():
        return int(token)
    return _NUMBER_WORDS.get(token)


def _combine_numbers(values: list[int]) -> int:
    """Additive/multiplicative composition, e.g. [4, 100] -> 400."""
    total = 0
    current = 0
    for value in values:
        if value < 100:
            current += value
        else:
            current = current * value if current else value
            total += current
            current = 0
    return total + current


# ---------------------------------------------------------------------------
# Category keywords (English + Hindi + Kannada) -> seeded English slugs.
# ---------------------------------------------------------------------------

_CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "embroidered-home-textiles": (
        "cushion cover",
        "cushion covers",
        "cushion",
        "tablecloth",
        "table cloth",
        "bedspread",
        "bed spread",
        "embroidered",
        "embroidery",
        "कढ़ाई",
        "कुशन",
        "कुशन कवर",
        "टेबलक्लॉथ",
        "ಕುಶನ್",
        "ಬೆಡ್ ಸ್ಪ್ರೆಡ್",
        "ದಿಂಬಿನ ಹೊದಿಕೆ",
    ),
    "block-printed-textiles": (
        "block print",
        "block-print",
        "block printed",
        "blockprint",
        "hand block",
        "printing",
        "saree",
        "sari",
        "kurti",
        "ब्लॉक प्रिंट",
        "छपाई",
        "ಬ್ಲಾಕ್ ಪ್ರಿಂಟ್",
    ),
    "handloom-scarves-stoles": (
        "scarf",
        "scarves",
        "stole",
        "stoles",
        "muffler",
        "handloom",
        "dupatta",
        "शॉल",
        "दुपट्टा",
        "ಸ್ಕಾರ್ಫ್",
        "ಶಾಲು",
    ),
    "embroidered-bags-pouches": (
        "handbag",
        "sling bag",
        "tote",
        "clutch",
        "pouch",
        "pouches",
        "bag",
        "bags",
        "हैंडबैग",
        "थैला",
        "बैग",
        "कೈಚೀಲ",
        "ಪೌಚ್",
        "ಚೀಲ",
    ),
    "imitation-artisan-jewellery": (
        "jewellery",
        "jewelry",
        "necklace",
        "earring",
        "earrings",
        "bangle",
        "bangles",
        "jhumka",
        "imitation",
        "artificial",
        "आभूषण",
        "गहने",
        "कान की बाली",
        "ಆಭರಣ",
        "ಕಿವಿಯೋಲೆ",
    ),
    "jute-products": (
        "jute bag",
        "jute bags",
        "jute",
        "gunny",
        "जूट बैग",
        "जूट",
        "ಜೂಟ್",
        "ಗೋಣಿ",
    ),
    "small-brass-metalware": (
        "brassware",
        "brass",
        "metalware",
        "metal",
        "diya",
        "bell",
        "idol",
        "पीतल",
        "ಹಿತ್ತಾಳೆ",
        "ಕಂಚು",
    ),
    "small-woodware": (
        "woodware",
        "wooden",
        "wood",
        "carving",
        "bowl",
        "काष्ठ",
        "लकड़ी",
        "ಮರದ",
        "ಕೆತ್ತನೆ",
    ),
}

# ---------------------------------------------------------------------------
# Country aliases (English + Hindi + Kannada) -> ISO2.
# ---------------------------------------------------------------------------

_COUNTRY_ALIASES: dict[str, str] = {
    # America / USA — including the spoken-English forms users actually say
    "united states of america": "US",
    "united states": "US",
    "america": "US",
    "usa": "US",
    "us": "US",
    "u s": "US",
    "u.s.": "US",
    "यू एस": "US",
    "यूएस": "US",
    "यू.एस.": "US",
    "यू एस पी ओ": "US",
    "अमेरिका": "US",
    "ಅಮೆರಿಕಾ": "US",
    # United Kingdom / Britain
    "united kingdom": "GB",
    "britain": "GB",
    "uk": "GB",
    "u.k.": "GB",
    "england": "GB",
    "ब्रिटेन": "GB",
    "यूके": "GB",
    "यू के": "GB",
    "ಇಂಗ್ಲೆಂಡ್": "GB",
    # United Arab Emirates / Dubai
    "united arab emirates": "AE",
    "uae": "AE",
    "dubai": "AE",
    "दुबई": "AE",
    "ದುಬೈ": "AE",
    # Australia
    "australia": "AU",
    "ऑस्ट्रेलिया": "AU",
    "ಆಸ್ಟ್ರೇಲಿಯಾ": "AU",
    # Germany
    "germany": "DE",
    "जर्मनी": "DE",
    "ಜರ್ಮನಿ": "DE",
    # Canada
    "canada": "CA",
    "कनाडा": "CA",
    # France
    "france": "FR",
    "फ्रांस": "FR",
    # Japan
    "japan": "JP",
    "जापान": "JP",
}


def _match_country(text: str) -> str:
    """First matching country alias -> ISO2, else the ``unknown`` sentinel."""
    for alias in sorted(_COUNTRY_ALIASES, key=len, reverse=True):
        if alias in text:
            return _COUNTRY_ALIASES[alias]
    return DESTINATION_UNSTATED


def _is_command(text: str) -> bool:
    """True iff the utterance is a flow command (simulate/restart/help…)."""
    return bool(re.match(r"(?i)^\s*(simulate|order|restart|reset|help|cancel)\b", text))


def _is_pure_number(text: str) -> bool:
    """True iff the utterance is only a number (with optional unit/currency)."""
    return bool(re.match(r"^[\d\s,]+(?:g|kg|grams?|inr|rs|rupees?|₹)?\s*$", text, re.IGNORECASE))


def _match_category(text: str) -> str:
    """Pick the seeded slug with the LONGEST matching keyword.
    Longest-match resolves compounds deterministically: "jute bags" must be
    jute-products (via "jute bags"), not embroidered-bags-pouches (via "bags").
    Ties fall back to category order, then keyword text — fully deterministic.

    Raises ``CategoryUnknownError`` when nothing matches — the rule engine
    never invents a category; the caller asks the user instead.
    """
    best: tuple[int, int, str] | None = None  # (-len(keyword), cat_index, slug)
    for index, slug in enumerate(CATEGORY_SLUGS):
        for keyword in _CATEGORY_KEYWORDS[slug]:
            if keyword in text:
                candidate = (-len(keyword), index, slug)
                if best is None or candidate < best:
                    best = candidate
    if best is None:
        raise CategoryUnknownError(
            "could not map any category keyword from the text to one of the "
            f"seeded slugs: {', '.join(CATEGORY_SLUGS)} — ask the user"
        )
    return best[2]


def _confidence(qty_known: bool, weight_known: bool, country_known: bool) -> str:
    """3 known -> high, 2 -> medium, <=1 -> low."""
    known = sum((qty_known, weight_known, country_known))
    if known >= 3:
        return "high"
    if known == 2:
        return "medium"
    return "low"


# ---------------------------------------------------------------------------
# RuleExtractor — the deterministic demo default (not an LLM).
# ---------------------------------------------------------------------------


class RuleExtractor(Extractor):
    """Deterministic regex/word-mapping extractor for the demo default.

    The APP calls ``extract_from_text(text, lang)`` with the spoken text (this
    is a rule engine, not a model — the transcript restriction does not apply
    to it).  ``extract(previous, lang)`` exists only for protocol parity and
    raises, because a rule engine has nothing to extract from without text.
    """

    def extract(self, previous: Shipment | None, lang: str) -> Shipment:
        raise NotImplementedError(
            "RuleExtractor needs the spoken text — call extract_from_text(text, lang)"
        )

    def extract_from_text(self, text: str, lang: str) -> Shipment:
        original = text
        normalized = _normalize(text)
        tokens = _tokenize(normalized)

        weight, weight_indices = _extract_weight(tokens)
        quantity = _extract_quantity(tokens, weight_indices)

        country = _match_country(normalized)
        category = _match_category(normalized)

        return Shipment(
            product_category=category,
            quantity=quantity if quantity is not None else QUANTITY_UNSTATED,
            weight_grams=weight if weight is not None else WEIGHT_UNSTATED,
            destination_country=country,
            confidence=_confidence(
                quantity is not None,
                weight is not None,
                country != DESTINATION_UNSTATED,
            ),
            raw_transcript=original,
        )


def _extract_weight(
    tokens: list[tuple[str, int, int]],
) -> tuple[int | None, set[int]]:
    """Find ``<number words> <weight unit>``; return (grams, consumed indices).

    ``"four hundred grams"`` -> (400, {i...}).  ``"2 kg"`` -> (2000, {...}).
    No match -> (None, set()).
    """
    index = 0
    while index < len(tokens):
        token, _, _ = tokens[index]
        if _number_value(token) is None:
            index += 1
            continue
        # Gather the maximal run of consecutive number tokens.
        run = []
        cursor = index
        while cursor < len(tokens) and _number_value(tokens[cursor][0]) is not None:
            run.append(cursor)
            cursor += 1
        if cursor < len(tokens) and tokens[cursor][0] in _WEIGHT_UNITS:
            values = [_number_value(tokens[i][0]) for i in run]
            multiplier = _WEIGHT_UNITS[tokens[cursor][0]]
            return _combine_numbers(values) * multiplier, {*run, cursor}
        index = cursor  # skip the number run — don't rescan inside it
    return None, set()


def _extract_time_indices(tokens: list[tuple[str, int, int]]) -> set[int]:
    """Indices of number runs immediately followed by a time unit.

    ``"दो बजे"`` / ``"2 hours"`` are clock/calendar references, never
    quantities: mirror ``_extract_weight``'s run+unit scan and mark the whole
    run so ``_extract_quantity`` skips it.
    """
    indices: set[int] = set()
    index = 0
    while index < len(tokens):
        if _number_value(tokens[index][0]) is None:
            index += 1
            continue
        start = index
        while index < len(tokens) and _number_value(tokens[index][0]) is not None:
            index += 1
        if index < len(tokens) and tokens[index][0] in _TIME_UNITS:
            indices.update(range(start, index))
    return indices


def _extract_quantity(tokens: list[tuple[str, int, int]], exclude: set[int]) -> int | None:
    """First number run not consumed by an earlier extractor (weight/time/value)
    -> the quantity, or None."""
    index = 0
    while index < len(tokens):
        if index in exclude or _number_value(tokens[index][0]) is None:
            index += 1
            continue
        values = []
        cursor = index
        while cursor < len(tokens) and _number_value(tokens[cursor][0]) is not None:
            if cursor not in exclude:
                values.append(_number_value(tokens[cursor][0]))
            cursor += 1
        return _combine_numbers(values)
    return None


# ---------------------------------------------------------------------------
# GeminiExtractor — LLM adapter.  Mocked-only in this plan (no API key).
# ---------------------------------------------------------------------------

# Instruction strings used in the model prompt — the transcript is NEVER part
# of these contents; the model sees only the schema and (on a re-prompt) the
# prior Shipment object with raw_transcript stripped.
_FIRST_PROMPT = (
    "Extract the export shipment described in your current context. "
    "Reply with ONLY JSON that validates against the response_schema. "
    "For any field you cannot determine, use the contract sentinels "
    "(-1 for quantity and weight_grams, 'unknown' for destination_country)."
)

_REPROMPT_PROMPT = (
    "Your previous response failed schema validation. "
    "Reply with ONLY JSON that validates against the response_schema. "
    "You may use the prior Shipment object for consistency, but never invent "
    "fields you do not know — use the contract sentinels."
)


class GeminiExtractor(Extractor):
    """LLM adapter implementing the extraction contract.

    Guardrails:
    - ``response_schema=Shipment.model_json_schema()`` with thinking disabled
      (``thinking_config={"thinking_budget": 0}``).
    - ``extract`` NEVER receives the transcript: the model gets only the
      schema and, on a re-prompt, ``previous.model_dump(exclude={"raw_transcript"})``.
    - Any thinking block in the (mock) response is dropped and never persisted
      as a fact; ``raw_transcript`` on the produced Shipment stays ``None``.
    - Schema ValidationError -> re-prompt (max ``max_reprompts`` times) with
      ONLY the schema + prior Shipment.  Business validation stays in
      ``app.services.validate`` — the model never validates.
    """

    def __init__(self, client: Any, max_reprompts: int = 2):
        # `client` is a MOCK in every test and every current caller — never a
        # real Gemini client, never an API key, never a network call.
        self._client = client
        self._max_reprompts = max_reprompts

    def extract(self, previous: Shipment | None, lang: str) -> Shipment:
        schema = Shipment.model_json_schema()
        config = {"response_schema": schema, "thinking_config": {"thinking_budget": 0}}
        response = self._client.generate_content(
            config=config,
            contents=[{"instruction": _FIRST_PROMPT, "response_schema": schema}],
        )
        last_error: Exception | None = None
        for _ in range(self._max_reprompts + 1):
            shipment, last_error = _try_parse(response)
            if shipment is not None:
                return shipment
            prior = _prior_without_transcript(previous)
            response = self._client.generate_content(
                config=config,
                contents=[
                    {"instruction": _REPROMPT_PROMPT, "response_schema": schema},
                    {"prior_shipment": prior},
                ],
            )
        raise ValueError(
            "GeminiExtractor could not produce a schema-valid Shipment after "
            f"{self._max_reprompts + 1} attempt(s): {last_error}"
        )


def _try_parse(response: Any) -> tuple[Shipment | None, Exception | None]:
    """Parse a model response into a Shipment.

    The response text is JSON (Gemini's structured-output convention); it is
    ``json.loads``-ed (code fences stripped defensively) and validated with
    ``Shipment.model_validate``.  Returns (None, error) when the JSON or the
    schema validation fails — the caller re-prompts.  The model never
    validates; only Pydantic + app.services.validate decide.
    """
    try:
        text = _non_thinking_text(response)
        data = json.loads(_strip_code_fence(text)) if isinstance(text, str) else text
        return Shipment.model_validate(data), None
    except (ValidationError, ValueError) as exc:
        return None, exc


def _strip_code_fence(text: str) -> str:
    """Strip a ```json ... ``` wrapper some models add around structured JSON."""
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped)
        stripped = re.sub(r"\s*```$", "", stripped)
    return stripped


def _prior_without_transcript(previous: Shipment | None) -> dict | None:
    """The prior Shipment as the model may see it — raw_transcript stripped.

    This is the USER-REQUIREMENT guarantee: even if the demo log stored the
    transcript on a Shipment, the LLM re-prompt never contains it.
    """
    if previous is None:
        return None
    return previous.model_dump(exclude={"raw_transcript"})


def _non_thinking_text(response: Any) -> str:
    """Extract the final text, dropping any thinking blocks from the response.

    The mock may model Gemini's ``parts`` list, where thought blocks carry
    ``thought=True``; those are dropped and never persisted as facts.
    """
    if isinstance(response, str):
        return response
    parts = getattr(response, "parts", None)
    if parts is not None:
        chunks = []
        for part in parts:
            if getattr(part, "thought", False):
                continue  # thinking block — dropped
            text = getattr(part, "text", "")
            if text:
                chunks.append(text)
        return "".join(chunks)
    return getattr(response, "text", "")


# ---------------------------------------------------------------------------
# Draft extraction — the multi-turn accumulation contract (Wave 1).
# ---------------------------------------------------------------------------

# Currency signals -> which side the amount sits on: "right" = the symbol
# precedes the number (₹15000), "left" = the word follows it (15000 rupees).
_CURRENCY_SIGNALS: tuple[tuple[str, str], ...] = (
    ("₹", "right"),
    ("rs", "left"),
    ("inr", "left"),
    ("rupees", "left"),
    ("रुपये", "left"),
    ("रुपए", "left"),
    ("$", "right"),
    ("usd", "left"),
)

# Consignee markers -> whether the name precedes (-1) or follows (+1) the
# marker: Hindi postpositions follow the name (जॉन को भेजें), English markers
# precede it (send to John).
_CONSIGNEE_MARKERS: tuple[tuple[str, int], ...] = (
    ("को भेजना है", -1),
    ("को भेजें", -1),
    ("send to", 1),
    ("ship to", 1),
    ("for", 1),
    ("consignee", 1),
    ("recipient", 1),
)

_ARTICLE_RE = re.compile(r"^(?:the|a|an)\s+", re.IGNORECASE)

# Hindi recipient postposition: "शिखा को अमेरिका में भेजना है" — the strict
# "को भेजना है" marker misses it because the verb is NOT adjacent to the को.
# Group 1 captures the pre-को name; the rest must contain a Hindi send verb.
# Python's \b is unreliable after Devanagari vowel signs (ो/ै are not \w), so
# both boundaries use a lookahead that rejects a continuing token character.
_TOKEN_CHARS = rf"\w{_INDIC_BLOCKS}"
_NOT_TOKEN = rf"(?![{_TOKEN_CHARS}])"
_RECIPIENT_KO_RE = re.compile(
    rf"^(.+?)\s*को{_NOT_TOKEN}[^।.!?]*(?:भेजना है|भेजो|भेजें|भेज){_NOT_TOKEN}"
)

# Postpositions that end a captured recipient name — grammar, never the name.
_POSTPOSITIONS = ("को", "में", "मे", "से", "पर")


def _draft_confidence(known: int) -> Literal["high", "medium", "low"]:
    """Six-field known-count bands: >=4 high, 2-3 medium, <=1 low."""
    if known >= 4:
        return "high"
    if known >= 2:
        return "medium"
    return "low"


def draft_confidence(draft: ShipmentDraft) -> Literal["high", "medium", "low"]:
    """Known-count confidence over a draft's six fields (>=4 high, 2-3 medium, <=1 low)."""
    return _draft_confidence(
        sum(
            (
                draft.product_category is not None,
                draft.quantity != QUANTITY_UNSTATED,
                draft.weight_grams != WEIGHT_UNSTATED,
                draft.destination_country != DESTINATION_UNSTATED,
                draft.consignee != CONSIGNEE_UNSTATED,
                draft.value_minor != VALUE_UNSTATED,
            )
        )
    )


def category_candidates(text: str) -> list[str]:
    """Category slugs whose keyword vocabulary intersects the text.

    The deterministic counterpart to ``_match_category``: instead of picking
    ONE best slug, returns every slug whose English/Hindi/Kannada keyword
    appears in the (normalized) text.  The chat turns these into numbered
    options when the exact category could not be resolved — the disambiguation
    contract.  Empty when the text matches nothing.
    """
    normalized = _normalize(text)
    hits: list[str] = []
    for slug in CATEGORY_SLUGS:
        for keyword in _CATEGORY_KEYWORDS[slug]:
            if keyword in normalized:
                hits.append(slug)
                break
    return hits


def _extract_consignee(text: str) -> str:
    """Name/address next to a consignee marker, else the ``unknown`` sentinel.

    The earliest marker wins (longer markers preferred on a tie).  Hindi
    markers are postpositions so the name precedes them ("जॉन को भेजें");
    English markers take the text that follows ("send to John").  Leading
    articles and surrounding punctuation are stripped; ~80 chars max.
    """
    normalized = _normalize(text)
    best: tuple[int, int, int, str] | None = None  # (pos, -len(marker), side, marker)
    for marker, side in _CONSIGNEE_MARKERS:
        pos = normalized.find(marker)
        if pos != -1 and (best is None or (pos, -len(marker)) < (best[0], best[1])):
            best = (pos, -len(marker), side, marker)
    if best is None:
        # Recipient-को fallback: "शिखा को अमेरिका में भेजना है" has no
        # contiguous marker, but the pre-को name is the consignee.
        match = _RECIPIENT_KO_RE.match(normalized)
        if match is not None:
            start, end = match.span(1)
            segment = _truncate_at_postposition(text[start:end])
            segment = _ARTICLE_RE.sub("", segment.strip()).strip(" ,:;")
            if segment:
                return segment[:80]
        return CONSIGNEE_UNSTATED
    pos, _, side, marker = best
    segment = text[:pos] if side < 0 else text[pos + len(marker):]
    segment = _ARTICLE_RE.sub("", segment.strip()).strip(" ,:;")
    if not segment:
        return CONSIGNEE_UNSTATED
    return segment[:80]


def _truncate_at_postposition(name: str) -> str:
    """Cut a captured recipient name at the first Hindi postposition token.

    A postposition (को/में/मे/से/पर) is grammar, never part of the name —
    "शिखा को अमेरिका" truncates to "शिखा".
    """
    for token, start, _ in _tokenize(name):
        if token in _POSTPOSITIONS:
            return name[:start].rstrip()
    return name


def _currency_amount_span(normalized: str) -> tuple[int, int] | None:
    """(start, end) of the digit amount beside the FIRST currency signal.

    Supports value keywords (value 15000), preceding/trailing symbols (₹15000 / 15000₹),
    and currency units (15000 rupees). None when no signal has a number.
    """
    val_kw_match = re.search(r"(?:value|price|cost|मूल्य|कीमत|दाम)\s*(?:of|is|:|-)?\s*(?:₹|\$|rs\.?|inr)?\s*(\d[\d,]*)", normalized, re.IGNORECASE)
    if val_kw_match:
        return val_kw_match.span(1)

    for signal, side in _CURRENCY_SIGNALS:
        for m in re.finditer(re.escape(signal), normalized):
            pos = m.start()
            left_match = re.search(r"(\d[\d,]*)\s*$", normalized[:pos])
            if left_match:
                return left_match.span(1)
            right_match = re.search(r"^\s*(\d[\d,]*)", normalized[pos + len(signal):])
            if right_match:
                start, end = right_match.span(1)
                return pos + len(signal) + start, pos + len(signal) + end
    return None


def _extract_value_minor(text: str) -> int:
    """Declared amount in INR minor units next to a currency signal.

    ``₹``/``$`` precede the amount ("₹15000"); the word signals follow it
    ("15000 rupees", "15000 रुपये").  Indic digits are normalised first; a
    comma-separated amount is accepted.  No signal, or no adjacent number, ->
    the -1 sentinel.
    """
    normalized = _normalize(text)
    span = _currency_amount_span(normalized)
    if span is None:
        return VALUE_UNSTATED
    start, end = span
    return int(normalized[start:end].replace(",", "")) * 100


def _token_indices_over(
    tokens: list[tuple[str, int, int]], start: int, end: int
) -> set[int]:
    """Indices of tokens overlapping the normalized-text span [start, end)."""
    return {
        i
        for i, (_, token_start, token_end) in enumerate(tokens)
        if token_start < end and start < token_end
    }


def _price_marker_len(
    tokens: list[tuple[str, int, int]], index: int
) -> int:
    """Token count of a price-marker phrase starting at ``index`` (0 = none).

    Single-token markers: पे/पर/कीमत; two-token phrases: का दाम, की कीमत.
    """
    if index >= len(tokens):
        return 0
    token = tokens[index][0]
    if token in ("पे", "पर", "कीमत"):
        return 1
    if token in ("का", "की"):
        nxt = tokens[index + 1][0] if index + 1 < len(tokens) else ""
        if (token, nxt) in (("का", "दाम"), ("की", "कीमत")):
            return 2
    return 0


def _unit_adjacent(
    tokens: list[tuple[str, int, int]], start: int, end: int
) -> bool:
    """A quantity/weight/time unit token hugs the number run [start, end)."""
    before = tokens[start - 1][0] if start > 0 else None
    after = tokens[end][0] if end < len(tokens) else None
    return (
        before in _QUANTITY_UNITS
        or after in _QUANTITY_UNITS
        or before in _WEIGHT_UNITS
        or after in _WEIGHT_UNITS
        or before in _TIME_UNITS
        or after in _TIME_UNITS
    )


def _run_is_value(
    tokens: list[tuple[str, int, int]],
    start: int,
    end: int,
    expected: str | None,
) -> bool:
    """A number run is a VALUE utterance iff a price marker hugs it, or the
    caller explicitly asked for the value — and in BOTH cases the run is NOT
    pinned to a quantity/weight/time unit (a number beside a unit stays
    quantity/weight).  The "पर"/"पे" markers are deliberately gated this way
    so "2 टुकड़े पे" never reads as an amount."""
    price_hug = (
        (start > 0 and _price_marker_len(tokens, start - 1) > 0)
        or (start > 1 and _price_marker_len(tokens, start - 2) == 2)
        or (end < len(tokens) and _price_marker_len(tokens, end) > 0)
    )
    if not price_hug and expected != "value_minor":
        return False
    return not _unit_adjacent(tokens, start, end)


def _extract_value_utterance(
    tokens: list[tuple[str, int, int]],
    normalized: str,
    expected: str | None,
) -> tuple[int, set[int]]:
    """Declared amount in INR minor units + the token indices it consumed.

    Fires when (a) a currency signal is present (reusing ``_extract_value_minor``),
    (b) a price marker hugs a number run not pinned to a quantity/weight/time
    unit, or (c) the caller explicitly asked for the value (``expected ==
    "value_minor"``) and the run is not pinned to a unit.  Returns
    ``(VALUE_UNSTATED, set())`` when nothing qualifies.  The consumed indices
    are unioned into ``_extract_quantity``'s exclude set so a value number is
    never re-read as the quantity.
    """
    span = _currency_amount_span(normalized)
    if span is not None:
        start, end = span
        return _extract_value_minor(normalized), _token_indices_over(tokens, start, end)
    index = 0
    while index < len(tokens):
        if _number_value(tokens[index][0]) is None:
            index += 1
            continue
        start = index
        while index < len(tokens) and _number_value(tokens[index][0]) is not None:
            index += 1
        if _run_is_value(tokens, start, index, expected):
            values = [
                v
                for v in (_number_value(tokens[i][0]) for i in range(start, index))
                if v is not None
            ]
            return _combine_numbers(values) * 100, set(range(start, index))
    return VALUE_UNSTATED, set()


class DraftExtractor(Protocol):
    """Model-facing multi-turn extraction contract.

    Same shape as ``Extractor`` but over ``ShipmentDraft``: the model is given
    ONLY the prior draft object (optionally) and a language tag — never the
    transcript.
    """

    def extract(self, previous: ShipmentDraft | None, lang: str) -> ShipmentDraft: ...


class RuleDraftExtractor(DraftExtractor):
    """Deterministic draft extractor — the ``RuleExtractor`` engine plus the
    consignee/value signals, with previous-draft carry-forward.

    ``extract_from_text`` merges over the previous draft: an extracted value
    always wins, a sentinel keeps the previous value.  The category carries
    forward from the previous draft when the text yields no keyword;
    ``CategoryUnknownError`` re-raises only when there is no previous category
    to carry.  ``extract`` exists for protocol parity and raises (a rule
    engine needs the spoken text).
    """

    def extract(self, previous: ShipmentDraft | None, lang: str) -> ShipmentDraft:
        raise NotImplementedError(
            "RuleDraftExtractor needs the spoken text — call "
            "extract_from_text(text, lang, previous)"
        )

    def extract_from_text(
        self, text: str, lang: str, previous: ShipmentDraft | None = None,
        expected: str | None = None,
    ) -> ShipmentDraft:
        original = text
        normalized = _normalize(text)
        tokens = _tokenize(normalized)

        # Extraction order (Wave 1 T2): time indices -> value indices -> weight
        # -> quantity, with each stage's consumed indices unioned into the
        # exclude set so a number run is claimed exactly once (a value number
        # is never re-read as quantity, "दो घंटे" is never quantity, etc.).
        time_indices = _extract_time_indices(tokens)
        value_minor, value_indices = _extract_value_utterance(
            tokens, normalized, expected
        )
        weight, weight_indices = _extract_weight(tokens)
        quantity = _extract_quantity(
            tokens, time_indices | value_indices | weight_indices
        )

        country = _match_country(normalized)
        consignee = _extract_consignee(original)

        # A consignee-only utterance ("जॉन डो, 123 बर्लिन को भेजना है") is the
        # answer to the pending consignee question — the address's digits
        # ("123") are NOT a quantity/weight/value re-statement.  When an
        # explicit consignee marker fired, carry the numeric fields forward
        # instead of re-extracting them from the address text.
        if consignee != CONSIGNEE_UNSTATED and previous is not None:
            quantity = previous.quantity
            weight_grams = previous.weight_grams
            value_minor = previous.value_minor

        # Case B (PR #2): when the user is answering the pending consignee
        # question with a plain name+address (no marker — the common case),
        # the WHOLE utterance is the consignee, not a re-statement of numbers.
        # Guarded by the ``expected`` hint so a stray multi-field turn is never
        # swallowed.  Commands and pure numbers are still rejected.
        if (
            expected == "consignee"
            and consignee == CONSIGNEE_UNSTATED
            and not _is_command(text)
            and not _is_pure_number(text)
            and len(text.strip()) >= 3
        ):
            consignee = text.strip()[:80]
            # The address's digits are part of the name — never quantities.
            quantity = previous.quantity if previous else QUANTITY_UNSTATED
            weight_grams = previous.weight_grams if previous else WEIGHT_UNSTATED
            value_minor = previous.value_minor if previous else VALUE_UNSTATED

        quantity = (
            quantity if quantity is not None else (previous.quantity if previous else QUANTITY_UNSTATED)
        )
        weight_grams = (
            weight if weight is not None else (previous.weight_grams if previous else WEIGHT_UNSTATED)
        )
        country = (
            country
            if country != DESTINATION_UNSTATED
            else (previous.destination_country if previous else DESTINATION_UNSTATED)
        )
        consignee = (
            consignee
            if consignee != CONSIGNEE_UNSTATED
            else (previous.consignee if previous else CONSIGNEE_UNSTATED)
        )
        value_minor = (
            value_minor
            if value_minor != VALUE_UNSTATED
            else (previous.value_minor if previous else VALUE_UNSTATED)
        )

        # Category resolution happens LAST: every other field is already
        # extracted, so an unknown category can attach them to the exception
        # instead of the caller losing the turn's partial progress.
        try:
            category = _match_category(normalized)
        except CategoryUnknownError:
            if previous is not None and previous.product_category is not None:
                category = previous.product_category
            else:
                partial = ShipmentDraft(
                    product_category=None,
                    quantity=quantity,
                    weight_grams=weight_grams,
                    destination_country=country,
                    consignee=consignee,
                    value_minor=value_minor,
                    confidence=_draft_confidence(
                        sum(
                            (
                                quantity != QUANTITY_UNSTATED,
                                weight_grams != WEIGHT_UNSTATED,
                                country != DESTINATION_UNSTATED,
                                consignee != CONSIGNEE_UNSTATED,
                                value_minor != VALUE_UNSTATED,
                            )
                        )
                    ),
                    raw_transcript=original,
                )
                raise CategoryUnknownError(
                    "could not map any category keyword from the text to one of "
                    f"the seeded slugs: {', '.join(CATEGORY_SLUGS)} — ask the user",
                    partial_draft=partial,
                ) from None

        return ShipmentDraft(
            product_category=category,
            quantity=quantity,
            weight_grams=weight_grams,
            destination_country=country,
            consignee=consignee,
            value_minor=value_minor,
            confidence=_draft_confidence(
                sum(
                    (
                        category is not None,
                        quantity != QUANTITY_UNSTATED,
                        weight_grams != WEIGHT_UNSTATED,
                        country != DESTINATION_UNSTATED,
                        consignee != CONSIGNEE_UNSTATED,
                        value_minor != VALUE_UNSTATED,
                    )
                )
            ),
            raw_transcript=original,
        )


# Prompts for the draft LLM adapter — the transcript is NEVER part of a
# re-prompt: the model sees only the schema and (on a re-prompt) the prior
# draft with raw_transcript stripped.
_DRAFT_FIRST_PROMPT = (
    "Extract the export shipment details explicitly stated in the transcript into the response_schema. "
    "Reply with ONLY JSON that validates against the response_schema.\n\n"
    "STRICT ANTI-HALLUCINATION & EXTRACTION RULES:\n"
    "1. ZERO FABRICATION: Do NOT invent, assume, generate, or hallucinate ANY field value that was not explicitly provided by the user. "
    "If the user did not specify a field in the transcript, you MUST use the contract sentinel value.\n"
    "2. SENTINEL DISCIPLINE: Use these exact sentinels for any missing or unmentioned field:\n"
    "   - product_category: null\n"
    "   - quantity: -1\n"
    "   - weight_grams: -1\n"
    "   - destination_country: 'unknown'\n"
    "   - consignee: 'unknown'\n"
    "   - value_minor: -1\n"
    "3. CATEGORY MATCHING: If the product is mentioned, map it to one of the enum category slugs in the schema. If unclear or not mentioned, set product_category to null. Never invent a category.\n"
    "4. RECIPIENT / CONSIGNEE: If the user provides the recipient's buyer name and/or delivery address (e.g. 'John Doe, 101 Street Munich Germany'), extract it into consignee as 'Name, Address' (or just Name/Address if only one is given). If not stated, set to 'unknown'.\n"
    "5. VALUE IN MINOR UNITS: Declared value is in INR minor units (paise). Multiply Rupees by 100 (e.g., ₹15,000 -> 1500000). Do NOT confuse street numbers or other non-currency numbers with the value.\n"
)

_DRAFT_REPROMPT_PROMPT = (
    "Your previous response failed schema validation. "
    "Reply with ONLY JSON that validates against the response_schema. "
    "Never invent or hallucinate fields you do not know — strictly use the contract sentinels."
)


def _clean_schema(schema: dict) -> dict:
    """Drop ``title``/``default`` keys recursively — the model must fill every
    field from the enum/type only, never from a default value.

    Also rewrites Pydantic v2's ``X | None`` encoding (``anyOf`` with a
    ``{"type": "null"}`` branch) into the SDK Schema's ``nullable: true`` —
    the google.generativeai proto rejects ``anyOf`` (``ValueError: Unknown
    field for Schema: anyOf``), so the live path needs this conversion.
    """
    cleaned: dict[str, object] = {}
    for key, value in schema.items():
        if key in ("title", "default"):
            continue
        if key == "anyOf" and isinstance(value, list):
            non_null = [item for item in value if isinstance(item, dict) and item.get("type") != "null"]
            if len(non_null) == 1 and isinstance(non_null[0], dict):
                cleaned.update({k: _clean_schema(v) if isinstance(v, dict) else v for k, v in non_null[0].items() if k not in ("title", "default")})
                cleaned["nullable"] = True
                continue
        cleaned[key] = _clean_schema(value) if isinstance(value, dict) else value
    return cleaned


def _normalize_tools(
    tools: list[MCPTool] | list[tuple[str, Callable[..., Any]]],
) -> list[MCPTool]:
    """Normalize the legacy ``(name, callable)`` tuple form to ``MCPTool``."""
    normalized: list[MCPTool] = []
    for entry in tools:
        if isinstance(entry, MCPTool):
            normalized.append(entry)
        else:
            name, handler = entry
            normalized.append(
                MCPTool(
                    name=name,
                    description=f"Call {name} to look up the answer.",
                    parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
                    handler=handler,
                )
            )
    return normalized


def _schema_to_proto(schema: dict, protos: Any) -> Any:
    """JSON-schema subset → ``protos.Schema``.

    The google-generativeai SDK accepts a fixed Schema proto field set
    (type, format, description, nullable, enum, items, properties, required);
    anything else (title/default) is dropped.
    """
    type_map = {
        "string": protos.Type.STRING,
        "integer": protos.Type.INTEGER,
        "number": protos.Type.NUMBER,
        "boolean": protos.Type.BOOLEAN,
        "array": protos.Type.ARRAY,
        "object": protos.Type.OBJECT,
    }
    kwargs: dict[str, object] = {
        "type": type_map.get(schema.get("type", "string"), protos.Type.STRING),
    }
    for key in ("format", "description", "enum", "nullable"):
        if key in schema:
            kwargs[key] = schema[key]
    items = schema.get("items")
    if isinstance(items, dict):
        kwargs["items"] = _schema_to_proto(items, protos)
    properties = schema.get("properties")
    if isinstance(properties, dict):
        kwargs["properties"] = {
            name: _schema_to_proto(prop, protos)
            for name, prop in properties.items()
            if isinstance(prop, dict)
        }
    required = schema.get("required")
    if isinstance(required, list):
        kwargs["required"] = [str(r) for r in required]
    return protos.Schema(**kwargs)


class _GenaiModelAdapter:
    """Translate the (config, contents) call shape to the real genai SDK.

    Supports function calling: when ``tools`` is given (a list of ``MCPTool``
    objects, or legacy ``(name, callable)`` pairs), a model function_call is
    executed and its result is fed back in the SDK-native Content/Part format
    until the model returns plain text.  The registry is the curated
    model-facing surface from ``app.services.mcp_tools`` — precise per-tool
    parameter schemas and named-argument dispatch (``executor(**call.args)``).
    """

    def __init__(
        self,
        model: Any,
        tools: list[MCPTool] | list[tuple[str, Callable[..., Any]]] | None = None,
    ) -> None:
        self._model = model
        self._tool_list = _normalize_tools(tools or [])
        self._tools = {tool.name: tool.handler for tool in self._tool_list}

    @staticmethod
    def _render_prompt(contents: list[dict]) -> str:
        """Flatten mock-shaped content dicts into one plain-text prompt.

        Each dict carries one role: ``instruction`` (+ optional
        ``response_schema``) is the task text, ``transcript`` the current
        utterance, ``prior_draft``/``prior_shipment`` a prior-state dump.
        The real SDK rejects bare dict contents, so the adapter joins the
        parts into a single prompt string.
        """
        sections: list[str] = []
        for item in contents:
            instruction = item.get("instruction")
            if instruction:
                sections.append(instruction)
            transcript = item.get("transcript")
            if transcript:
                sections.append(f"Transcript: {transcript}")
            prior = item.get("prior_draft") or item.get("prior_shipment")
            if prior is not None:
                sections.append(f"Prior state: {json.dumps(prior, ensure_ascii=False)}")
        return "\n\n".join(sections)

    def generate_content(self, config: dict, contents: list[dict]) -> Any:
        generation_config: dict[str, object] = {
            "response_mime_type": "application/json",
            "response_schema": config["response_schema"],
        }
        # The google-generativeai 0.8.x GenerationConfig has no thinking field;
        # the schema validation + reprompt loop enforces correctness instead.
        prompt = self._render_prompt(contents)
        if not self._tools:
            return self._model.generate_content(
                prompt,
                generation_config=generation_config,
            )
        return self._generate_with_tools(prompt, generation_config)

    def _generate_with_tools(self, prompt: str, generation_config: dict[str, object]) -> Any:
        """Run the function-calling loop: model → tool call → tool result →
        model, until the model returns plain text (max 3 rounds)."""
        try:
            from google.generativeai import protos
        except ImportError:  # pragma: no cover — SDK present whenever tools are
            return self._model.generate_content(
                prompt, generation_config=generation_config
            )
        declarations = [
            protos.FunctionDeclaration(
                name=tool.name,
                description=tool.description,
                parameters=_schema_to_proto(tool.parameters, protos),
            )
            for tool in self._tool_list
        ]
        tool = protos.Tool(function_declarations=declarations)
        conversation = [protos.Content(role="user", parts=[protos.Part(text=prompt)])]
        for _ in range(3):
            response = self._model.generate_content(
                conversation,
                generation_config=generation_config,
                tools=[tool],
            )
            function_calls = [
                p.function_call for p in response.parts if getattr(p, "function_call", None)
            ]
            if not function_calls:
                return response
            conversation.append(protos.Content(role="model", parts=response.parts))
            tool_parts = []
            for call in function_calls:
                executor = self._tools.get(call.name)
                if executor is None:
                    tool_parts.append(
                        protos.Part(
                            function_response=protos.FunctionResponse(
                                name=call.name,
                                response={"error": f"unknown tool {call.name}"},
                            )
                        )
                    )
                    continue
                args = dict(call.args or {})
                result = executor(**args)
                tool_parts.append(
                    protos.Part(
                        function_response=protos.FunctionResponse(
                            name=call.name,
                            response={"results": result},
                        )
                    )
                )
            conversation.append(
                protos.Content(role="user", parts=tool_parts)
            )
        return response


def _build_genai_client() -> Any:
    """The real genai model wrapper from the env key, built lazily.

    Raises ``RuntimeError`` when GEMINI_API_KEY is absent — checked BEFORE the
    optional import so tests pass without the package or a key.
    """
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY not set")
    from google.generativeai.client import configure
    from google.generativeai.generative_models import GenerativeModel

    configure(api_key=key)
    model = GenerativeModel(os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite"))
    from app.services.mcp_tools import get_mcp_tools

    return _GenaiModelAdapter(model, tools=get_mcp_tools())


class GeminiDraftExtractor(DraftExtractor):
    """LLM adapter over the draft contract (Wave 1).

    Guardrails (mirror ``GeminiExtractor``):
    - the transcript appears ONLY as the initial model content — it is never
      stored on the produced draft (``raw_transcript`` stays None) and never
      included in a re-prompt (re-prompts carry only the schema + the prior
      draft with ``raw_transcript`` stripped);
    - ``response_schema=ShipmentDraft.model_json_schema()`` (title/default
      keys stripped) with thinking disabled;
    - schema ValidationError -> re-prompt (max ``max_reprompts``); business
      validation stays in app.services.validate — the model never validates.
    """

    def __init__(self, client: Any | None = None, max_reprompts: int = 2):
        self._client = client
        self._max_reprompts = max_reprompts

    def extract(
        self, transcript: str, previous: ShipmentDraft | None, lang: str
    ) -> ShipmentDraft:
        client = self._client
        if client is None:
            client = _build_genai_client()
        schema = _clean_schema(ShipmentDraft.model_json_schema())
        config = {"response_schema": schema, "thinking_config": {"thinking_budget": 0}}
        response = client.generate_content(
            config=config,
            contents=[
                {
                    "instruction": _DRAFT_FIRST_PROMPT,
                    "response_schema": schema,
                    "transcript": transcript,
                }
            ],
        )
        last_error: Exception | None = None
        for _ in range(self._max_reprompts + 1):
            draft, last_error = _try_parse_draft(response)
            if draft is not None:
                return draft
            prior = _prior_draft_without_transcript(previous)
            response = client.generate_content(
                config=config,
                contents=[
                    {"instruction": _DRAFT_REPROMPT_PROMPT, "response_schema": schema},
                    {"prior_draft": prior},
                ],
            )
        raise ValueError(
            "GeminiDraftExtractor could not produce a schema-valid ShipmentDraft "
            f"after {self._max_reprompts + 1} attempt(s): {last_error}"
        )


def _try_parse_draft(response: Any) -> tuple[ShipmentDraft | None, Exception | None]:
    """Parse a model response into a ShipmentDraft (schema-only validation).

    Same as ``_try_parse`` but over the draft schema, with the transcript
    guarantee enforced: whatever the model echoed, the produced draft's
    ``raw_transcript`` stays None.

    The model may answer a country as a free-form name ("United States",
    "अमेरिका") rather than the ISO2 the validation contract requires — it is
    normalized through ``_COUNTRY_ALIASES`` at this boundary so the merged
    draft never carries a value ``validate_shipment`` would reject.
    """
    try:
        text = _non_thinking_text(response)
        data = json.loads(_strip_code_fence(text)) if isinstance(text, str) else text
        if isinstance(data, dict):
            country = data.get("destination_country")
            if isinstance(country, str) and country not in ("unknown",):
                normalized = _COUNTRY_ALIASES.get(country.strip().lower())
                if normalized is not None:
                    data["destination_country"] = normalized
        draft = ShipmentDraft.model_validate(data)
        return draft.model_copy(update={"raw_transcript": None}), None
    except (ValidationError, ValueError) as exc:
        return None, exc


def _prior_draft_without_transcript(previous: ShipmentDraft | None) -> dict | None:
    """The prior draft as the model may see it — raw_transcript stripped."""
    if previous is None:
        return None
    return previous.model_dump(exclude={"raw_transcript"})


__all__ = [
    "CategoryUnknownError",
    "DraftExtractor",
    "Extractor",
    "GeminiDraftExtractor",
    "GeminiExtractor",
    "RuleDraftExtractor",
    "RuleExtractor",
    "draft_confidence",
]
