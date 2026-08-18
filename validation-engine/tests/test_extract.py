"""Tests for the todo-10 extraction contract.

Covers:
- ``RuleExtractor`` happy path (en), Hindi path, failure path (sentinels,
  no crash), units, country aliases, unknown-category raise.
- ``GeminiExtractor`` with a MOCK client: the USER-REQUIREMENT proof that the
  model never receives the transcript, thinking blocks are dropped, and the
  re-prompt carries only the schema + prior Shipment (raw_transcript stripped).
- ``app.services.validate``: deterministic-only verification (ZZ / quantity=0
  rejected, sentinels accepted, ``missing_required`` list).
- ``Shipment`` schema: invalid category slug rejected.
"""

import json

import pytest
from pydantic import ValidationError

from app.schemas.shipment import Shipment
from app.services.extract import (
    CategoryUnknownError,
    GeminiExtractor,
    RuleExtractor,
)
from app.services.validate import validate_shipment

# ---------------------------------------------------------------------------
# RuleExtractor — happy path (en)
# ---------------------------------------------------------------------------


def test_rule_extract_en_happy() -> None:
    s = RuleExtractor().extract_from_text("eight cushion covers, four hundred grams, America", "en")
    assert s.quantity == 8
    assert s.weight_grams == 400
    assert s.destination_country == "US"
    assert s.product_category == "embroidered-home-textiles"
    assert s.confidence == "high"
    assert s.raw_transcript == "eight cushion covers, four hundred grams, America"


def test_rule_extract_digit_quantity() -> None:
    s = RuleExtractor().extract_from_text("12 jute bags, 2 kg, to Australia", "en")
    assert s.quantity == 12
    assert s.weight_grams == 2000  # kg -> grams
    assert s.destination_country == "AU"
    assert s.product_category == "jute-products"
    assert s.confidence == "high"


# ---------------------------------------------------------------------------
# RuleExtractor — Hindi
# ---------------------------------------------------------------------------


def test_rule_extract_hi_word_number() -> None:
    s = RuleExtractor().extract_from_text("मुझे छह कुशन कवर चाहिए", "hi")
    assert s.quantity == 6  # छह = six, Hindi word number
    assert s.product_category == "embroidered-home-textiles"  # कुशन -> cushion
    assert s.weight_grams == -1
    assert s.destination_country == "unknown"
    assert s.confidence == "low"


def test_rule_extract_hi_digit() -> None:
    s = RuleExtractor().extract_from_text("मुझे 6 कुशन कवर चाहिए", "hi")
    assert s.quantity == 6
    assert s.product_category == "embroidered-home-textiles"


# ---------------------------------------------------------------------------
# RuleExtractor — failure paths
# ---------------------------------------------------------------------------


def test_rule_extract_no_numbers_returns_sentinels() -> None:
    # No numbers -> sentinels + confidence low, and NO crash.
    s = RuleExtractor().extract_from_text("We make handloom scarves", "en")
    assert s.quantity == -1
    assert s.weight_grams == -1
    assert s.confidence == "low"
    assert s.product_category == "handloom-scarves-stoles"


def test_rule_extract_unknown_category_raises() -> None:
    # The rule engine never invents a category — the caller asks the user.
    with pytest.raises(CategoryUnknownError, match="ask the user"):
        RuleExtractor().extract_from_text("please send this parcel quickly", "en")


def test_rule_extract_country_aliases() -> None:
    assert (
        RuleExtractor().extract_from_text("send scarves to the UK", "en").destination_country
        == "GB"
    )
    assert (
        RuleExtractor().extract_from_text("send scarves to Dubai", "en").destination_country == "AE"
    )
    assert RuleExtractor().extract_from_text("jute to britain", "en").destination_country == "GB"
    assert (
        RuleExtractor().extract_from_text("brassware to america", "en").destination_country == "US"
    )


def test_rule_extract_medium_confidence_two_fields() -> None:
    # quantity + weight present, destination missing -> medium.
    s = RuleExtractor().extract_from_text("three brass diyas, one hundred grams", "en")
    assert s.quantity == 3
    assert s.weight_grams == 100
    assert s.destination_country == "unknown"
    assert s.confidence == "medium"


# ---------------------------------------------------------------------------
# Mocks for the GeminiExtractor tests (NEVER a real client / API / network).
# ---------------------------------------------------------------------------


class _MockPart:
    def __init__(self, text: str, thought: bool = False) -> None:
        self.text = text
        self.thought = thought


class _MockResponse:
    def __init__(self, parts: list[_MockPart]) -> None:
        self.parts = parts


class _MockClient:
    """Records every call; returns queued responses in order."""

    def __init__(self, responses: list[_MockResponse]) -> None:
        self.responses = list(responses)
        self.calls: list[tuple[dict, list[dict]]] = []

    def generate_content(self, config: dict, contents: list[dict]) -> _MockResponse:
        self.calls.append((config, contents))
        return self.responses.pop(0)


_VALID_PAYLOAD = {
    "product_category": "jute-products",
    "quantity": 5,
    "weight_grams": -1,
    "destination_country": "unknown",
    "confidence": "low",
}

_SCHEMA_INVALID_PAYLOAD = {
    "product_category": "not-a-real-slug",  # fails the Literal -> reprompt
    "quantity": 3,
    "weight_grams": 200,
    "destination_country": "IN",
    "confidence": "medium",
}


def test_gemini_extractor_never_receives_transcript() -> None:
    """USER-REQUIREMENT: the mock's recorded args contain NO transcript text,
    only the response_schema (+ prior Shipment), and a thinking block is
    dropped — never persisted as a fact."""
    client = _MockClient(
        [
            _MockResponse(
                [
                    _MockPart("internal chain of thought about the user", thought=True),
                    _MockPart(json.dumps(_VALID_PAYLOAD)),
                ]
            ),
        ]
    )
    prior = Shipment(
        product_category="embroidered-home-textiles",
        quantity=8,
        weight_grams=400,
        destination_country="US",
        confidence="high",
        raw_transcript="eight cushion covers, four hundred grams, America",
    )

    s = GeminiExtractor(client).extract(previous=prior, lang="en")

    # The parsed Shipment comes from the non-thinking part.
    assert s.quantity == 5
    assert s.product_category == "jute-products"
    assert s.raw_transcript is None  # the LLM never had the transcript

    assert len(client.calls) == 1
    config, contents = client.calls[0]
    assert config["response_schema"] == Shipment.model_json_schema()
    assert config["thinking_config"] == {"thinking_budget": 0}

    blob = json.dumps({"config": config, "contents": contents}, ensure_ascii=False)
    assert "eight cushion covers" not in blob
    assert "four hundred grams" not in blob
    assert "America" not in blob
    assert "internal chain of thought" not in blob  # thinking dropped, not a fact


def test_gemini_extractor_reprompt_excludes_transcript() -> None:
    """On a schema ValidationError the extractor re-prompts with ONLY the
    schema + prior Shipment object — never the transcript; raw_transcript is
    stripped from the object handed back to the model."""
    client = _MockClient(
        [
            _MockResponse([_MockPart(json.dumps(_SCHEMA_INVALID_PAYLOAD))]),
            _MockResponse([_MockPart(json.dumps(_VALID_PAYLOAD))]),
        ]
    )
    prior = Shipment(
        product_category="embroidered-home-textiles",
        quantity=8,
        weight_grams=400,
        destination_country="US",
        confidence="high",
        raw_transcript="SECRET TRANSCRIPT: eight cushion covers, four hundred grams",
    )

    s = GeminiExtractor(client).extract(previous=prior, lang="en")

    assert s.quantity == 5
    assert len(client.calls) == 2  # first was schema-invalid -> reprompt

    for config, contents in client.calls:
        assert config["response_schema"] == Shipment.model_json_schema()
        assert config["thinking_config"] == {"thinking_budget": 0}
        blob = json.dumps({"config": config, "contents": contents}, ensure_ascii=False)
        assert "SECRET TRANSCRIPT" not in blob
        assert "eight cushion covers" not in blob
        assert "four hundred grams" not in blob

    # The prior Shipment handed to the model on the re-prompt excludes the
    # transcript field entirely.
    re_prompt_contents = client.calls[1][1]
    prior_sent = re_prompt_contents[1]["prior_shipment"]
    assert prior_sent["product_category"] == "embroidered-home-textiles"
    assert prior_sent["quantity"] == 8
    assert "raw_transcript" not in prior_sent


# ---------------------------------------------------------------------------
# app.services.validate — deterministic-only verification (never the LLM)
# ---------------------------------------------------------------------------


def test_validate_rejects_non_real_iso2() -> None:
    # "ZZ" matches ^[A-Z]{2}$ but is not a real country — rejected.
    s = Shipment(
        product_category="jute-products",
        quantity=2,
        weight_grams=100,
        destination_country="ZZ",
        confidence="high",
    )
    with pytest.raises(ValidationError):
        validate_shipment(s)


def test_validate_rejects_quantity_zero() -> None:
    s = Shipment(
        product_category="jute-products",
        quantity=0,
        weight_grams=100,
        destination_country="IN",
        confidence="high",
    )
    with pytest.raises(ValidationError):
        validate_shipment(s)


def test_validate_rejects_out_of_range_weight() -> None:
    s = Shipment(
        product_category="jute-products",
        quantity=2,
        weight_grams=60_000,  # above 50_000
        destination_country="IN",
        confidence="high",
    )
    with pytest.raises(ValidationError):
        validate_shipment(s)


def test_validate_accepts_sentinels() -> None:
    # A partial Shipment is legal — the caller asks the user via missing_required.
    s = Shipment(
        product_category="jute-products",
        quantity=-1,
        weight_grams=-1,
        destination_country="unknown",
        confidence="low",
    )
    assert validate_shipment(s) is s


def test_validate_accepts_valid_shipment() -> None:
    s = Shipment(
        product_category="jute-products",
        quantity=2,
        weight_grams=100,
        destination_country="IN",
        confidence="high",
    )
    assert validate_shipment(s) is s


# ---------------------------------------------------------------------------
# Shipment schema
# ---------------------------------------------------------------------------


def test_shipment_rejects_unknown_category() -> None:
    with pytest.raises(ValidationError):
        Shipment(
            product_category="not-a-category",
            quantity=1,
            weight_grams=100,
            destination_country="US",
            confidence="high",
        )
