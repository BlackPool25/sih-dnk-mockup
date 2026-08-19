from decimal import Decimal

import pytest

from app.tax import (
    TaxCalculationError,
    calculate_import_tax,
    calculate_multiple_taxes,
    calculate_tax,
)


def test_zero_tax():

    result = calculate_tax(
        tax_base_minor=10000,
        tax_rate_percent=Decimal("0"),
    )

    assert result["tax_base_minor"] == 10000
    assert result["tax_rate_percent"] == Decimal("0")
    assert result["tax_minor"] == 0
    assert result["tax_type"] == "IMPORT_TAX"
    assert result["currency"] == "INR"


def test_ten_percent_tax():

    result = calculate_tax(
        tax_base_minor=10000,
        tax_rate_percent=Decimal("10"),
    )

    assert result["tax_minor"] == 1000


def test_eighteen_percent_tax():

    result = calculate_tax(
        tax_base_minor=10000,
        tax_rate_percent=Decimal("18"),
    )

    assert result["tax_minor"] == 1800


def test_decimal_tax_rate():

    result = calculate_tax(
        tax_base_minor=10000,
        tax_rate_percent=Decimal("7.5"),
    )

    assert result["tax_minor"] == 750


def test_tax_rounding():

    result = calculate_tax(
        tax_base_minor=10001,
        tax_rate_percent=Decimal("10"),
    )

    assert result["tax_minor"] == 1000


def test_negative_tax_base_is_rejected():

    with pytest.raises(
        TaxCalculationError,
        match="Tax base cannot be negative",
    ):
        calculate_tax(
            tax_base_minor=-1,
            tax_rate_percent=Decimal("10"),
        )


def test_negative_tax_rate_is_rejected():

    with pytest.raises(
        TaxCalculationError,
        match="Tax rate cannot be negative",
    ):
        calculate_tax(
            tax_base_minor=10000,
            tax_rate_percent=Decimal("-1"),
        )


def test_tax_rate_above_100_is_rejected():

    with pytest.raises(
        TaxCalculationError,
        match="Tax rate cannot exceed 100 percent",
    ):
        calculate_tax(
            tax_base_minor=10000,
            tax_rate_percent=Decimal("100.1"),
        )


def test_empty_tax_type_is_rejected():

    with pytest.raises(
        TaxCalculationError,
        match="Tax type is required",
    ):
        calculate_tax(
            tax_base_minor=10000,
            tax_rate_percent=Decimal("10"),
            tax_type="",
        )


def test_empty_currency_is_rejected():

    with pytest.raises(
        TaxCalculationError,
        match="Currency is required",
    ):
        calculate_tax(
            tax_base_minor=10000,
            tax_rate_percent=Decimal("10"),
            currency="",
        )


def test_destination_country_is_normalized():

    result = calculate_tax(
        tax_base_minor=10000,
        tax_rate_percent=Decimal("10"),
        destination_country="us",
    )

    assert result[
        "destination_country"
    ] == "US"


def test_import_tax_includes_duty():

    result = calculate_import_tax(
        customs_value_minor=10000,
        duty_minor=1000,
        tax_rate_percent=Decimal("10"),
    )

    # Tax base = 10,000 + 1,000
    # Tax = 11,000 × 10%
    assert result[
        "tax_base_minor"
    ] == 11000

    assert result[
        "tax_minor"
    ] == 1100


def test_import_tax_excludes_duty():

    result = calculate_import_tax(
        customs_value_minor=10000,
        duty_minor=1000,
        tax_rate_percent=Decimal("10"),
        include_duty_in_tax_base=False,
    )

    # Tax base = 10,000
    assert result[
        "tax_base_minor"
    ] == 10000

    assert result[
        "tax_minor"
    ] == 1000


def test_import_tax_with_additional_base():

    result = calculate_import_tax(
        customs_value_minor=10000,
        duty_minor=1000,
        tax_rate_percent=Decimal("10"),
        additional_tax_base_minor=500,
    )

    # 10,000 + 1,000 + 500 = 11,500
    assert result[
        "tax_base_minor"
    ] == 11500

    assert result[
        "tax_minor"
    ] == 1150


def test_negative_duty_is_rejected():

    with pytest.raises(
        TaxCalculationError,
        match="Duty cannot be negative",
    ):
        calculate_import_tax(
            customs_value_minor=10000,
            duty_minor=-1,
            tax_rate_percent=Decimal("10"),
        )


def test_multiple_taxes():

    result = calculate_multiple_taxes(
        [
            {
                "tax_type": "VAT",
                "tax_base_minor": 10000,
                "tax_rate_percent": Decimal("18"),
                "currency": "INR",
            },
            {
                "tax_type": "LOCAL_TAX",
                "tax_base_minor": 10000,
                "tax_rate_percent": Decimal("2"),
                "currency": "INR",
            },
        ]
    )

    assert len(
        result["components"]
    ) == 2

    assert (
        result["components"][0]["tax_minor"]
        == 1800
    )

    assert (
        result["components"][1]["tax_minor"]
        == 200
    )

    assert result[
        "total_tax_minor"
    ] == 2000


def test_multiple_taxes_requires_components():

    with pytest.raises(
        TaxCalculationError,
        match="At least one tax component",
    ):
        calculate_multiple_taxes([])


def test_multiple_taxes_requires_tax_base():

    with pytest.raises(
        TaxCalculationError,
        match="Missing tax component field",
    ):
        calculate_multiple_taxes(
            [
                {
                    "tax_type": "VAT",
                    "tax_rate_percent": Decimal("18"),
                }
            ]
        )


def test_provenance_is_preserved():

    provenance = {
        "source": "destination-tax-table",
        "version": "2026-01",
    }

    result = calculate_tax(
        tax_base_minor=10000,
        tax_rate_percent=Decimal("18"),
        provenance=provenance,
    )

    assert result[
        "provenance"
    ] == provenance