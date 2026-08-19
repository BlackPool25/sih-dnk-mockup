from decimal import Decimal
from typing import Any

from app.landed_cost import calculate_landed_cost


class PricingServiceError(Exception):
    """Raised when the pricing service cannot calculate a quote."""


def calculate_price(
    *,
    product_value_minor: int,
    shipping_cost_minor: int,
    insurance_minor: int,
    destination_country: str,
    standard_duty_rate_percent: Decimal,
    tax_rate_percent: Decimal,
    currency: str = "INR",
    preferential_eligible: bool = False,
    preferential_rate_percent: Decimal | None = None,
    preferential_agreement: str | None = None,
    preferential_reason: str | None = None,
    include_duty_in_tax_base: bool = True,
    additional_tax_base_minor: int = 0,
    other_additions_minor: int = 0,
    country_fee_components: list[
        dict[str, Any]
    ] | None = None,
    platform_fee_rate_percent: Decimal = Decimal("0"),
    platform_fixed_fee_minor: int = 0,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Calculate a complete pricing quote.

    This function is intentionally an orchestration layer.
    Individual financial calculations remain inside their
    dedicated modules.
    """

    try:
        landed_cost = calculate_landed_cost(
            product_value_minor=product_value_minor,
            shipping_cost_minor=shipping_cost_minor,
            insurance_minor=insurance_minor,
            standard_duty_rate_percent=(
                standard_duty_rate_percent
            ),
            tax_rate_percent=(
                tax_rate_percent
            ),
            destination_country=(
                destination_country
            ),
            currency=currency,
            preferential_eligible=(
                preferential_eligible
            ),
            preferential_rate_percent=(
                preferential_rate_percent
            ),
            preferential_agreement=(
                preferential_agreement
            ),
            preferential_reason=(
                preferential_reason
            ),
            include_duty_in_tax_base=(
                include_duty_in_tax_base
            ),
            additional_tax_base_minor=(
                additional_tax_base_minor
            ),
            fee_components=(
                country_fee_components
            ),
            other_additions_minor=(
                other_additions_minor
            ),
            platform_fee_rate_percent=(
                platform_fee_rate_percent
            ),
            platform_fixed_fee_minor=(
                platform_fixed_fee_minor
            ),
            provenance=provenance,
        )

    except Exception as exc:
        if isinstance(
            exc,
            PricingServiceError,
        ):
            raise

        raise PricingServiceError(
            f"Unable to calculate pricing: {exc}"
        ) from exc

    return {
        "status": "calculated",
        "currency": landed_cost[
            "currency"
        ],
        "destination_country": landed_cost[
            "destination_country"
        ],

        "product_value_minor": landed_cost[
            "product_value_minor"
        ],

        "shipping_cost_minor": landed_cost[
            "shipping_cost_minor"
        ],

        "customs_value": landed_cost[
            "customs_value"
        ],

        "preferential": landed_cost[
            "preferential"
        ],

        "duty": landed_cost[
            "duty"
        ],

        "tax": landed_cost[
            "tax"
        ],

        "fees": landed_cost[
            "fees"
        ],

        "platform_fee": landed_cost[
            "platform_fee"
        ],

        "pre_platform_total_minor": (
            landed_cost[
                "pre_platform_total_minor"
            ]
        ),

        "landed_cost_minor": landed_cost[
            "landed_cost_minor"
        ],

        "provenance": landed_cost[
            "provenance"
        ],
    }