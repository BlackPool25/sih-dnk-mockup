from decimal import Decimal

import pytest

from app.preferential_rates import (
    PreferentialRateLookupError,
    lookup_preferential_rate,
    normalize_code,
)


def test_normalize_country_code():

    assert normalize_code(
        "in",
        "origin_country",
    ) == "IN"


def test_normalize_category():

    assert normalize_code(
        " jute-products ",
        "category_slug",
    ) == "JUTE-PRODUCTS"


def test_empty_code_is_rejected():

    with pytest.raises(
        PreferentialRateLookupError,
        match="cannot be empty",
    ):
        normalize_code(
            "",
            "origin_country",
        )


def test_non_string_code_is_rejected():

    with pytest.raises(
        PreferentialRateLookupError,
        match="must be a string",
    ):
        normalize_code(
            123,
            "origin_country",
        )


def test_matching_preferential_rule():

    result = lookup_preferential_rate(
        origin_country="IN",
        destination_country="US",
        category_slug="jute-products",
    )

    assert result["eligible"] is True

    assert (
        result["rate_percent"]
        == Decimal("5")
    )

    assert (
        result["agreement"]
        == "TEST-PREFERENTIAL-AGREEMENT"
    )

    assert (
        "ORIGIN_REQUIREMENT"
        in result["conditions"]
    )


def test_unknown_rule_returns_ineligible():

    result = lookup_preferential_rate(
        origin_country="IN",
        destination_country="GB",
        category_slug="jute-products",
    )

    assert result["eligible"] is False

    assert result["rate_percent"] is None

    assert result["agreement"] is None

    assert result["conditions"] == []


def test_lookup_is_case_insensitive():

    result = lookup_preferential_rate(
        origin_country="in",
        destination_country="us",
        category_slug="JUTE-PRODUCTS",
    )

    assert result["eligible"] is True


def test_provenance_is_returned():

    result = lookup_preferential_rate(
        origin_country="IN",
        destination_country="US",
        category_slug="JUTE-PRODUCTS",
    )

    assert (
        result["provenance"]["source"]
        == "engine-test-configuration"
    )