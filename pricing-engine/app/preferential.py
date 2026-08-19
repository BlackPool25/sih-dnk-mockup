from decimal import Decimal
from typing import Any


class PreferentialRateError(Exception):
    """Raised when preferential-rate processing fails."""


def _validate_rate(
    rate: Decimal,
    field_name: str,
) -> None:
    if rate < Decimal("0"):
        raise PreferentialRateError(
            f"{field_name} cannot be negative"
        )

    if rate > Decimal("100"):
        raise PreferentialRateError(
            f"{field_name} cannot exceed 100 percent"
        )


def calculate_preferential_rate(
    *,
    eligible: bool,
    standard_rate_percent: Decimal,
    preferential_rate_percent: Decimal | None,
    reason: str | None = None,
    agreement: str | None = None,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Determine the effective duty rate.

    Important:
        This function does NOT determine eligibility.

    The caller must first determine whether the shipment
    qualifies for preferential treatment.

    If eligible=True, preferential_rate_percent is required.

    If eligible=False, the standard duty rate is used.
    """

    _validate_rate(
        standard_rate_percent,
        "Standard duty rate",
    )

    if preferential_rate_percent is not None:
        _validate_rate(
            preferential_rate_percent,
            "Preferential duty rate",
        )

    if eligible:
        if preferential_rate_percent is None:
            raise PreferentialRateError(
                "Preferential rate is required when "
                "shipment is eligible"
            )

        if (
            preferential_rate_percent
            > standard_rate_percent
        ):
            raise PreferentialRateError(
                "Preferential rate cannot be greater "
                "than standard duty rate"
            )

        effective_rate = (
            preferential_rate_percent
        )

        rate_type = "PREFERENTIAL"

    else:
        effective_rate = (
            standard_rate_percent
        )

        rate_type = "STANDARD"

    return {
        "eligible": eligible,
        "standard_rate_percent": (
            standard_rate_percent
        ),
        "preferential_rate_percent": (
            preferential_rate_percent
        ),
        "effective_rate_percent": (
            effective_rate
        ),
        "rate_type": rate_type,
        "agreement": agreement,
        "reason": reason,
        "provenance": provenance or {},
    }