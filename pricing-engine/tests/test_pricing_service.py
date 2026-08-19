from decimal import Decimal

from app.pricing_service import (
    PricingServiceError,
    calculate_price,
)


def test_calculate_price_returns_complete_breakdown():

    result = calculate_price(
        product_value_minor=10000,
        shipping_cost_minor=2000,
        insurance_minor=100,
        destination_country="US",
        standard_duty_rate_percent=Decimal("10"),
        tax_rate_percent=Decimal("18"),
        currency="USD",
        preferential_eligible=True,
        preferential_rate_percent=Decimal("5"),
        preferential_agreement="TEST-AGREEMENT",
        country_fee_components=[],
        platform_fee_rate_percent=Decimal("5"),
    )

    assert result["status"] == "calculated"

    assert result[
        "destination_country"
    ] == "US"

    assert result[
        "currency"
    ] == "USD"

    assert "customs_value" in result
    assert "preferential" in result
    assert "duty" in result
    assert "tax" in result
    assert "fees" in result
    assert "platform_fee" in result

    assert (
        result["landed_cost_minor"]
        >
        result["pre_platform_total_minor"]
    )


def test_standard_duty_is_used_when_not_preferential():

    result = calculate_price(
        product_value_minor=10000,
        shipping_cost_minor=0,
        insurance_minor=0,
        destination_country="US",
        standard_duty_rate_percent=Decimal("10"),
        tax_rate_percent=Decimal("0"),
        currency="USD",
        preferential_eligible=False,
        country_fee_components=[],
    )

    assert (
        result[
            "preferential"
        ]["rate_type"]
        == "STANDARD"
    )

    assert (
        result[
            "duty"
        ]["duty_minor"]
        == 1000
    )


def test_preferential_rate_is_used():

    result = calculate_price(
        product_value_minor=10000,
        shipping_cost_minor=0,
        insurance_minor=0,
        destination_country="US",
        standard_duty_rate_percent=Decimal("10"),
        tax_rate_percent=Decimal("0"),
        currency="USD",
        preferential_eligible=True,
        preferential_rate_percent=Decimal("5"),
        country_fee_components=[],
    )

    assert (
        result[
            "preferential"
        ]["effective_rate_percent"]
        == Decimal("5")
    )

    assert (
        result[
            "duty"
        ]["duty_minor"]
        == 500
    )


def test_platform_fee_is_returned():

    result = calculate_price(
        product_value_minor=10000,
        shipping_cost_minor=0,
        insurance_minor=0,
        destination_country="US",
        standard_duty_rate_percent=Decimal("0"),
        tax_rate_percent=Decimal("0"),
        currency="USD",
        country_fee_components=[],
        platform_fee_rate_percent=Decimal("5"),
    )

    assert (
        result[
            "platform_fee"
        ]["total_fee_minor"]
        == 500
    )

    assert (
        result["landed_cost_minor"]
        == 10500
    )


def test_fixed_platform_fee_is_returned():

    result = calculate_price(
        product_value_minor=10000,
        shipping_cost_minor=0,
        insurance_minor=0,
        destination_country="US",
        standard_duty_rate_percent=Decimal("0"),
        tax_rate_percent=Decimal("0"),
        currency="USD",
        country_fee_components=[],
        platform_fixed_fee_minor=250,
    )

    assert (
        result[
            "platform_fee"
        ]["total_fee_minor"]
        == 250
    )

    assert (
        result["landed_cost_minor"]
        == 10250
    )


def test_country_fees_are_returned():

    result = calculate_price(
        product_value_minor=10000,
        shipping_cost_minor=0,
        insurance_minor=0,
        destination_country="US",
        standard_duty_rate_percent=Decimal("0"),
        tax_rate_percent=Decimal("0"),
        currency="USD",
        country_fee_components=[
            {
                "fee_type": "PROCESSING",
                "base_minor": 10000,
                "rate_percent": Decimal("2"),
            }
        ],
    )

    assert (
        result[
            "fees"
        ]["total_fee_minor"]
        == 200
    )

    assert (
        result["landed_cost_minor"]
        == 10200
    )


def test_zero_shipping_is_allowed():

    result = calculate_price(
        product_value_minor=10000,
        shipping_cost_minor=0,
        insurance_minor=0,
        destination_country="US",
        standard_duty_rate_percent=Decimal("0"),
        tax_rate_percent=Decimal("0"),
        currency="USD",
        country_fee_components=[],
    )

    assert (
        result["shipping_cost_minor"]
        == 0
    )


def test_provenance_is_returned():

    provenance = {
        "source": "pricing-test",
        "version": "1.0",
    }

    result = calculate_price(
        product_value_minor=10000,
        shipping_cost_minor=0,
        insurance_minor=0,
        destination_country="US",
        standard_duty_rate_percent=Decimal("0"),
        tax_rate_percent=Decimal("0"),
        currency="USD",
        country_fee_components=[],
        provenance=provenance,
    )

    assert result[
        "provenance"
    ] == provenance