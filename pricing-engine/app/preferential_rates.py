from decimal import Decimal
from typing import Any


class PreferentialRateLookupError(Exception):
    """Raised when preferential-rate data is unavailable."""


# Test configuration only.
#
# These values are intentionally deterministic test data.
# They are NOT authoritative real-world tariff rates.
PREFERENTIAL_RATE_TABLE: dict[
    tuple[str, str, str],
    dict[str, Any],
] = {
    (
        "IN",
        "US",
        "JUTE-PRODUCTS",
    ): {
        "eligible": True,
        "rate_percent": Decimal("5"),
        "agreement": "TEST-PREFERENTIAL-AGREEMENT",
        "conditions": [
            "ORIGIN_REQUIREMENT",
            "DOCUMENTATION_REQUIRED",
        ],
        "provenance": {
            "source": "engine-test-configuration",
            "version": "1.0",
        },
    },
}


def normalize_code(
    value: str,
    field_name: str,
) -> str:
    if not isinstance(value, str):
        raise PreferentialRateLookupError(
            f"{field_name} must be a string"
        )

    value = value.strip().upper()

    if not value:
        raise PreferentialRateLookupError(
            f"{field_name} cannot be empty"
        )

    return value


def lookup_preferential_rate(
    *,
    origin_country: str,
    destination_country: str,
    category_slug: str,
) -> dict[str, Any]:
    """
    Look up preferential treatment for a shipment.

    Eligibility data is returned separately from the actual
    rate calculation.
    """

    origin_country = normalize_code(
        origin_country,
        "origin_country",
    )

    destination_country = normalize_code(
        destination_country,
        "destination_country",
    )

    category_slug = normalize_code(
        category_slug,
        "category_slug",
    )

    key = (
        origin_country,
        destination_country,
        category_slug,
    )

    result = PREFERENTIAL_RATE_TABLE.get(key)

    if result is None:
        return {
            "eligible": False,
            "rate_percent": None,
            "agreement": None,
            "conditions": [],
            "provenance": {},
        }

    return {
        "eligible": bool(
            result["eligible"]
        ),
        "rate_percent": (
            Decimal(result["rate_percent"])
        ),
        "agreement": result.get(
            "agreement"
        ),
        "conditions": list(
            result.get(
                "conditions",
                [],
            )
        ),
        "provenance": dict(
            result.get(
                "provenance",
                {},
            )
        ),
    }