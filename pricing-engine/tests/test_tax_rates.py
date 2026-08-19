from decimal import Decimal

import pytest

from app.tax_rates import (
    TaxRateLookupError,
    get_primary_tax_rate,
    lookup_tax_rates,
    normalize_country_code,
)


def test_country_code_is_normalized():

    assert normalize_country_code("us") == "US"
    assert normalize_country_code(" IN ") == "IN"


def test_invalid_country_length_is_rejected():

    with pytest.raises(
        TaxRateLookupError,
        match="exactly 2 letters",
    ):
        normalize_country_code("USA")


def test_empty_country_is_rejected():

    with pytest.raises(
        TaxRateLookupError,
    ):
        normalize_country_code("")


def test_non_string_country_is_rejected():

    with pytest.raises(
        TaxRateLookupError,
        match="must be a string",
    ):
        normalize_country_code(123)


def test_non_alpha_country_is_rejected():

    with pytest.raises(
        TaxRateLookupError,
        match="only letters",
    ):
        normalize_country_code("1A")


def test_lookup_known_country():

    result = lookup_tax_rates("in")

    assert result[
        "country_code"
    ] == "IN"

    assert result[
        "currency"
    ] == "INR"

    assert len(
        result["tax_components"]
    ) == 1


def test_unknown_country_is_rejected():

    with pytest.raises(
        TaxRateLookupError,
        match="No tax configuration found",
    ):
        lookup_tax_rates("ZZ")


def test_primary_rate():

    rate = get_primary_tax_rate("IN")

    assert rate == Decimal("18")


def test_primary_rate_for_zero_rate_country():

    rate = get_primary_tax_rate("US")

    assert rate == Decimal("0")


def test_lookup_returns_independent_copy():

    first = lookup_tax_rates("IN")

    first[
        "tax_components"
    ][0][
        "rate_percent"
    ] = Decimal("99")

    second = lookup_tax_rates("IN")

    assert second[
        "tax_components"
    ][0][
        "rate_percent"
    ] == Decimal("18")