from decimal import Decimal, ROUND_HALF_UP
from typing import Any


class DutyCalculationError(Exception):
    """Raised when duty cannot be calculated."""


def _money(value: Decimal) -> Decimal:
    """
    Round monetary values to two decimal places.
    """

    return value.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )


def _validate_rate(rate: Decimal) -> None:
    if rate < Decimal("0"):
        raise DutyCalculationError(
            "Duty rate cannot be negative"
        )

    if rate > Decimal("100"):
        raise DutyCalculationError(
            "Duty rate cannot exceed 100 percent"
        )


def calculate_duty(
    customs_value_minor: int,
    duty_rate_percent: Decimal,
    *,
    currency: str = "INR",
    basis: str = "CIF",
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Calculate import duty.

    Parameters
    ----------
    customs_value_minor:
        Customs value in the smallest currency unit.

        Example:
            INR 10,000 -> 1000000 paise

    duty_rate_percent:
        Duty percentage.

        Example:
            10% -> Decimal("10")

    currency:
        Currency of the customs value.

    basis:
        Duty valuation basis.

        Currently this function expects the caller to provide
        the already-computed customs value.

    provenance:
        Optional information describing where the rate/value
        originated.

    Returns
    -------
    dict
        Structured duty calculation.
    """

    if customs_value_minor < 0:
        raise DutyCalculationError(
            "Customs value cannot be negative"
        )

    _validate_rate(duty_rate_percent)

    if not currency or not currency.strip():
        raise DutyCalculationError(
            "Currency is required"
        )

    if not basis or not basis.strip():
        raise DutyCalculationError(
            "Duty basis is required"
        )

    customs_value = Decimal(
        customs_value_minor
    )

    rate = (
        duty_rate_percent
        / Decimal("100")
    )

    duty_minor = (
        customs_value * rate
    ).quantize(
        Decimal("1"),
        rounding=ROUND_HALF_UP,
    )

    duty_minor_int = int(duty_minor)

    return {
        "customs_value_minor": customs_value_minor,
        "duty_rate_percent": duty_rate_percent,
        "duty_minor": duty_minor_int,
        "currency": currency.upper(),
        "basis": basis.upper(),
        "provenance": provenance or {},
    }


def calculate_duty_from_value(
    customs_value_minor: int,
    duty_rate_percent: Decimal,
    *,
    currency: str = "INR",
    basis: str = "CIF",
    preferential_rate_percent: Decimal | None = None,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Calculate duty while optionally applying a preferential
    duty rate.

    If a preferential rate is supplied, it is used instead
    of the standard rate.

    This function does NOT determine eligibility for the
    preferential rate. Eligibility must be established by
    the preferential-rate component.
    """

    effective_rate = duty_rate_percent
    rate_type = "STANDARD"

    if preferential_rate_percent is not None:
        _validate_rate(
            preferential_rate_percent
        )

        if (
            preferential_rate_percent
            > duty_rate_percent
        ):
            raise DutyCalculationError(
                "Preferential duty rate cannot be "
                "greater than the standard duty rate"
            )

        effective_rate = (
            preferential_rate_percent
        )
        rate_type = "PREFERENTIAL"

    result = calculate_duty(
        customs_value_minor=customs_value_minor,
        duty_rate_percent=effective_rate,
        currency=currency,
        basis=basis,
        provenance=provenance,
    )

    result["standard_duty_rate_percent"] = (
        duty_rate_percent
    )

    result["preferential_duty_rate_percent"] = (
        preferential_rate_percent
    )

    result["rate_type"] = rate_type

    return result