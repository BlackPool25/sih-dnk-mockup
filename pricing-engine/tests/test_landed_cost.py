from decimal import Decimal

import pytest

from app.landed_cost import (
    LandedCostCalculationError,
    calculate_landed_cost,
)


def test_basic_landed_cost():
    """
    Basic end-to-end landed-cost calculation.

    Product       = 10,000
    Shipping      = 2,000
    Insurance     = 100

    Customs value = 12,100

    Duty @ 10%    = 1,210

    Tax base      = 12,100 + 1,210
                  = 13,310

    Tax @ 18%     = 2,395.8
                  = 2,396 after rounding

    Country fees  = 0

    Platform fee  = 0

    Final         = 10,000 + 2,000 + 100
                  + 1,210 + 2,396
                  = 15,706
    """

    result = calculate_landed_cost(
        product_value_minor=10000,
        shipping_cost_minor=2000,
        insurance_minor=100,
        standard_duty_rate_percent=Decimal("10"),
        tax_rate_percent=Decimal("18"),
        destination_country="US",
        currency="INR",
        preferential_eligible=False,
        preferential_rate_percent=None,
        include_duty_in_tax_base=True,
        fee_components=[],
        platform_fee_rate_percent=Decimal("0"),
        platform_fixed_fee_minor=0,
    )

    assert result["currency"] == "INR"
    assert result["destination_country"] == "US"

    assert (
        result["customs_value"]["customs_value_minor"]
        == 12100
    )

    assert (
        result["duty"]["duty_minor"]
        == 1210
    )

    assert (
        result["tax"]["tax_base_minor"]
        == 13310
    )

    assert (
        result["tax"]["tax_minor"]
        == 2396
    )

    assert (
        result["fees"]["total_fee_minor"]
        == 0
    )

    assert (
        result["platform_fee"]["total_fee_minor"]
        == 0
    )

    assert (
        result["pre_platform_total_minor"]
        == 15706
    )

    assert (
        result["landed_cost_minor"]
        == 15706
    )


def test_preferential_rate_changes_duty():
    """
    Standard duty = 10%
    Preferential duty = 5%

    Customs value = 12,100

    Preferential duty:
        12,100 × 5% = 605
    """

    result = calculate_landed_cost(
        product_value_minor=10000,
        shipping_cost_minor=2000,
        insurance_minor=100,
        standard_duty_rate_percent=Decimal("10"),
        tax_rate_percent=Decimal("18"),
        destination_country="US",
        currency="INR",
        preferential_eligible=True,
        preferential_rate_percent=Decimal("5"),
        preferential_agreement="TEST-AGREEMENT",
        preferential_reason="Origin requirement satisfied",
        fee_components=[],
        platform_fee_rate_percent=Decimal("0"),
    )

    assert (
        result["preferential"]["eligible"]
        is True
    )

    assert (
        result["preferential"]["effective_rate_percent"]
        == Decimal("5")
    )

    assert (
        result["preferential"]["rate_type"]
        == "PREFERENTIAL"
    )

    assert (
        result["preferential"]["agreement"]
        == "TEST-AGREEMENT"
    )

    assert (
        result["duty"]["duty_rate_percent"]
        == Decimal("5")
    )

    assert (
        result["duty"]["duty_minor"]
        == 605
    )


def test_ineligible_preferential_rate_uses_standard_duty():
    """
    If preferential treatment is not available,
    the standard duty rate must be used.
    """

    result = calculate_landed_cost(
        product_value_minor=10000,
        shipping_cost_minor=2000,
        insurance_minor=100,
        standard_duty_rate_percent=Decimal("10"),
        tax_rate_percent=Decimal("18"),
        destination_country="US",
        currency="INR",
        preferential_eligible=False,
        preferential_rate_percent=None,
        fee_components=[],
    )

    assert (
        result["preferential"]["eligible"]
        is False
    )

    assert (
        result["preferential"]["rate_type"]
        == "STANDARD"
    )

    assert (
        result["preferential"]["effective_rate_percent"]
        == Decimal("10")
    )

    assert (
        result["duty"]["duty_minor"]
        == 1210
    )


def test_duty_is_included_in_tax_base():
    """
    Customs value = 10,000
    Duty = 1,000

    Tax base = 11,000

    Tax @ 10% = 1,100
    """

    result = calculate_landed_cost(
        product_value_minor=10000,
        shipping_cost_minor=0,
        insurance_minor=0,
        standard_duty_rate_percent=Decimal("10"),
        tax_rate_percent=Decimal("10"),
        destination_country="US",
        currency="USD",
        include_duty_in_tax_base=True,
        fee_components=[],
    )

    assert (
        result["customs_value"]["customs_value_minor"]
        == 10000
    )

    assert (
        result["duty"]["duty_minor"]
        == 1000
    )

    assert (
        result["tax"]["tax_base_minor"]
        == 11000
    )

    assert (
        result["tax"]["tax_minor"]
        == 1100
    )


def test_duty_is_excluded_from_tax_base():
    """
    Customs value = 10,000
    Duty = 1,000

    Duty is excluded.

    Tax base = 10,000

    Tax @ 10% = 1,000
    """

    result = calculate_landed_cost(
        product_value_minor=10000,
        shipping_cost_minor=0,
        insurance_minor=0,
        standard_duty_rate_percent=Decimal("10"),
        tax_rate_percent=Decimal("10"),
        destination_country="US",
        currency="USD",
        include_duty_in_tax_base=False,
        fee_components=[],
    )

    assert (
        result["tax"]["tax_base_minor"]
        == 10000
    )

    assert (
        result["tax"]["tax_minor"]
        == 1000
    )


def test_additional_tax_base_is_included():
    """
    Customs value = 10,000
    Duty = 1,000
    Additional tax base = 500

    Tax base:
        10,000 + 1,000 + 500
        = 11,500

    Tax @ 10% = 1,150
    """

    result = calculate_landed_cost(
        product_value_minor=10000,
        shipping_cost_minor=0,
        insurance_minor=0,
        standard_duty_rate_percent=Decimal("10"),
        tax_rate_percent=Decimal("10"),
        destination_country="US",
        currency="USD",
        include_duty_in_tax_base=True,
        additional_tax_base_minor=500,
        fee_components=[],
    )

    assert (
        result["tax"]["tax_base_minor"]
        == 11500
    )

    assert (
        result["tax"]["tax_minor"]
        == 1150
    )


def test_country_percentage_fee_is_included():
    """
    Country fee:
        2% of 10,000 = 200
    """

    result = calculate_landed_cost(
        product_value_minor=10000,
        shipping_cost_minor=0,
        insurance_minor=0,
        standard_duty_rate_percent=Decimal("0"),
        tax_rate_percent=Decimal("0"),
        destination_country="US",
        currency="USD",
        fee_components=[
            {
                "fee_type": "PROCESSING",
                "base_minor": 10000,
                "rate_percent": Decimal("2"),
            }
        ],
    )

    assert (
        result["fees"]["total_fee_minor"]
        == 200
    )

    assert (
        result["fees"]["components"][0][
            "total_fee_minor"
        ]
        == 200
    )


def test_country_fixed_fee_is_included():
    """
    Country fixed fee = 300
    """

    result = calculate_landed_cost(
        product_value_minor=10000,
        shipping_cost_minor=0,
        insurance_minor=0,
        standard_duty_rate_percent=Decimal("0"),
        tax_rate_percent=Decimal("0"),
        destination_country="US",
        currency="USD",
        fee_components=[
            {
                "fee_type": "HANDLING",
                "base_minor": 10000,
                "fixed_minor": 300,
            }
        ],
    )

    assert (
        result["fees"]["total_fee_minor"]
        == 300
    )


def test_multiple_country_fees_are_included():
    """
    Percentage fee = 2% of 10,000 = 200
    Fixed fee = 300

    Total = 500
    """

    result = calculate_landed_cost(
        product_value_minor=10000,
        shipping_cost_minor=0,
        insurance_minor=0,
        standard_duty_rate_percent=Decimal("0"),
        tax_rate_percent=Decimal("0"),
        destination_country="US",
        currency="USD",
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
    )

    assert (
        result["fees"]["total_fee_minor"]
        == 500
    )

    assert len(
        result["fees"]["components"]
    ) == 2


def test_platform_percentage_fee_is_included():
    """
    Platform fee is calculated on the
    pre-platform landed cost.

    Example with no duty/tax/country fees:

        Product = 10,000
        Shipping = 2,000

        Pre-platform total = 12,000

        Platform fee @ 5%:
            12,000 × 5%
            = 600

        Final = 12,600
    """

    result = calculate_landed_cost(
        product_value_minor=10000,
        shipping_cost_minor=2000,
        insurance_minor=0,
        standard_duty_rate_percent=Decimal("0"),
        tax_rate_percent=Decimal("0"),
        destination_country="US",
        currency="USD",
        fee_components=[],
        platform_fee_rate_percent=Decimal("5"),
        platform_fixed_fee_minor=0,
    )

    assert (
        result["pre_platform_total_minor"]
        == 12000
    )

    assert (
        result["platform_fee"]["fee_base_minor"]
        == 12000
    )

    assert (
        result["platform_fee"][
            "percentage_fee_minor"
        ]
        == 600
    )

    assert (
        result["platform_fee"]["total_fee_minor"]
        == 600
    )

    assert (
        result["landed_cost_minor"]
        == 12600
    )


def test_platform_fixed_fee_is_included():
    """
    Platform fixed fee = 250.
    """

    result = calculate_landed_cost(
        product_value_minor=10000,
        shipping_cost_minor=0,
        insurance_minor=0,
        standard_duty_rate_percent=Decimal("0"),
        tax_rate_percent=Decimal("0"),
        destination_country="US",
        currency="USD",
        fee_components=[],
        platform_fee_rate_percent=Decimal("0"),
        platform_fixed_fee_minor=250,
    )

    assert (
        result["platform_fee"]["fixed_fee_minor"]
        == 250
    )

    assert (
        result["platform_fee"]["total_fee_minor"]
        == 250
    )

    assert (
        result["landed_cost_minor"]
        == 10250
    )


def test_platform_percentage_and_fixed_fee():
    """
    Pre-platform total = 10,000

    Platform percentage = 5% = 500
    Fixed platform fee = 250

    Total platform fee = 750

    Final = 10,750
    """

    result = calculate_landed_cost(
        product_value_minor=10000,
        shipping_cost_minor=0,
        insurance_minor=0,
        standard_duty_rate_percent=Decimal("0"),
        tax_rate_percent=Decimal("0"),
        destination_country="US",
        currency="USD",
        fee_components=[],
        platform_fee_rate_percent=Decimal("5"),
        platform_fixed_fee_minor=250,
    )

    assert (
        result["platform_fee"][
            "percentage_fee_minor"
        ]
        == 500
    )

    assert (
        result["platform_fee"][
            "fixed_fee_minor"
        ]
        == 250
    )

    assert (
        result["platform_fee"]["total_fee_minor"]
        == 750
    )

    assert (
        result["landed_cost_minor"]
        == 10750
    )


def test_zero_platform_fee_does_not_change_total():
    """
    With no platform fee:

        landed cost == pre-platform total
    """

    result = calculate_landed_cost(
        product_value_minor=10000,
        shipping_cost_minor=1000,
        insurance_minor=0,
        standard_duty_rate_percent=Decimal("10"),
        tax_rate_percent=Decimal("10"),
        destination_country="US",
        currency="USD",
        fee_components=[],
        platform_fee_rate_percent=Decimal("0"),
        platform_fixed_fee_minor=0,
    )

    assert (
        result["landed_cost_minor"]
        == result["pre_platform_total_minor"]
    )


def test_other_customs_additions_are_included():
    """
    Product = 10,000
    Shipping = 1,000
    Insurance = 100
    Other additions = 500

    Customs value = 11,600
    """

    result = calculate_landed_cost(
        product_value_minor=10000,
        shipping_cost_minor=1000,
        insurance_minor=100,
        other_additions_minor=500,
        standard_duty_rate_percent=Decimal("0"),
        tax_rate_percent=Decimal("0"),
        destination_country="US",
        currency="USD",
        fee_components=[],
    )

    assert (
        result["customs_value"]["customs_value_minor"]
        == 11600
    )


def test_full_calculation_with_all_components():
    """
    Full calculation:

    Product        = 10,000
    Shipping       = 2,000
    Insurance      = 100

    Customs value:
        10,000 + 2,000 + 100
        = 12,100

    Preferential duty = 5%

    Duty:
        12,100 × 5%
        = 605

    Tax includes duty:

        12,100 + 605
        = 12,705

    Tax @ 18%:

        12,705 × 18%
        = 2,286.9
        = 2,287

    Country fee:
        2% of 10,000
        = 200

    Pre-platform total:

        10,000
        + 2,000
        + 100
        + 605
        + 2,287
        + 200
        = 15,192

    Platform fee @ 5%:

        15,192 × 5%
        = 759.6
        = 760

    Final:

        15,192 + 760
        = 15,952
    """

    result = calculate_landed_cost(
        product_value_minor=10000,
        shipping_cost_minor=2000,
        insurance_minor=100,
        standard_duty_rate_percent=Decimal("10"),
        tax_rate_percent=Decimal("18"),
        destination_country="US",
        currency="USD",
        preferential_eligible=True,
        preferential_rate_percent=Decimal("5"),
        preferential_agreement="TEST-AGREEMENT",
        preferential_reason="Eligible origin",
        include_duty_in_tax_base=True,
        fee_components=[
            {
                "fee_type": "PROCESSING",
                "base_minor": 10000,
                "rate_percent": Decimal("2"),
            }
        ],
        platform_fee_rate_percent=Decimal("5"),
        platform_fixed_fee_minor=0,
    )

    assert (
        result["customs_value"]["customs_value_minor"]
        == 12100
    )

    assert (
        result["duty"]["duty_minor"]
        == 605
    )

    assert (
        result["tax"]["tax_base_minor"]
        == 12705
    )

    assert (
        result["tax"]["tax_minor"]
        == 2287
    )

    assert (
        result["fees"]["total_fee_minor"]
        == 200
    )

    assert (
        result["pre_platform_total_minor"]
        == 15192
    )

    assert (
        result["platform_fee"]["total_fee_minor"]
        == 760
    )

    assert (
        result["landed_cost_minor"]
        == 15952
    )


def test_negative_product_value_is_rejected():

    with pytest.raises(
        LandedCostCalculationError,
        match="Product value cannot be negative",
    ):
        calculate_landed_cost(
            product_value_minor=-1,
            shipping_cost_minor=0,
            insurance_minor=0,
            standard_duty_rate_percent=Decimal("10"),
            tax_rate_percent=Decimal("10"),
            destination_country="US",
        )


def test_negative_shipping_cost_is_rejected():

    with pytest.raises(
        LandedCostCalculationError,
        match="Shipping cost cannot be negative",
    ):
        calculate_landed_cost(
            product_value_minor=10000,
            shipping_cost_minor=-1,
            insurance_minor=0,
            standard_duty_rate_percent=Decimal("10"),
            tax_rate_percent=Decimal("10"),
            destination_country="US",
        )


def test_negative_insurance_is_rejected():

    with pytest.raises(
        LandedCostCalculationError,
        match="Insurance cannot be negative",
    ):
        calculate_landed_cost(
            product_value_minor=10000,
            shipping_cost_minor=0,
            insurance_minor=-1,
            standard_duty_rate_percent=Decimal("10"),
            tax_rate_percent=Decimal("10"),
            destination_country="US",
        )


def test_negative_other_additions_are_rejected():

    with pytest.raises(
        LandedCostCalculationError,
        match="Other additions cannot be negative",
    ):
        calculate_landed_cost(
            product_value_minor=10000,
            shipping_cost_minor=0,
            insurance_minor=0,
            other_additions_minor=-1,
            standard_duty_rate_percent=Decimal("10"),
            tax_rate_percent=Decimal("10"),
            destination_country="US",
        )


def test_negative_additional_tax_base_is_rejected():

    with pytest.raises(
        LandedCostCalculationError,
        match="Additional tax base cannot be negative",
    ):
        calculate_landed_cost(
            product_value_minor=10000,
            shipping_cost_minor=0,
            insurance_minor=0,
            additional_tax_base_minor=-1,
            standard_duty_rate_percent=Decimal("10"),
            tax_rate_percent=Decimal("10"),
            destination_country="US",
        )


def test_negative_platform_fixed_fee_is_rejected():

    with pytest.raises(
        LandedCostCalculationError,
        match="Platform fixed fee cannot be negative",
    ):
        calculate_landed_cost(
            product_value_minor=10000,
            shipping_cost_minor=0,
            insurance_minor=0,
            standard_duty_rate_percent=Decimal("10"),
            tax_rate_percent=Decimal("10"),
            destination_country="US",
            platform_fixed_fee_minor=-1,
        )


def test_empty_destination_country_is_rejected():

    with pytest.raises(
        LandedCostCalculationError,
        match="Destination country is required",
    ):
        calculate_landed_cost(
            product_value_minor=10000,
            shipping_cost_minor=0,
            insurance_minor=0,
            standard_duty_rate_percent=Decimal("10"),
            tax_rate_percent=Decimal("10"),
            destination_country="",
        )


def test_invalid_destination_country_length_is_rejected():

    with pytest.raises(
        LandedCostCalculationError,
        match="exactly 2 letters",
    ):
        calculate_landed_cost(
            product_value_minor=10000,
            shipping_cost_minor=0,
            insurance_minor=0,
            standard_duty_rate_percent=Decimal("10"),
            tax_rate_percent=Decimal("10"),
            destination_country="USA",
        )


def test_invalid_destination_country_characters_are_rejected():

    with pytest.raises(
        LandedCostCalculationError,
        match="only letters",
    ):
        calculate_landed_cost(
            product_value_minor=10000,
            shipping_cost_minor=0,
            insurance_minor=0,
            standard_duty_rate_percent=Decimal("10"),
            tax_rate_percent=Decimal("10"),
            destination_country="1A",
        )


def test_destination_country_is_normalized():

    result = calculate_landed_cost(
        product_value_minor=10000,
        shipping_cost_minor=0,
        insurance_minor=0,
        standard_duty_rate_percent=Decimal("0"),
        tax_rate_percent=Decimal("0"),
        destination_country=" us ",
        currency="usd",
        fee_components=[],
    )

    assert (
        result["destination_country"]
        == "US"
    )

    assert (
        result["currency"]
        == "USD"
    )


def test_empty_currency_is_rejected():

    with pytest.raises(
        LandedCostCalculationError,
        match="Currency is required",
    ):
        calculate_landed_cost(
            product_value_minor=10000,
            shipping_cost_minor=0,
            insurance_minor=0,
            standard_duty_rate_percent=Decimal("10"),
            tax_rate_percent=Decimal("10"),
            destination_country="US",
            currency="",
        )


def test_provenance_is_preserved():

    provenance = {
        "source": "pricing-engine-test",
        "version": "1.0",
    }

    result = calculate_landed_cost(
        product_value_minor=10000,
        shipping_cost_minor=0,
        insurance_minor=0,
        standard_duty_rate_percent=Decimal("10"),
        tax_rate_percent=Decimal("10"),
        destination_country="US",
        currency="USD",
        fee_components=[],
        provenance=provenance,
    )

    assert (
        result["provenance"]
        == provenance
    )

    assert (
        result["customs_value"]["provenance"]
        == provenance
    )

    assert (
        result["duty"]["provenance"]
        == provenance
    )

    assert (
        result["tax"]["provenance"]
        == provenance
    )

    assert (
        result["platform_fee"]["provenance"]
        == provenance
    )