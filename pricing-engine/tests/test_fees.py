from decimal import Decimal

import pytest

from app.fees import (
    FeeCalculationError,
    calculate_country_fees,
    calculate_fee,
)


def test_zero_percent_fee():

    result = calculate_fee(
        fee_type="PROCESSING",
        base_minor=10000,
        rate_percent=Decimal("0"),
    )

    assert result[
        "percentage_fee_minor"
    ] == 0

    assert result[
        "total_fee_minor"
    ] == 0


def test_percentage_fee():

    result = calculate_fee(
        fee_type="PROCESSING",
        base_minor=10000,
        rate_percent=Decimal("5"),
    )

    assert result[
        "percentage_fee_minor"
    ] == 500

    assert result[
        "total_fee_minor"
    ] == 500


def test_fixed_fee():

    result = calculate_fee(
        fee_type="PROCESSING",
        base_minor=10000,
        fixed_minor=250,
    )

    assert result[
        "percentage_fee_minor"
    ] == 0

    assert result[
        "fixed_fee_minor"
    ] == 250

    assert result[
        "total_fee_minor"
    ] == 250


def test_percentage_plus_fixed_fee():

    result = calculate_fee(
        fee_type="PROCESSING",
        base_minor=10000,
        rate_percent=Decimal("5"),
        fixed_minor=250,
    )

    assert result[
        "percentage_fee_minor"
    ] == 500

    assert result[
        "fixed_fee_minor"
    ] == 250

    assert result[
        "total_fee_minor"
    ] == 750


def test_negative_base_is_rejected():

    with pytest.raises(
        FeeCalculationError,
        match="Fee base cannot be negative",
    ):
        calculate_fee(
            fee_type="PROCESSING",
            base_minor=-1,
        )


def test_negative_fixed_fee_is_rejected():

    with pytest.raises(
        FeeCalculationError,
        match="Fixed fee cannot be negative",
    ):
        calculate_fee(
            fee_type="PROCESSING",
            base_minor=10000,
            fixed_minor=-1,
        )


def test_negative_rate_is_rejected():

    with pytest.raises(
        FeeCalculationError,
        match="Fee rate cannot be negative",
    ):
        calculate_fee(
            fee_type="PROCESSING",
            base_minor=10000,
            rate_percent=Decimal("-1"),
        )


def test_rate_above_100_is_rejected():

    with pytest.raises(
        FeeCalculationError,
        match="Fee rate cannot exceed 100 percent",
    ):
        calculate_fee(
            fee_type="PROCESSING",
            base_minor=10000,
            rate_percent=Decimal("101"),
        )


def test_empty_fee_type_is_rejected():

    with pytest.raises(
        FeeCalculationError,
        match="Fee type is required",
    ):
        calculate_fee(
            fee_type="",
            base_minor=10000,
        )


def test_empty_currency_is_rejected():

    with pytest.raises(
        FeeCalculationError,
        match="Currency is required",
    ):
        calculate_fee(
            fee_type="PROCESSING",
            base_minor=10000,
            currency="",
        )


def test_country_with_no_components():

    result = calculate_country_fees(
        country_code="US",
        fee_components=[],
    )

    assert result[
        "total_fee_minor"
    ] == 0

    assert result[
        "components"
    ] == []


def test_multiple_country_fees():

    result = calculate_country_fees(
        country_code="US",
        fee_components=[
            {
                "fee_type": "PROCESSING",
                "base_minor": 10000,
                "rate_percent": Decimal("2"),
            },
            {
                "fee_type": "HANDLING",
                "base_minor": 10000,
                "fixed_minor": 300,
            },
        ],
        currency="USD",
    )

    assert len(
        result["components"]
    ) == 2

    assert result[
        "components"
    ][0]["total_fee_minor"] == 200

    assert result[
        "components"
    ][1]["total_fee_minor"] == 300

    assert result[
        "total_fee_minor"
    ] == 500


def test_country_code_is_normalized():

    result = calculate_country_fees(
        country_code="us",
        fee_components=[],
        currency="USD",
    )

    assert result[
        "country_code"
    ] == "US"


def test_invalid_country_code_is_rejected():

    with pytest.raises(
        FeeCalculationError,
        match="exactly 2 letters",
    ):
        calculate_country_fees(
            country_code="USA",
            fee_components=[],
        )


def test_missing_fee_type_is_rejected():

    with pytest.raises(
        FeeCalculationError,
        match="fee_type",
    ):
        calculate_country_fees(
            country_code="US",
            fee_components=[
                {
                    "base_minor": 10000,
                }
            ],
        )


def test_missing_fee_base_is_rejected():

    with pytest.raises(
        FeeCalculationError,
        match="base_minor",
    ):
        calculate_country_fees(
            country_code="US",
            fee_components=[
                {
                    "fee_type": "PROCESSING",
                }
            ],
        )


def test_provenance_is_preserved():

    provenance = {
        "source": "test",
        "version": "1",
    }

    result = calculate_fee(
        fee_type="PROCESSING",
        base_minor=10000,
        rate_percent=Decimal("5"),
        provenance=provenance,
    )

    assert result[
        "provenance"
    ] == provenance