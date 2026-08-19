from decimal import Decimal

import pytest

from app.duty import (
    DutyCalculationError,
    calculate_duty,
    calculate_duty_from_value,
)


def test_zero_duty():

    result = calculate_duty(
        customs_value_minor=10000,
        duty_rate_percent=Decimal("0"),
    )

    assert result["customs_value_minor"] == 10000
    assert result["duty_rate_percent"] == Decimal("0")
    assert result["duty_minor"] == 0
    assert result["currency"] == "INR"
    assert result["basis"] == "CIF"


def test_ten_percent_duty():

    result = calculate_duty(
        customs_value_minor=10000,
        duty_rate_percent=Decimal("10"),
    )

    assert result["customs_value_minor"] == 10000
    assert result["duty_rate_percent"] == Decimal("10")
    assert result["duty_minor"] == 1000


def test_twenty_five_percent_duty():

    result = calculate_duty(
        customs_value_minor=10000,
        duty_rate_percent=Decimal("25"),
    )

    assert result["duty_minor"] == 2500


def test_decimal_duty_rate():

    result = calculate_duty(
        customs_value_minor=10000,
        duty_rate_percent=Decimal("7.5"),
    )

    assert result["duty_minor"] == 750


def test_duty_rounding():

    result = calculate_duty(
        customs_value_minor=10001,
        duty_rate_percent=Decimal("10"),
    )

    assert result["duty_minor"] == 1000


def test_negative_customs_value_is_rejected():

    with pytest.raises(
        DutyCalculationError,
        match="Customs value cannot be negative",
    ):
        calculate_duty(
            customs_value_minor=-1,
            duty_rate_percent=Decimal("10"),
        )


def test_negative_duty_rate_is_rejected():

    with pytest.raises(
        DutyCalculationError,
        match="Duty rate cannot be negative",
    ):
        calculate_duty(
            customs_value_minor=10000,
            duty_rate_percent=Decimal("-1"),
        )


def test_duty_rate_above_100_is_rejected():

    with pytest.raises(
        DutyCalculationError,
        match="Duty rate cannot exceed 100 percent",
    ):
        calculate_duty(
            customs_value_minor=10000,
            duty_rate_percent=Decimal("100.1"),
        )


def test_missing_currency_is_rejected():

    with pytest.raises(
        DutyCalculationError,
        match="Currency is required",
    ):
        calculate_duty(
            customs_value_minor=10000,
            duty_rate_percent=Decimal("10"),
            currency="",
        )


def test_missing_basis_is_rejected():

    with pytest.raises(
        DutyCalculationError,
        match="Duty basis is required",
    ):
        calculate_duty(
            customs_value_minor=10000,
            duty_rate_percent=Decimal("10"),
            basis="",
        )


def test_currency_is_normalized():

    result = calculate_duty(
        customs_value_minor=10000,
        duty_rate_percent=Decimal("10"),
        currency="inr",
    )

    assert result["currency"] == "INR"


def test_provenance_is_preserved():

    provenance = {
        "source": "test",
        "version": "1",
    }

    result = calculate_duty(
        customs_value_minor=10000,
        duty_rate_percent=Decimal("10"),
        provenance=provenance,
    )

    assert result["provenance"] == provenance


def test_preferential_rate_is_used():

    result = calculate_duty_from_value(
        customs_value_minor=10000,
        duty_rate_percent=Decimal("10"),
        preferential_rate_percent=Decimal("5"),
    )

    assert result["standard_duty_rate_percent"] == Decimal("10")

    assert (
        result["preferential_duty_rate_percent"]
        == Decimal("5")
    )

    assert result["duty_rate_percent"] == Decimal("5")

    assert result["duty_minor"] == 500

    assert result["rate_type"] == "PREFERENTIAL"


def test_standard_rate_is_used_without_preference():

    result = calculate_duty_from_value(
        customs_value_minor=10000,
        duty_rate_percent=Decimal("10"),
    )

    assert result["duty_rate_percent"] == Decimal("10")

    assert result["duty_minor"] == 1000

    assert result["rate_type"] == "STANDARD"


def test_preferential_rate_cannot_exceed_standard_rate():

    with pytest.raises(
        DutyCalculationError,
        match=(
            "Preferential duty rate cannot be greater"
        ),
    ):
        calculate_duty_from_value(
            customs_value_minor=10000,
            duty_rate_percent=Decimal("5"),
            preferential_rate_percent=Decimal("10"),
        )