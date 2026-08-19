from decimal import Decimal
from typing import Any

from app.customs_value import calculate_customs_value
from app.duty import calculate_duty_from_value
from app.fees import calculate_country_fees
from app.preferential import calculate_preferential_rate
from app.platform_fees import calculate_platform_fee
from app.tax import calculate_import_tax


class LandedCostCalculationError(Exception):
    """Raised when landed cost cannot be calculated."""


def _require_non_negative(
    value: int,
    field_name: str,
) -> None:
    if value < 0:
        raise LandedCostCalculationError(
            f"{field_name} cannot be negative"
        )


def _validate_country_code(
    country_code: str,
) -> str:
    if not isinstance(country_code, str):
        raise LandedCostCalculationError(
            "Destination country must be a string"
        )

    country_code = country_code.strip().upper()

    if not country_code:
        raise LandedCostCalculationError(
            "Destination country is required"
        )

    if len(country_code) != 2:
        raise LandedCostCalculationError(
            "Destination country must contain exactly 2 letters"
        )

    if not country_code.isalpha():
        raise LandedCostCalculationError(
            "Destination country must contain only letters"
        )

    return country_code


def _validate_currency(
    currency: str,
) -> str:
    if not isinstance(currency, str):
        raise LandedCostCalculationError(
            "Currency must be a string"
        )

    currency = currency.strip().upper()

    if not currency:
        raise LandedCostCalculationError(
            "Currency is required"
        )

    return currency


def calculate_landed_cost(
    *,
    product_value_minor: int,
    shipping_cost_minor: int,
    insurance_minor: int,
    standard_duty_rate_percent: Decimal,
    tax_rate_percent: Decimal,
    destination_country: str,
    currency: str = "INR",
    preferential_eligible: bool = False,
    preferential_rate_percent: Decimal | None = None,
    preferential_agreement: str | None = None,
    preferential_reason: str | None = None,
    include_duty_in_tax_base: bool = True,
    additional_tax_base_minor: int = 0,
    fee_components: list[dict[str, Any]] | None = None,
    other_additions_minor: int = 0,
    platform_fee_rate_percent: Decimal = Decimal("0"),
    platform_fixed_fee_minor: int = 0,
    provenance: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Calculate the complete landed cost.

    Calculation flow:

        Product value
            +
        Shipping
            +
        Insurance
            +
        Other customs additions
            ↓
        Customs Value
            ↓
        Preferential Rate Selection
            ↓
        Import Duty
            ↓
        Import Tax
            ↓
        Country / Customs Fees
            ↓
        Pre-Platform Total
            ↓
        Platform Fee
            ↓
        Final Landed Cost

    All monetary values are represented in minor
    currency units.

    Example:

        INR 10,000 = 1,000,000 paise

    The function intentionally keeps every component
    separately visible in the returned dictionary.
    """

    # --------------------------------------------------------
    # 1. Validate monetary inputs
    # --------------------------------------------------------

    _require_non_negative(
        product_value_minor,
        "Product value",
    )

    _require_non_negative(
        shipping_cost_minor,
        "Shipping cost",
    )

    _require_non_negative(
        insurance_minor,
        "Insurance",
    )

    _require_non_negative(
        other_additions_minor,
        "Other additions",
    )

    _require_non_negative(
        additional_tax_base_minor,
        "Additional tax base",
    )

    _require_non_negative(
        platform_fixed_fee_minor,
        "Platform fixed fee",
    )

    # --------------------------------------------------------
    # 2. Validate country and currency
    # --------------------------------------------------------

    destination_country = _validate_country_code(
        destination_country
    )

    currency = _validate_currency(
        currency
    )

    # --------------------------------------------------------
    # 3. Calculate customs value
    # --------------------------------------------------------

    customs_value = calculate_customs_value(
        product_value_minor=(
            product_value_minor
        ),
        shipping_cost_minor=(
            shipping_cost_minor
        ),
        insurance_minor=(
            insurance_minor
        ),
        other_additions_minor=(
            other_additions_minor
        ),
        currency=currency,
        basis="CIF",
        provenance=provenance,
    )

    customs_value_minor = customs_value[
        "customs_value_minor"
    ]

    # --------------------------------------------------------
    # 4. Calculate preferential rate
    # --------------------------------------------------------

    preferential = calculate_preferential_rate(
        eligible=preferential_eligible,
        standard_rate_percent=(
            standard_duty_rate_percent
        ),
        preferential_rate_percent=(
            preferential_rate_percent
        ),
        agreement=(
            preferential_agreement
        ),
        reason=(
            preferential_reason
        ),
        provenance=provenance,
    )

    effective_duty_rate = preferential[
        "effective_rate_percent"
    ]

    # --------------------------------------------------------
    # 5. Calculate import duty
    # --------------------------------------------------------

    duty = calculate_duty_from_value(
        customs_value_minor=(
            customs_value_minor
        ),
        duty_rate_percent=(
            standard_duty_rate_percent
        ),
        currency=currency,
        basis="CIF",
        preferential_rate_percent=(
            preferential_rate_percent
            if preferential_eligible
            else None
        ),
        provenance=provenance,
    )

    duty_rate_used = duty[
        "duty_rate_percent"
    ]

    # Safety invariant:
    #
    # The preferential-rate engine and duty engine
    # must agree about the effective rate.

    if duty_rate_used != effective_duty_rate:
        raise LandedCostCalculationError(
            "Duty rate mismatch between preferential-rate "
            "calculation and duty calculation"
        )

    duty_minor = duty[
        "duty_minor"
    ]

    # --------------------------------------------------------
    # 6. Calculate import tax
    # --------------------------------------------------------

    tax = calculate_import_tax(
        customs_value_minor=(
            customs_value_minor
        ),
        duty_minor=duty_minor,
        tax_rate_percent=(
            tax_rate_percent
        ),
        currency=currency,
        destination_country=(
            destination_country
        ),
        include_duty_in_tax_base=(
            include_duty_in_tax_base
        ),
        additional_tax_base_minor=(
            additional_tax_base_minor
        ),
        provenance=provenance,
    )

    tax_minor = tax[
        "tax_minor"
    ]

    # --------------------------------------------------------
    # 7. Calculate country / customs fees
    # --------------------------------------------------------

    fees = calculate_country_fees(
        country_code=destination_country,
        fee_components=(
            fee_components or []
        ),
        currency=currency,
    )

    country_fees_minor = fees[
        "total_fee_minor"
    ]

    # --------------------------------------------------------
    # 8. Calculate pre-platform total
    # --------------------------------------------------------
    #
    # This is the total cost before the platform's own fee.
    #
    # Product
    # + Shipping
    # + Insurance
    # + Other additions
    # + Duty
    # + Tax
    # + Country fees

    pre_platform_total_minor = (
        product_value_minor
        + shipping_cost_minor
        + insurance_minor
        + other_additions_minor
        + duty_minor
        + tax_minor
        + country_fees_minor
    )

    # --------------------------------------------------------
    # 9. Calculate platform fee
    # --------------------------------------------------------
    #
    # Current business rule:
    #
    # Platform fee is calculated on the complete
    # pre-platform landed cost.
    #
    # Percentage platform fee:
    #
    #     pre_platform_total × rate / 100
    #
    # Plus optional fixed platform fee.

    platform_fee = calculate_platform_fee(
        fee_base_minor=(
            pre_platform_total_minor
        ),
        rate_percent=(
            platform_fee_rate_percent
        ),
        fixed_fee_minor=(
            platform_fixed_fee_minor
        ),
        currency=currency,
        fee_type="PLATFORM_FEE",
        provenance=provenance,
    )

    platform_fee_minor = platform_fee[
        "total_fee_minor"
    ]

    # --------------------------------------------------------
    # 10. Calculate final landed cost
    # --------------------------------------------------------

    landed_cost_minor = (
        pre_platform_total_minor
        + platform_fee_minor
    )

    # --------------------------------------------------------
    # 11. Build structured result
    # --------------------------------------------------------

    return {
        "currency": currency,

        "destination_country": (
            destination_country
        ),

        # Original commercial value
        "product_value_minor": (
            product_value_minor
        ),

        # Shipping chosen by the optimization layer
        "shipping_cost_minor": (
            shipping_cost_minor
        ),

        # Insurance
        "insurance_minor": (
            insurance_minor
        ),

        # Other additions included in customs valuation
        "other_additions_minor": (
            other_additions_minor
        ),

        # Customs calculation
        "customs_value": customs_value,

        # Preferential-rate decision
        "preferential": preferential,

        # Import duty
        "duty": duty,

        # Import tax
        "tax": tax,

        # Destination-country fees
        "fees": fees,

        # Platform fee
        "platform_fee": platform_fee,

        # Total before platform fee
        "pre_platform_total_minor": (
            pre_platform_total_minor
        ),

        # Final amount
        "landed_cost_minor": (
            landed_cost_minor
        ),

        # Data provenance
        "provenance": provenance or {},
    }