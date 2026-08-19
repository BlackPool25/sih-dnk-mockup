import pytest

from app.fee_rates import (
    FeeRateLookupError,
    lookup_country_fees,
    normalize_country_code,
)


def test_normalize_country_code():

    assert normalize_country_code(
        "us"
    ) == "US"


def test_normalize_country_code_with_spaces():

    assert normalize_country_code(
        " IN "
    ) == "IN"


def test_non_string_country_code():

    with pytest.raises(
        FeeRateLookupError,
        match="must be a string",
    ):
        normalize_country_code(123)


def test_invalid_country_code_length():

    with pytest.raises(
        FeeRateLookupError,
        match="exactly 2 letters",
    ):
        normalize_country_code("USA")


def test_non_alpha_country_code():

    with pytest.raises(
        FeeRateLookupError,
        match="only letters",
    ):
        normalize_country_code("1A")


def test_known_country():

    result = lookup_country_fees("US")

    assert result[
        "country_code"
    ] == "US"

    assert result[
        "currency"
    ] == "USD"

    assert len(
        result["fees"]
    ) == 1


def test_unknown_country():

    with pytest.raises(
        FeeRateLookupError,
        match="No fee configuration found",
    ):
        lookup_country_fees("ZZ")


def test_lookup_returns_copy():

    first = lookup_country_fees("US")

    first[
        "fees"
    ][0][
        "fixed_minor"
    ] = 999999

    second = lookup_country_fees("US")

    assert second[
        "fees"
    ][0][
        "fixed_minor"
    ] == 250


def test_provenance():

    result = lookup_country_fees("US")

    assert result[
        "provenance"
    ]["source"] == (
        "engine-test-configuration"
    )