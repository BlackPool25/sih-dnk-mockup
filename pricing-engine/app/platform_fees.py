from decimal import Decimal, ROUND_HALF_UP
from typing import Any


class PlatformFeeCalculationError(Exception):
    """Raised when a platform fee cannot be calculated."""


def _round_minor(value: Decimal) -> int:
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
        raise PlatformFeeCalculationError(
            f"{field_name} cannot be negative"
        )


def _validate_rate(
    value: Decimal,
    field_name: str,
) -> None:
    if value < Decimal("0"):
        raise PlatformFeeCalculationError(
            f"{field_name} cannot be negative"
        )

    if value > Decimal("100"):
        raise PlatformFeeCalculationError(
            f"{field_name} cannot exceed 100 percent"
        )


def calculate_platform_fee(
    *,
    fee_base_minor: int,
    rate_percent: Decimal = Decimal("0"),
    fixed_fee_minor: int = 0,
    currency: str = "INR",
    fee_type: str = "PLATFORM_FEE",
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Calculate the platform fee.

    Formula:

        percentage component =
            fee base × rate / 100

        total platform fee =
            percentage component
            + fixed fee

    All monetary values are represented in minor
    currency units.
    """

    _validate_non_negative(
        fee_base_minor,
        "Platform fee base",
    )

    _validate_non_negative(
        fixed_fee_minor,
        "Platform fixed fee",
    )

    _validate_rate(
        rate_percent,
        "Platform fee rate",
    )

    fee_type = fee_type.strip().upper()

    if not fee_type:
        raise PlatformFeeCalculationError(
            "Platform fee type is required"
        )

    currency = currency.strip().upper()

    if not currency:
        raise PlatformFeeCalculationError(
            "Currency is required"
        )

    percentage_fee_minor = _round_minor(
        Decimal(fee_base_minor)
        * rate_percent
        / Decimal("100")
    )

    total_fee_minor = (
        percentage_fee_minor
        + fixed_fee_minor
    )

    return {
        "fee_type": fee_type,
        "fee_base_minor": fee_base_minor,
        "rate_percent": rate_percent,
        "percentage_fee_minor": (
            percentage_fee_minor
        ),
        "fixed_fee_minor": fixed_fee_minor,
        "total_fee_minor": total_fee_minor,
        "currency": currency,
        "provenance": provenance or {},
    }