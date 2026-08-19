from decimal import Decimal, ROUND_HALF_UP
from typing import Any


class TaxCalculationError(Exception):
    """Raised when tax cannot be calculated."""


def _round_minor(value: Decimal) -> int:
    """Round a monetary Decimal to the nearest minor currency unit."""

    return int(
        value.quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )


def _validate_rate(
    rate_percent: Decimal,
) -> None:
    if rate_percent < Decimal("0"):
        raise TaxCalculationError(
            "Tax rate cannot be negative"
        )

    if rate_percent > Decimal("100"):
        raise TaxCalculationError(
            "Tax rate cannot exceed 100 percent"
        )


def _validate_amount(
    value: int,
    field_name: str,
) -> None:
    if value < 0:
        raise TaxCalculationError(
            f"{field_name} cannot be negative"
        )


def calculate_tax(
    tax_base_minor: int,
    tax_rate_percent: Decimal,
    *,
    tax_type: str = "IMPORT_TAX",
    currency: str = "INR",
    destination_country: str | None = None,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Calculate a single tax component.

    Parameters
    ----------
    tax_base_minor:
        Monetary amount on which the tax is calculated.

    tax_rate_percent:
        Tax percentage.

        Example:
            Decimal("18") = 18%

    tax_type:
        Name of the tax.

        Examples:
            IMPORT_TAX
            VAT
            GST
            IGST
            SALES_TAX

    currency:
        Currency of the tax base.

    destination_country:
        Optional destination country.

    provenance:
        Source information for the tax rate.

    Returns
    -------
    dict
        Structured tax calculation.
    """

    _validate_amount(
        tax_base_minor,
        "Tax base",
    )

    _validate_rate(
        tax_rate_percent
    )

    tax_type = tax_type.strip().upper()

    if not tax_type:
        raise TaxCalculationError(
            "Tax type is required"
        )

    currency = currency.strip().upper()

    if not currency:
        raise TaxCalculationError(
            "Currency is required"
        )

    if destination_country is not None:
        destination_country = (
            destination_country.strip().upper()
        )

        if not destination_country:
            raise TaxCalculationError(
                "Destination country cannot be empty"
            )

    tax_base = Decimal(
        tax_base_minor
    )

    rate = (
        tax_rate_percent
        / Decimal("100")
    )

    tax_minor = _round_minor(
        tax_base * rate
    )

    return {
        "tax_type": tax_type,
        "tax_base_minor": tax_base_minor,
        "tax_rate_percent": tax_rate_percent,
        "tax_minor": tax_minor,
        "currency": currency,
        "destination_country": (
            destination_country
        ),
        "provenance": provenance or {},
    }


def calculate_import_tax(
    customs_value_minor: int,
    duty_minor: int,
    tax_rate_percent: Decimal,
    *,
    tax_type: str = "IMPORT_TAX",
    currency: str = "INR",
    destination_country: str | None = None,
    include_duty_in_tax_base: bool = True,
    additional_tax_base_minor: int = 0,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Calculate an import tax.

    By default:

        Tax Base =
            Customs Value
            + Import Duty
            + Additional Tax Base

    If the destination country's tax rules do not include
    duty in the tax base, set:

        include_duty_in_tax_base=False

    The caller is responsible for supplying the correct
    country-specific rule.
    """

    _validate_amount(
        customs_value_minor,
        "Customs value",
    )

    _validate_amount(
        duty_minor,
        "Duty",
    )

    _validate_amount(
        additional_tax_base_minor,
        "Additional tax base",
    )

    if include_duty_in_tax_base:
        tax_base_minor = (
            customs_value_minor
            + duty_minor
            + additional_tax_base_minor
        )
    else:
        tax_base_minor = (
            customs_value_minor
            + additional_tax_base_minor
        )

    result = calculate_tax(
        tax_base_minor=tax_base_minor,
        tax_rate_percent=tax_rate_percent,
        tax_type=tax_type,
        currency=currency,
        destination_country=destination_country,
        provenance=provenance,
    )

    result.update(
        {
            "customs_value_minor": (
                customs_value_minor
            ),
            "duty_minor": duty_minor,
            "include_duty_in_tax_base": (
                include_duty_in_tax_base
            ),
            "additional_tax_base_minor": (
                additional_tax_base_minor
            ),
        }
    )

    return result


def calculate_multiple_taxes(
    tax_components: list[dict[str, Any]],
) -> dict[str, Any]:
    """
    Aggregate multiple independent tax components.

    Each component must contain:

        tax_type
        tax_base_minor
        tax_rate_percent

    This function calculates each component and returns
    both the individual breakdown and the total.

    Example:

        VAT  = 18%
        Local tax = 2%

    can be represented as two separate components.
    """

    if not tax_components:
        raise TaxCalculationError(
            "At least one tax component is required"
        )

    calculated_components: list[
        dict[str, Any]
    ] = []

    total_tax_minor = 0

    for component in tax_components:
        if not isinstance(component, dict):
            raise TaxCalculationError(
                "Each tax component must be an object"
            )

        try:
            result = calculate_tax(
                tax_base_minor=component[
                    "tax_base_minor"
                ],
                tax_rate_percent=component[
                    "tax_rate_percent"
                ],
                tax_type=component.get(
                    "tax_type",
                    "IMPORT_TAX",
                ),
                currency=component.get(
                    "currency",
                    "INR",
                ),
                destination_country=component.get(
                    "destination_country"
                ),
                provenance=component.get(
                    "provenance"
                ),
            )
        except KeyError as exc:
            raise TaxCalculationError(
                f"Missing tax component field: {exc.args[0]}"
            ) from exc

        calculated_components.append(
            result
        )

        total_tax_minor += result[
            "tax_minor"
        ]

    return {
        "components": calculated_components,
        "total_tax_minor": total_tax_minor,
        "currency": calculated_components[0][
            "currency"
        ],
    }