import pytest

from app.customs_value import (
    CustomsValueCalculationError,
    calculate_customs_value,
)


def test_product_value_only():

    result = calculate_customs_value(
        product_value_minor=10000,
    )

    assert result["product_value_minor"] == 10000
    assert result["shipping_cost_minor"] == 0
    assert result["insurance_minor"] == 0
    assert result["other_additions_minor"] == 0
    assert result["customs_value_minor"] == 10000


def test_cif_customs_value():

    result = calculate_customs_value(
        product_value_minor=10000,
        shipping_cost_minor=2000,
        insurance_minor=100,
    )

    assert result["customs_value_minor"] == 12100


def test_other_additions_are_included():

    result = calculate_customs_value(
        product_value_minor=10000,
        shipping_cost_minor=2000,
        insurance_minor=100,
        other_additions_minor=500,
    )

    assert result["customs_value_minor"] == 12600


def test_all_zero_additions():

    result = calculate_customs_value(
        product_value_minor=10000,
        shipping_cost_minor=0,
        insurance_minor=0,
        other_additions_minor=0,
    )

    assert result["customs_value_minor"] == 10000


def test_negative_product_value_is_rejected():

    with pytest.raises(
        CustomsValueCalculationError,
        match="Product value cannot be negative",
    ):
        calculate_customs_value(
            product_value_minor=-1,
        )


def test_negative_shipping_is_rejected():

    with pytest.raises(
        CustomsValueCalculationError,
        match="Shipping cost cannot be negative",
    ):
        calculate_customs_value(
            product_value_minor=10000,
            shipping_cost_minor=-1,
        )


def test_negative_insurance_is_rejected():

    with pytest.raises(
        CustomsValueCalculationError,
        match="Insurance cannot be negative",
    ):
        calculate_customs_value(
            product_value_minor=10000,
            insurance_minor=-1,
        )


def test_negative_other_addition_is_rejected():

    with pytest.raises(
        CustomsValueCalculationError,
        match="Other additions cannot be negative",
    ):
        calculate_customs_value(
            product_value_minor=10000,
            other_additions_minor=-1,
        )


def test_currency_is_normalized():

    result = calculate_customs_value(
        product_value_minor=10000,
        currency="inr",
    )

    assert result["currency"] == "INR"


def test_empty_currency_is_rejected():

    with pytest.raises(
        CustomsValueCalculationError,
        match="Currency is required",
    ):
        calculate_customs_value(
            product_value_minor=10000,
            currency="",
        )


def test_cif_basis_is_normalized():

    result = calculate_customs_value(
        product_value_minor=10000,
        basis="cif",
    )

    assert result["basis"] == "CIF"


def test_unsupported_basis_is_rejected():

    with pytest.raises(
        CustomsValueCalculationError,
        match="Unsupported customs valuation basis",
    ):
        calculate_customs_value(
            product_value_minor=10000,
            basis="FOB",
        )


def test_provenance_is_preserved():

    provenance = {
        "source": "test-rate-table",
        "version": "1.0",
    }

    result = calculate_customs_value(
        product_value_minor=10000,
        provenance=provenance,
    )

    assert result["provenance"] == provenance


def test_customs_value_with_realistic_example():

    result = calculate_customs_value(
        product_value_minor=1000000,
        shipping_cost_minor=250000,
        insurance_minor=5000,
    )

    assert result["customs_value_minor"] == 1255000