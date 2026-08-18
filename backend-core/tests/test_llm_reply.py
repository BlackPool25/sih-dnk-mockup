"""llm_reply — template replies, echo lines, options, Gemini enrichment.

Pins: echo only from known fields (sentinels excluded), Hindi templates render
with the right keys, options list caps at 5, and GeminiEnricher never mutates
figures and degrades to the template when no key or on failure.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from app.services.enricher import GeminiEnricher
from app.services.llm_reply import (
    FIELD_ORDER,
    ask_line,
    ask_line_variants,
    echo_line,
    options_line,
)

DRAFT_FULL = {
    "product_category": "jute-products",
    "quantity": 12,
    "weight_grams": 500,
    "destination_country": "DE",
    "consignee": "unknown",
    "value_minor": 1500000,
}
DB_INFO = {"category_name": "Jute Products"}


def test_field_order_category_first() -> None:
    assert FIELD_ORDER[0] == "product_category"
    assert set(FIELD_ORDER) == {
        "product_category",
        "destination_country",
        "quantity",
        "weight_grams",
        "value_minor",
        "consignee",
    }


def test_echo_line_hi_includes_only_known_fields() -> None:
    line = echo_line("hi", DRAFT_FULL, DB_INFO)
    assert line.startswith("मैंने समझा")
    assert "Jute Products" in line
    assert "12" in line
    assert "500" in line
    assert "जर्मनी" in line
    assert "1500000" in line  # raw minor — display formatting is a UI concern
    assert "unknown" not in line  # consignee sentinel excluded


def test_echo_line_empty_when_nothing_known() -> None:
    assert echo_line("hi", {}) == ""


def test_echo_line_en() -> None:
    line = echo_line("en", DRAFT_FULL, DB_INFO)
    assert "category Jute Products" in line
    assert "Germany" in line or "DE" in line  # DE maps to जर्मनी; en fallback shows raw


def test_ask_line_happy_and_fallback() -> None:
    assert "किस देश" in ask_line("hi", "destination_country")
    assert "किस उत्पाद" in ask_line("hi", "product_category")
    assert "माफ़" in ask_line("hi", "no_such_field")


def test_options_line_caps_at_five() -> None:
    candidates = [{"name": f"Cat {i}"} for i in range(9)]
    line = options_line("hi", candidates)
    assert "1) Cat 0" in line
    assert "5) Cat 4" in line
    assert "Cat 5" not in line
    assert "कृपया चुनें" in line


def test_enricher_returns_template_without_key(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    enricher = GeminiEnricher(api_key=None)
    assert enricher.enrich("hi", "नमस्ते", DRAFT_FULL, DB_INFO) == "नमस्ते"


def test_enricher_uses_key_and_preserves_figures() -> None:
    fake_model = MagicMock()
    fake_model.generate_content.return_value = MagicMock(
        text="हाँ, समझ गया — 12 टुकड़े, 500 ग्राम, जर्मनी। किस देश में भेजना है?"
    )
    enricher = GeminiEnricher(api_key="test-key")
    enricher._model = fake_model  # bypass real client construction

    out = enricher.enrich("hi", "मैंने समझा — 12 टुकड़े, 500 ग्राम, जर्मनी।", DRAFT_FULL, DB_INFO)
    assert out.startswith("हाँ")
    assert "12" in out and "500" in out and "जर्मनी" in out


def test_enricher_falls_back_on_call_failure() -> None:
    fake_model = MagicMock()
    fake_model.generate_content.side_effect = RuntimeError("boom")
    enricher = GeminiEnricher(api_key="test-key")
    enricher._model = fake_model

    template = "मैंने समझा — 12 टुकड़े।"
    assert enricher.enrich("hi", template, DRAFT_FULL, DB_INFO) == template


def test_enrich_asks_one_question_about_next_field() -> None:
    fake_model = MagicMock()
    fake_model.generate_content.return_value = MagicMock(
        text="अच्छा समझ गया! अब बताइए, किस देश में भेजना है?"
    )
    enricher = GeminiEnricher(api_key="test-key")
    enricher._model = fake_model

    out = enricher.enrich(
        "hi",
        "मैंने समझा — श्रेणी Small Woodware, मात्रा 1। किस देश में भेजना है?",
        {"product_category": "small-woodware", "quantity": 1},
        {"category_name": "Small Woodware"},
        next_field="destination_country",
    )
    prompt = fake_model.generate_content.call_args.args[0]
    assert "destination_country" in prompt
    assert "exactly one question" in prompt.lower()
    assert "never" in prompt.lower()  # anti-hallucination rule present
    assert out == "अच्छा समझ गया! अब बताइए, किस देश में भेजना है?"


def test_enrich_preserves_figures_exactly() -> None:
    draft = {
        "product_category": "small-woodware",
        "quantity": 1,
        "weight_grams": 400,
        "value_minor": 200000,
        "destination_country": "US",
        "consignee": "unknown",
    }
    fake_model = MagicMock()
    fake_model.generate_content.return_value = MagicMock(
        text="ठीक है! लकड़ी का सामान, 1 टुकड़ा, 400 ग्राम, कीमत 200000 रुपये। किस देश में भेजना है?"
    )
    enricher = GeminiEnricher(api_key="test-key")
    enricher._model = fake_model

    out = enricher.enrich(
        "hi", "मैंने समझा।", draft, {"category_name": "Small Woodware"},
        next_field="destination_country",
    )
    prompt = fake_model.generate_content.call_args.args[0]
    for digit in ("1", "400", "200000"):
        assert digit in prompt  # the model sees the input figures verbatim
    for digit in ("1", "400", "200000"):
        assert digit in out  # the model's echo passes through untouched


def test_enrich_falls_back_to_template_without_key(monkeypatch) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    enricher = GeminiEnricher(api_key=None)
    template = "मैंने समझा — 1 टुकड़ा।"
    assert (
        enricher.enrich("hi", template, {"quantity": 1}, {}, next_field="destination_country")
        == template
    )


def test_enrich_varied_phrasing_two_calls_differ() -> None:
    fake_model = MagicMock()
    fake_model.generate_content.side_effect = [
        MagicMock(text="किस देश में भेजेंगे?"),
        MagicMock(text="अब बताइए, कहाँ भेजना है?"),
    ]
    enricher = GeminiEnricher(api_key="test-key")
    enricher._model = fake_model
    kwargs = dict(
        lang="hi",
        template_text="मैंने समझा।",
        draft={"quantity": 1},
        db_info={},
        next_field="destination_country",
    )
    first = enricher.enrich(**kwargs)
    second = enricher.enrich(**kwargs)
    prompt = fake_model.generate_content.call_args.args[0]
    assert "varied" in prompt.lower() or "natural" in prompt.lower()
    assert fake_model.generate_content.call_count == 2
    assert first != second


def test_ask_line_variants_rotate() -> None:
    """Two different history lengths yield two different phrasings; the
    rotation wraps around the variant count and falls back to ask_line."""
    first = ask_line_variants("hi", "quantity", 0)
    second = ask_line_variants("hi", "quantity", 1)
    assert first != second
    assert ask_line_variants("hi", "quantity", 2) == first
    # product_category reuses the plain category ask (no variants defined)
    assert ask_line_variants("hi", "product_category", 0) == ask_line("hi", "product_category")


def test_ask_line_variants_all_in_set() -> None:
    """Every field/language resolves to a declared variant or the fallback,
    and every declared variant is a non-empty string."""
    from app.services.llm_reply import ASK_VARIANTS, _ASK_VARIANTS_EN

    for lang, variants in (("hi", ASK_VARIANTS), ("en", _ASK_VARIANTS_EN)):
        assert len(variants) == len(FIELD_ORDER) - 1
        for field, options in variants.items():
            assert field in FIELD_ORDER
            assert isinstance(options, tuple) and len(options) >= 2
            assert all(isinstance(o, str) and o.strip() for o in options)
        for field in FIELD_ORDER:
            out = ask_line_variants(lang, field, 0)
            allowed = variants.get(field, ()) + (ask_line(lang, field),)
            assert out in allowed
            assert out


def test_is_filler_phrases_and_discourse() -> None:
    """The curated filler set plus multi-word discourse turns are filler."""
    from app.services.llm_reply import is_filler

    for phrase in (
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
        "अरे भाई अच्छी बात हुई",  # the acceptance-contract utterance
    ):
        assert is_filler(phrase), phrase


def test_is_filler_rejects_extractable_content() -> None:
    """Filler must not swallow real data: a polite prefix + a country/measure
    is a data turn, and 'बस यही है' (a confirmation) is not flagged."""
    from app.services.llm_reply import is_filler

    assert is_filler("हाँ अमेरिका") is False
    assert is_filler("500 ग्राम") is False
    assert is_filler("अरे भाई, 12 जूट बैग") is False
    assert is_filler("बस यही है") is False


def test_is_filler_normalizes_punctuation_and_case() -> None:
    from app.services.llm_reply import is_filler

    assert is_filler("अरे भाई!") is True
    assert is_filler("  OK  ") is True
    assert is_filler("Theek") is True
    assert is_filler("") is False
    assert is_filler("   ") is False
