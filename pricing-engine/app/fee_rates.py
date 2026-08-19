from decimal import Decimal
from typing import Any


class FeeRateLookupError(Exception):
    """Raised when country-fee configuration is unavailable."""


# TEST CONFIGURATION ONLY.
#
# These values are intentionally deterministic examples for
# testing the engine. They are NOT authoritative real-world
# fee schedules.
COUNTRY_FEE_TABLE: dict[
    str,
    dict[str, Any],
] = {
    "US": {
        "currency": "USD",
        "fees": [
            {
                "fee_type": "CUSTOMS_PROCESSING",
                "rate_percent": Decimal("0"),
                "fixed_minor": 250,
            }
        ],
        "provenance": {
            "source": "engine-test-configuration",
            "version": "1.0",
        },
    },
    "IN": {
        "currency": "INR",
        "fees": [
            {
                "fee_type": "CUSTOMS_PROCESSING",
                "rate_percent": Decimal("1"),
                "fixed_minor": 100,
            }
        ],
        "provenance": {
            "source": "engine-test-configuration",
            "version": "1.0",
        },
    },
}


def normalize_country_code(
    country_code: str,
) -> str:
    if not isinstance(country_code, str):
        raise FeeRateLookupError(
            "Country code must be a string"
        )

    country_code = country_code.strip().upper()

    if len(country_code) != 2:
        raise FeeRateLookupError(
            "Country code must contain exactly 2 letters"
        )

    if not country_code.isalpha():
        raise FeeRateLookupError(
            "Country code must contain only letters"
        )

    return country_code


def lookup_country_fees(
    country_code: str,
) -> dict[str, Any]:
    """
    Return fee configuration for a country.

    A copy is returned so callers cannot modify the
    global configuration.
    """

    country_code = normalize_country_code(
        country_code
    )

    configuration = COUNTRY_FEE_TABLE.get(
        country_code
    )

    if configuration is None:
        raise FeeRateLookupError(
            f"No fee configuration found for "
            f"country {country_code}"
        )

    return {
        "country_code": country_code,
        "currency": configuration["currency"],
        "fees": [
            dict(fee)
            for fee in configuration["fees"]
        ],
        "provenance": dict(
            configuration.get(
                "provenance",
                {},
            )
        ),
    }