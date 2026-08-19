from decimal import Decimal, ROUND_HALF_UP
from typing import Any


class FeeCalculationError(Exception):
    """Raised when country fees cannot be calculated."""


def _round_minor(value: Decimal) -> int:
    return int(
        value.quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
    )


def _validate_amount(
    value: int,
    field_name: str,
) -> None:
    if value < 0:
        raise FeeCalculationError(
            f"{field_name} cannot be negative"
        )


def _validate_rate(
    value: Decimal,
    field_name: str,
) -> None:
    if value < Decimal("0"):
        raise FeeCalculationError(
            f"{field_name} cannot be negative"
        )

    if value > Decimal("100"):
        raise FeeCalculationError(
            f"{field_name} cannot exceed 100 percent"
        )


def calculate_fee(
    *,
    fee_type: str,
    base_minor: int,
    rate_percent: Decimal = Decimal("0"),
    fixed_minor: int = 0,
    currency: str = "INR",
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Calculate one country-specific fee.

    Fee formula:

        percentage fee =
            base × rate / 100

        total fee =
            percentage fee + fixed fee

    Monetary values use minor currency units.
    """

    if not fee_type or not fee_type.strip():
        raise FeeCalculationError(
            "Fee type is required"
        )

    _validate_amount(
        base_minor,
        "Fee base",
    )

    _validate_amount(
        fixed_minor,
        "Fixed fee",
    )

    _validate_rate(
        rate_percent,
        "Fee rate",
    )

    currency = currency.strip().upper()

    if not currency:
        raise FeeCalculationError(
            "Currency is required"
        )

    percentage_fee_minor = _round_minor(
        Decimal(base_minor)
        * rate_percent
        / Decimal("100")
    )

    total_fee_minor = (
        percentage_fee_minor
        + fixed_minor
    )

    return {
        "fee_type": fee_type.strip().upper(),
        "base_minor": base_minor,
        "rate_percent": rate_percent,
        "percentage_fee_minor": (
            percentage_fee_minor
        ),
        "fixed_fee_minor": fixed_minor,
        "total_fee_minor": total_fee_minor,
        "currency": currency,
        "provenance": provenance or {},
    }


def calculate_country_fees(
    *,
    country_code: str,
    fee_components: list[dict[str, Any]],
    currency: str = "INR",
) -> dict[str, Any]:
    """
    Calculate all configured fees for a destination country.

    Each fee component must contain:

        fee_type
        base_minor

    Optional:

        rate_percent
        fixed_minor
        provenance
    """

    country_code = country_code.strip().upper()

    if not country_code:
        raise FeeCalculationError(
            "Country code is required"
        )

    if len(country_code) != 2:
        raise FeeCalculationError(
            "Country code must contain exactly 2 letters"
        )

    if not country_code.isalpha():
        raise FeeCalculationError(
            "Country code must contain only letters"
        )

    if not fee_components:
        return {
            "country_code": country_code,
            "components": [],
            "total_fee_minor": 0,
            "currency": currency.upper(),
        }

    components: list[
        dict[str, Any]
    ] = []

    total_fee_minor = 0

    for component in fee_components:
        if not isinstance(component, dict):
            raise FeeCalculationError(
                "Each fee component must be an object"
            )

        if "fee_type" not in component:
            raise FeeCalculationError(
                "Missing fee component field: fee_type"
            )

        if "base_minor" not in component:
            raise FeeCalculationError(
                "Missing fee component field: base_minor"
            )

        raw_rate = component.get("rate_percent", Decimal("0"))
        rate_percent = raw_rate if isinstance(raw_rate, Decimal) else Decimal(str(raw_rate))
        result = calculate_fee(
            fee_type=component["fee_type"],
            base_minor=int(component["base_minor"]),
            rate_percent=rate_percent,
            fixed_minor=int(component.get("fixed_minor", 0)),
            currency=component.get(
                "currency",
                currency,
            ),
            provenance=component.get(
                "provenance",
                {},
            ),
        )

        components.append(result)

        total_fee_minor += result[
            "total_fee_minor"
        ]

    return {
        "country_code": country_code,
        "components": components,
        "total_fee_minor": total_fee_minor,
        "currency": currency.upper(),
    }