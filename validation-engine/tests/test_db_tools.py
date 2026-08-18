"""Tests for ``app.services.db_tools`` — the read-only DB tool surface.

These hit the LIVE seeded DB (no fixtures — the container must be up).
Each test pins either a happy path, a row cap, or a negative behaviour
from the todo-9 spec.
"""

import pytest

from app.services.db_tools import (
    get_config_flag,
    get_state_sales_tax,
    lookup_duty,
    lookup_hs_codes,
    quote_lane,
    search_categories,
)

# --- search_categories ------------------------------------------------------


def test_search_categories_finds_by_slug() -> None:
    rows = search_categories("brass")
    slugs = {r["slug"] for r in rows}
    assert "small-brass-metalware" in slugs
    for row in rows:
        assert row["source_url"]
        assert row["confidence"]
        assert "is_estimate" in row


def test_search_categories_finds_by_name() -> None:
    rows = search_categories("Jewellery")
    assert any("jewellery" in r["slug"] for r in rows)


def test_search_categories_row_cap() -> None:
    """A query matching every row must still return <= 5."""
    rows = search_categories("")
    assert len(rows) <= 5


def test_search_categories_unknown_query_empty() -> None:
    assert search_categories("zzzz-no-such-category") == []


def test_search_categories_hindi_keyword_finds_category() -> None:
    """Spoken Hindi product words must resolve through the keyword index —
    this is what lets the Gemini tool-calling path answer 'मुझे कपड़ा भी
    यू एस पी ओ' instead of the hardcoded rule gate blocking the model."""
    rows = search_categories("कपड़ा")
    slugs = {r["slug"] for r in rows}
    # कपड़ा (cloth) is ambiguous — it must surface the textile family so the
    # model can pick the best match or ask the user.
    assert "block-printed-textiles" in slugs
    assert "handloom-scarves-stoles" in slugs
    for row in rows:
        assert row["source_url"]


def test_search_categories_hindi_keyword_jute() -> None:
    rows = search_categories("जूट")
    assert any(r["slug"] == "jute-products" for r in rows)


def test_search_categories_garment_words_find_textiles() -> None:
    """Garment words users actually say ('शर्ट' shirt, 'शॉर्ट्स' shorts) must
    surface the textile family so the model can decide or ask."""
    for word in ("शर्ट", "शॉर्ट्स", "shirt", "shorts"):
        slugs = {r["slug"] for r in search_categories(word)}
        assert "block-printed-textiles" in slugs, f"{word} -> {slugs}"


def test_search_categories_short_is_textile_family() -> None:
    """'शॉर्ट' (STT for shorts) must resolve — the user's real utterance
    'शॉर्ट पिंक्स नया यूएस' depends on this."""
    slugs = {r["slug"] for r in search_categories("शॉर्ट")}
    assert "block-printed-textiles" in slugs


# --- lookup_hs_codes --------------------------------------------------------


def test_lookup_hs_codes_by_category() -> None:
    rows = lookup_hs_codes(category="block-printed-textiles")
    assert len(rows) >= 1
    for row in rows:
        assert row["category_slug"] == "block-printed-textiles"
        assert row["source_url"]
        assert row["confidence"]


def test_lookup_hs_codes_by_hs6() -> None:
    rows = lookup_hs_codes(hs6="5208")
    assert len(rows) >= 1
    assert all(r["hs6"] == "5208" for r in rows)


def test_lookup_hs_codes_by_category_and_hs6() -> None:
    rows = lookup_hs_codes(category="block-printed-textiles", hs6="5208")
    assert len(rows) >= 1
    assert all(r["category_slug"] == "block-printed-textiles" for r in rows)


def test_lookup_hs_codes_row_cap() -> None:
    """No filters -> the whole table (99 rows) must still return <= 10."""
    rows = lookup_hs_codes()
    assert 1 <= len(rows) <= 10


def test_lookup_hs_codes_unknown_scopes_empty() -> None:
    assert lookup_hs_codes(category="zz-no-such-cat") == []
    assert lookup_hs_codes(hs6="999999") == []


# --- lookup_duty ------------------------------------------------------------


def test_lookup_duty_market() -> None:
    rows = lookup_duty("US")
    assert len(rows) >= 1
    for row in rows:
        assert row["country_iso2"] == "US"
        assert row["rate_type"]
        assert "rate_pct" in row
        assert "basis" in row
        assert row["source_url"]
        assert row["confidence"]
        assert "is_estimate" in row


def test_lookup_duty_by_hs6() -> None:
    rows = lookup_duty("US", hs6="520852")
    assert len(rows) >= 1
    assert all(r["hs6"] == "520852" for r in rows)


def test_lookup_duty_row_cap() -> None:
    """AE/AU/GB each have 24 rate rows -> must come back capped at 20."""
    for iso2 in ("AE", "AU", "GB"):
        rows = lookup_duty(iso2)
        assert 1 <= len(rows) <= 20, iso2


def test_lookup_duty_unknown_country_returns_empty() -> None:
    """Pinned: [] for a never-seen country — NOT an exception."""
    assert lookup_duty("ZZ") == []


# --- quote_lane -------------------------------------------------------------


def test_quote_lane_us_100g_slab_math() -> None:
    """US ITPS: 40000 + ceil((100-50)/50)*3500 = 43500."""
    result = quote_lane("US", 100)
    assert result["cost_minor"] == 43500
    assert result["weight_cap_g"] == 5000
    assert result["volume_free"] is True
    assert result["transit_min_days"] == 18
    assert result["transit_max_days"] == 28
    assert result["source_url"]
    assert result["confidence"]
    assert "is_estimate" in result


def test_quote_lane_below_first_slab_charges_first_slab() -> None:
    assert quote_lane("US", 10)["cost_minor"] == 40000
    assert quote_lane("US", 50)["cost_minor"] == 40000


def test_quote_lane_default_lane_is_itps() -> None:
    assert quote_lane("US", 100)["cost_minor"] == quote_lane("US", 100, "ITPS")["cost_minor"]


def test_quote_lane_over_cap_raises_value_error() -> None:
    with pytest.raises(ValueError, match="cap"):
        quote_lane("US", 6000)


def test_quote_lane_unknown_country_raises_lookup_error() -> None:
    with pytest.raises(LookupError):
        quote_lane("ZZ", 100)


def test_quote_lane_unknown_lane_raises_lookup_error() -> None:
    with pytest.raises(LookupError):
        quote_lane("US", 100, lane="NOSUCH")


# --- get_state_sales_tax ----------------------------------------------------


def test_get_state_sales_tax_california() -> None:
    result = get_state_sales_tax("CA")
    assert result["state_iso2"] == "CA"
    assert result["state_rate_pct"] == 7.25
    assert result["state_name"]
    assert result["source_url"]
    assert result["confidence"]


def test_get_state_sales_tax_unknown_raises_key_error() -> None:
    with pytest.raises(KeyError):
        get_state_sales_tax("ZZ")


# --- get_config_flag --------------------------------------------------------


def test_get_config_flag_scalar_value() -> None:
    result = get_config_flag("us.s301.rate_pct")
    assert result["flag_value"] == 10
    assert result["source_url"]
    assert result["confidence"]
    assert "is_estimate" in result


def test_get_config_flag_unknown_raises_key_error() -> None:
    with pytest.raises(KeyError):
        get_config_flag("nope")
