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
import re
from typing import Any, Protocol

from pydantic import ValidationError

from app.schemas.shipment import (
    CATEGORY_SLUGS,
    DESTINATION_UNSTATED,
    QUANTITY_UNSTATED,
    WEIGHT_UNSTATED,
    Shipment,
)


class Extractor(Protocol):
    """Model-facing extraction contract.

    ``extract`` deliberately takes NO transcript argument: the model is given
    ONLY the prior Shipment object (optionally) and a language tag.
    """

    def extract(self, previous: Shipment | None, lang: str) -> Shipment: ...


class CategoryUnknownError(ValueError):
    """Raised by ``RuleExtractor`` when no category keyword matches the text.

    The rule engine does not invent a category — the caller catches this and
    asks the user which of the 8 seeded categories applies.
    """


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
}

# A token is a run of word characters (letters/digits, incl. Devanagari +
# Kannada) — enough for both English and the Indic scripts.
_TOKEN_RE = re.compile(r"\w+", re.UNICODE)


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
        "ಕೈಚೀಲ",
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
    # America / USA
    "united states of america": "US",
    "united states": "US",
    "america": "US",
    "usa": "US",
    "अमेरिका": "US",
    "ಅಮೆರಿಕಾ": "US",
    # United Kingdom / Britain
    "united kingdom": "GB",
    "britain": "GB",
    "uk": "GB",
    "england": "GB",
    "ब्रिटेन": "GB",
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
}


def _match_country(text: str) -> str:
    """First matching country alias -> ISO2, else the ``unknown`` sentinel."""
    for alias in sorted(_COUNTRY_ALIASES, key=len, reverse=True):
        if alias in text:
            return _COUNTRY_ALIASES[alias]
    return DESTINATION_UNSTATED


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


def _extract_quantity(
    tokens: list[tuple[str, int, int]], exclude: set[int]
) -> int | None:
    """First number run not consumed by the weight match -> value, or None."""
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


__all__ = [
    "CategoryUnknownError",
    "Extractor",
    "GeminiExtractor",
    "RuleExtractor",
]
