"""POST /api/extract — rule-first draft extraction endpoint (Wave 1).

Pins: rule extraction returns a draft with extractor="rule"; an unmappable
category is a 200 with category_unknown=true (never 4xx); a previous draft is
carried on the unknown-category turn.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.api.extract import _merge_filled
from app.schemas.shipment import ShipmentDraft

client = TestClient(app)


@pytest.fixture(autouse=True)
def _no_gemini_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Rule-path determinism: the repo .env now carries GEMINI_API_KEY (wired
    by Wave 1 T1), so without removing it the endpoint would build a real
    model and hit the network.  The merge tests call ``_merge_filled`` directly
    with a mock gemini draft; the live smoke test runs outside pytest with the
    key set."""
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)


def _draft(**overrides: object) -> ShipmentDraft:
    """A fully-known base draft; per-field overrides apply."""
    base: dict[str, object] = {
        "product_category": "small-woodware",
        "quantity": 1,
        "weight_grams": 400,
        "destination_country": "US",
        "consignee": "शिखा",
        "value_minor": 200000,
    }
    base.update(overrides)
    return ShipmentDraft(**base)


def test_merge_rule_value_wins_over_gemini() -> None:
    """A deterministic rule value is NEVER overwritten by Gemini."""
    rule = _draft(quantity=5)
    gemini = _draft(quantity=7)
    merged = _merge_filled(rule, gemini, None)
    assert merged.quantity == 5
    assert merged.weight_grams == 400


def test_merge_gemini_corrects_stored_field() -> None:
    """A sane Gemini value may correct/reaffirm a previously-stored field."""
    previous = _draft(weight_grams=500)
    rule = _draft(weight_grams=-1)
    confirmed = _merge_filled(rule, _draft(weight_grams=500), previous)
    assert confirmed.weight_grams == 500
    corrected = _merge_filled(rule, _draft(weight_grams=400), previous)
    assert corrected.weight_grams == 400


def test_merge_gemini_rejected_when_implausible() -> None:
    """An implausible Gemini value is never adopted — previous is kept."""
    previous = _draft(weight_grams=400)
    rule = _draft(weight_grams=-1)
    merged = _merge_filled(rule, _draft(weight_grams=1_000_000_000), previous)
    assert merged.weight_grams == 400


def test_merge_gap_fill_no_previous() -> None:
    """Gemini fills an unstated field when there is nothing stored yet."""
    rule = _draft(quantity=-1, weight_grams=-1)
    gemini = _draft(quantity=-1, weight_grams=400)
    merged = _merge_filled(rule, gemini, None)
    assert merged.weight_grams == 400
    assert merged.quantity == -1


def test_extract_rule_happy_path() -> None:
    response = client.post(
        "/api/extract",
        json={"text": "12 jute bags to Germany, 500 grams, 15000 rupees", "lang": "hi"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["category_unknown"] is False
    assert body["extractor"] == "rule"
    assert body["draft"]["product_category"] == "jute-products"
    assert body["draft"]["quantity"] == 12
    assert body["draft"]["weight_grams"] == 500
    assert body["draft"]["destination_country"] == "DE"
    assert body["draft"]["value_minor"] == 1500000


def test_extract_category_unknown_is_200() -> None:
    response = client.post(
        "/api/extract",
        json={"text": "five hundred grams", "lang": "hi"},
    )
    assert response.status_code == 200  # the chat must ask, never a 4xx
    body = response.json()
    assert body["category_unknown"] is True
    assert body["extractor"] == "rule"
    assert body["draft"]["product_category"] is None


def test_extract_category_unknown_keeps_previous() -> None:
    previous = {
        "product_category": "jute-products",
        "quantity": -1,
        "weight_grams": 500,
        "destination_country": "unknown",
        "consignee": "unknown",
        "value_minor": -1,
        "confidence": "low",
    }
    response = client.post(
        "/api/extract",
        json={"text": "to germany", "lang": "hi", "previous": previous},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["category_unknown"] is False  # carried forward — category known
    assert body["draft"]["product_category"] == "jute-products"
    assert body["draft"]["weight_grams"] == 500


def test_extract_gemini_resolves_category_when_rules_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The hardcoded rule gate must NOT block the model: when the rules cannot
    map the category but GEMINI_API_KEY is set, Gemini runs (with its
    search_categories tool) and may resolve the category from the catalog."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")
    resolved = _draft(product_category="block-printed-textiles", quantity=-1, weight_grams=-1)

    class _FakeGemini:
        def extract(self, transcript: str, previous: ShipmentDraft, lang: str) -> ShipmentDraft:
            assert "कपड़ा" in transcript, f"model must see the utterance: {transcript!r}"
            return resolved

    monkeypatch.setattr("app.api.extract.GeminiDraftExtractor", lambda: _FakeGemini())
    response = client.post(
        "/api/extract",
        json={"text": "मुझे कपड़ा भी यू एस पी ओ", "lang": "hi"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["category_unknown"] is False  # Gemini resolved it
    assert body["extractor"] == "gemini"
    assert body["draft"]["product_category"] == "block-printed-textiles"


def test_extract_gemini_still_ambiguous_asks_user(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """When Gemini also cannot decide, the chat must ask with candidates."""
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    class _FakeGemini:
        def extract(self, transcript: str, previous: ShipmentDraft, lang: str) -> ShipmentDraft:
            return _draft(product_category=None, quantity=-1, weight_grams=-1)

    monkeypatch.setattr("app.api.extract.GeminiDraftExtractor", lambda: _FakeGemini())
    response = client.post(
        "/api/extract",
        json={"text": "मुझे कपड़ा भी यू एस पी ओ", "lang": "hi"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["category_unknown"] is True
    assert body["draft"]["product_category"] is None
