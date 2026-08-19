from decimal import Decimal
from typing import Any


class TaxRateLookupError(Exception):
    """Raised when a country tax configuration cannot be found."""


# Temporary deterministic configuration.
#
# These are ENGINE TEST CONFIGURATIONS, not authoritative
# real-world tax rates. Replace them later with your verified
# country/rate data source.
TAX_RATE_TABLE: dict[str, dict[str, Any]] = {
    "US": {
        "currency": "USD",
        "tax_components": [
            {
                "tax_type": "IMPORT_TAX",
                "rate_percent": Decimal("0"),
                "include_duty_in_tax_base": False,
            }
        ],
        "provenance": {
            "source": "engine-test-configuration",
            "version": "1.0",
        },
    },
    "IN": {
        "currency": "INR",
        "tax_components": [
            {
                "tax_type": "IMPORT_TAX",
                "rate_percent": Decimal("18"),
                "include_duty_in_tax_base": True,
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
        raise TaxRateLookupError(
            "Country code must be a string"
        )

    country_code = country_code.strip().upper()

    if len(country_code) != 2:
        raise TaxRateLookupError(
            "Country code must contain exactly 2 letters"
        )

    if not country_code.isalpha():
        raise TaxRateLookupError(
            "Country code must contain only letters"
        )

    return country_code


def lookup_tax_rates(
    country_code: str,
) -> dict[str, Any]:
    """
    Return the configured tax rules for a destination country.

    The returned object is copied so callers cannot accidentally
    modify the global configuration.
    """

    country_code = normalize_country_code(
        country_code
    )

    configuration = TAX_RATE_TABLE.get(
        country_code
    )

    if configuration is None:
        raise TaxRateLookupError(
            f"No tax configuration found for "
            f"country {country_code}"
        )

    return {
        "country_code": country_code,
        "currency": configuration["currency"],
        "tax_components": [
            dict(component)
            for component in configuration[
                "tax_components"
            ]
        ],
        "provenance": dict(
            configuration.get(
                "provenance",
                {},
            )
        ),
    }


def get_primary_tax_rate(
    country_code: str,
) -> Decimal:
    """
    Return the first configured tax rate.

    Use this only where a single tax component is expected.
    """

    configuration = lookup_tax_rates(
        country_code
    )

    components = configuration[
        "tax_components"
    ]

    if not components:
        raise TaxRateLookupError(
            f"No tax components configured for "
            f"{country_code}"
        )

    return Decimal(
        components[0]["rate_percent"]
    )