from decimal import Decimal, ROUND_HALF_UP
from typing import Any


class CustomsValueCalculationError(Exception):
    """Raised when customs value cannot be calculated."""


def _round_minor(value: Decimal) -> int:
    """Round a monetary Decimal to the nearest minor unit."""
    return int(
        value.quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )


def _validate_non_negative(
    value: int,
    field_name: str,
) -> None:
    if value < 0:
        raise CustomsValueCalculationError(
            f"{field_name} cannot be negative"
        )


def calculate_customs_value(
    product_value_minor: int,
    shipping_cost_minor: int = 0,
    insurance_minor: int = 0,
    other_additions_minor: int = 0,
    *,
    currency: str = "INR",
    basis: str = "CIF",
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Calculate the customs value used as the basis for duty.

    For CIF:

        Customs Value =
            Product Value
            + Shipping
            + Insurance
            + Other Applicable Additions

    All monetary values are expressed in minor currency units.

    Example:

        Product value = 10,000
        Shipping     = 2,000
        Insurance    = 100

        Customs value = 12,100
    """

    _validate_non_negative(
        product_value_minor,
        "Product value",
    )

    _validate_non_negative(
        shipping_cost_minor,
        "Shipping cost",
    )

    _validate_non_negative(
        insurance_minor,
        "Insurance",
    )

    _validate_non_negative(
        other_additions_minor,
        "Other additions",
    )

    currency = currency.strip().upper()

    if not currency:
        raise CustomsValueCalculationError(
            "Currency is required"
        )

    basis = basis.strip().upper()

    if not basis:
        raise CustomsValueCalculationError(
            "Customs valuation basis is required"
        )

    if basis != "CIF":
        raise CustomsValueCalculationError(
            f"Unsupported customs valuation basis: {basis}"
        )

    product_value = Decimal(
        product_value_minor
    )

    shipping_cost = Decimal(
        shipping_cost_minor
    )

    insurance = Decimal(
        insurance_minor
    )

    other_additions = Decimal(
        other_additions_minor
    )

    customs_value = (
        product_value
        + shipping_cost
        + insurance
        + other_additions
    )

    customs_value_minor = _round_minor(
        customs_value
    )

    return {
        "basis": basis,
        "product_value_minor": product_value_minor,
        "shipping_cost_minor": shipping_cost_minor,
        "insurance_minor": insurance_minor,
        "other_additions_minor": other_additions_minor,
        "customs_value_minor": customs_value_minor,
        "currency": currency,
        "provenance": provenance or {},
    }