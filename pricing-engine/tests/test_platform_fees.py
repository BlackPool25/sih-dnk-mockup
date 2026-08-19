from decimal import Decimal

import pytest

from app.platform_fees import (
    PlatformFeeCalculationError,
    calculate_platform_fee,
)


def test_zero_platform_fee():

    result = calculate_platform_fee(
        fee_base_minor=10000,
        rate_percent=Decimal("0"),
    )

    assert result["percentage_fee_minor"] == 0
    assert result["fixed_fee_minor"] == 0
    assert result["total_fee_minor"] == 0


def test_percentage_platform_fee():

    result = calculate_platform_fee(
        fee_base_minor=10000,
        rate_percent=Decimal("5"),
    )

    assert result[
        "percentage_fee_minor"
    ] == 500

    assert result[
        "total_fee_minor"
    ] == 500


def test_fixed_platform_fee():

    result = calculate_platform_fee(
        fee_base_minor=10000,
        fixed_fee_minor=250,
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


def test_percentage_and_fixed_platform_fee():

    result = calculate_platform_fee(
        fee_base_minor=10000,
        rate_percent=Decimal("5"),
        fixed_fee_minor=250,
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


def test_decimal_platform_rate():

    result = calculate_platform_fee(
        fee_base_minor=10000,
        rate_percent=Decimal("2.5"),
    )

    assert result[
        "total_fee_minor"
    ] == 250


def test_negative_fee_base_is_rejected():

    with pytest.raises(
        PlatformFeeCalculationError,
        match="Platform fee base cannot be negative",
    ):
        calculate_platform_fee(
            fee_base_minor=-1,
        )


def test_negative_fixed_fee_is_rejected():

    with pytest.raises(
        PlatformFeeCalculationError,
        match="Platform fixed fee cannot be negative",
    ):
        calculate_platform_fee(
            fee_base_minor=10000,
            fixed_fee_minor=-1,
        )


def test_negative_rate_is_rejected():

    with pytest.raises(
        PlatformFeeCalculationError,
        match="Platform fee rate cannot be negative",
    ):
        calculate_platform_fee(
            fee_base_minor=10000,
            rate_percent=Decimal("-1"),
        )


def test_rate_above_100_is_rejected():

    with pytest.raises(
        PlatformFeeCalculationError,
        match="Platform fee rate cannot exceed 100 percent",
    ):
        calculate_platform_fee(
            fee_base_minor=10000,
            rate_percent=Decimal("101"),
        )


def test_empty_fee_type_is_rejected():

    with pytest.raises(
        PlatformFeeCalculationError,
        match="Platform fee type is required",
    ):
        calculate_platform_fee(
            fee_base_minor=10000,
            fee_type="",
        )


def test_empty_currency_is_rejected():

    with pytest.raises(
        PlatformFeeCalculationError,
        match="Currency is required",
    ):
        calculate_platform_fee(
            fee_base_minor=10000,
            currency="",
        )


def test_currency_is_normalized():

    result = calculate_platform_fee(
        fee_base_minor=10000,
        currency="inr",
    )

    assert result["currency"] == "INR"


def test_custom_fee_type():

    result = calculate_platform_fee(
        fee_base_minor=10000,
        rate_percent=Decimal("3"),
        fee_type="SERVICE_FEE",
    )

    assert result[
        "fee_type"
    ] == "SERVICE_FEE"


def test_provenance_is_preserved():

    provenance = {
        "source": "platform-config",
        "version": "1.0",
    }

    result = calculate_platform_fee(
        fee_base_minor=10000,
        rate_percent=Decimal("5"),
        provenance=provenance,
    )

    assert result[
        "provenance"
    ] == provenance