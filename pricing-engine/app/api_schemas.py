from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class StrictBaseModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class PricingItemRequest(StrictBaseModel):
    item_id: str = Field(min_length=1, max_length=100)
    quantity: int = Field(gt=0, le=10000)
    unit_weight_g: int = Field(gt=0, le=1_000_000)
    splittable: bool
    length_cm: Decimal = Field(gt=0, le=10_000)
    width_cm: Decimal = Field(gt=0, le=10_000)
    height_cm: Decimal = Field(gt=0, le=10_000)

    @field_validator("item_id")
    @classmethod
    def validate_item_id(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("item_id cannot be empty")
        return value


class PackageRequest(StrictBaseModel):
    package_id: str = Field(min_length=1, max_length=100)
    name: str = Field(min_length=1, max_length=200)
    tare_weight_g: int = Field(ge=0, le=100_000)
    length_cm: Decimal = Field(gt=0, le=10_000)
    width_cm: Decimal = Field(gt=0, le=10_000)
    height_cm: Decimal = Field(gt=0, le=10_000)
    cost_minor: int = Field(ge=0, le=100_000_000)
    max_product_weight_g: int | None = Field(default=None, gt=0, le=10_000_000)

    @field_validator("package_id", "name")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be empty")
        return value


class LaneRequest(StrictBaseModel):
    name: Literal["ITPS", "EMS"]
    lane: Literal["ITPS", "EMS"]
    first_slab_g: int = Field(gt=0, le=1_000_000)
    first_slab_rate_minor: int = Field(ge=0, le=100_000_000)
    addl_slab_g: int = Field(gt=0, le=1_000_000)
    addl_slab_rate_minor: int = Field(ge=0, le=100_000_000)
    weight_cap_g: int | None = Field(default=None, gt=0, le=100_000_000)
    volume_free: bool
    divisor: int | None = Field(default=None, gt=0, le=100_000_000)
    transit_min_days: int | None = Field(default=None, ge=0, le=3650)
    transit_max_days: int | None = Field(default=None, ge=0, le=3650)
    provenance: dict[str, str] = Field(default_factory=dict)

    @field_validator("lane")
    @classmethod
    def lane_matches_name(cls, value: Literal["ITPS", "EMS"], info):
        name = info.data.get("name")
        if name is not None and value != name:
            raise ValueError("lane must match name")
        return value

    @field_validator("transit_max_days")
    @classmethod
    def validate_transit_range(cls, value: int | None, info):
        minimum = info.data.get("transit_min_days")
        if value is not None and minimum is not None and value < minimum:
            raise ValueError("transit_max_days must be greater than or equal to transit_min_days")
        return value

    @field_validator("divisor")
    @classmethod
    def validate_ems_divisor(cls, value: int | None, info):
        if info.data.get("lane") == "EMS" and value is None:
            raise ValueError("EMS requires a volumetric divisor")
        return value


class LandedCostRequest(StrictBaseModel):
    destination_country: str = Field(min_length=2, max_length=2)
    currency: str = Field(min_length=3, max_length=3)
    product_value_minor: int = Field(ge=0, le=100_000_000_000)
    insurance_minor: int = Field(default=0, ge=0, le=100_000_000_000)
    other_additions_minor: int = Field(default=0, ge=0, le=100_000_000_000)
    standard_duty_rate_percent: Decimal = Field(ge=0, le=100)
    tax_rate_percent: Decimal = Field(ge=0, le=100)
    include_duty_in_tax_base: bool = True
    additional_tax_base_minor: int = Field(default=0, ge=0, le=100_000_000_000)
    preferential_eligible: bool = False
    preferential_rate_percent: Decimal | None = Field(default=None, ge=0, le=100)
    preferential_agreement: str | None = Field(default=None, max_length=200)
    preferential_reason: str | None = Field(default=None, max_length=500)
    country_fee_components: list[dict] = Field(default_factory=list, max_length=50)
    platform_fee_rate_percent: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    platform_fixed_fee_minor: int = Field(default=0, ge=0, le=100_000_000_000)

    @field_validator("destination_country")
    @classmethod
    def validate_destination_country(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 2 or not value.isalpha():
            raise ValueError("destination_country must be a 2-letter country code")
        return value

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("currency must be a 3-letter currency code")
        return value

    @field_validator("preferential_agreement", "preferential_reason")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class PricingRequest(StrictBaseModel):
    items: list[PricingItemRequest] = Field(min_length=1, max_length=100)
    packages: list[PackageRequest] = Field(min_length=1, max_length=50)
    lanes: list[LaneRequest] = Field(min_length=1, max_length=10)
    optimization_mode: Literal["CHEAPEST", "FASTEST", "BALANCED"] = "CHEAPEST"
    max_parcels: int | None = Field(default=None, gt=0, le=100)
    landed_cost: LandedCostRequest | None = None

    @field_validator("items")
    @classmethod
    def validate_unique_item_ids(cls, value):
        ids = [item.item_id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError("item_id values must be unique")
        return value

    @field_validator("packages")
    @classmethod
    def validate_unique_package_ids(cls, value):
        ids = [package.package_id for package in value]
        if len(ids) != len(set(ids)):
            raise ValueError("package_id values must be unique")
        return value

    @field_validator("lanes")
    @classmethod
    def validate_unique_lanes(cls, value):
        names = [lane.name for lane in value]
        if len(names) != len(set(names)):
            raise ValueError("Each shipping lane may appear only once")
        return value


class LegacyDimensionsRequest(StrictBaseModel):
    length_cm: Decimal = Field(gt=0, le=10_000)
    width_cm: Decimal = Field(gt=0, le=10_000)
    height_cm: Decimal = Field(gt=0, le=10_000)


class LegacyUnitValueRequest(StrictBaseModel):
    amount_minor: int = Field(ge=0, le=100_000_000_000)
    currency: str = Field(min_length=3, max_length=3)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if not value:
            raise ValueError("currency cannot be empty")
        return value


class LegacyPricingItemRequest(StrictBaseModel):
    item_id: str = Field(min_length=1, max_length=100)
    category_slug: str = Field(min_length=1, max_length=200)
    quantity: int = Field(gt=0, le=10_000)
    unit_weight_g: int = Field(gt=0, le=1_000_000)
    dimensions_cm: LegacyDimensionsRequest
    unit_value: LegacyUnitValueRequest
    splittable: bool

    @field_validator("item_id", "category_slug")
    @classmethod
    def validate_non_empty_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Value cannot be empty")
        return value


class LegacyPricingRequest(StrictBaseModel):
    destination_country: str = Field(min_length=2, max_length=2)
    optimization_mode: Literal["CHEAPEST", "FASTEST", "BALANCED"]
    items: list[LegacyPricingItemRequest] = Field(min_length=1, max_length=100)

    @field_validator("destination_country")
    @classmethod
    def validate_destination_country(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 2 or not value.isalpha():
            raise ValueError("destination_country must be a 2-letter country code")
        return value

    @field_validator("items")
    @classmethod
    def validate_unique_item_ids(cls, value):
        ids = [item.item_id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError("item_id values must be unique")
        return value


class ParcelResponse(StrictBaseModel):
    parcel_id: str
    lane: Literal["ITPS", "EMS"]
    package_id: str
    item_quantities: dict[str, int]
    product_weight_g: int
    packaging_weight_g: int
    actual_weight_g: int
    volumetric_weight_g: int | None
    chargeable_weight_g: int
    shipping_cost_minor: int
    packaging_cost_minor: int
    total_cost_minor: int
    transit_min_days: int | None
    transit_max_days: int | None
    objective_value: int


class ShipmentBreakdownResponse(StrictBaseModel):
    parcel_count: int
    product_weight_g: int
    packaging_weight_g: int
    actual_weight_g: int


class CostBreakdownResponse(StrictBaseModel):
    shipping_cost_minor: int
    packaging_cost_minor: int
    total_cost_minor: int
    currency: str


class TransitResponse(StrictBaseModel):
    min_days: int | None
    max_days: int | None


class CustomsValueResponse(StrictBaseModel):
    basis: str
    product_value_minor: int
    shipping_cost_minor: int
    insurance_minor: int
    other_additions_minor: int
    customs_value_minor: int
    currency: str
    provenance: dict = Field(default_factory=dict)


class PreferentialResponse(StrictBaseModel):
    eligible: bool
    standard_rate_percent: Decimal
    preferential_rate_percent: Decimal | None
    effective_rate_percent: Decimal
    rate_type: str
    agreement: str | None = None
    reason: str | None = None
    provenance: dict = Field(default_factory=dict)


class DutyResponse(StrictBaseModel):
    customs_value_minor: int
    duty_rate_percent: Decimal
    duty_minor: int
    currency: str
    basis: str
    provenance: dict = Field(default_factory=dict)
    standard_duty_rate_percent: Decimal
    preferential_duty_rate_percent: Decimal | None
    rate_type: str


class TaxResponse(StrictBaseModel):
    tax_type: str
    tax_base_minor: int
    tax_rate_percent: Decimal
    tax_minor: int
    currency: str
    destination_country: str | None
    provenance: dict = Field(default_factory=dict)
    customs_value_minor: int
    duty_minor: int
    include_duty_in_tax_base: bool
    additional_tax_base_minor: int


class FeeComponentResponse(StrictBaseModel):
    fee_type: str
    base_minor: int
    rate_percent: Decimal
    percentage_fee_minor: int
    fixed_fee_minor: int
    total_fee_minor: int
    currency: str
    provenance: dict = Field(default_factory=dict)


class CountryFeesResponse(StrictBaseModel):
    country_code: str
    components: list[FeeComponentResponse]
    total_fee_minor: int
    currency: str


class PlatformFeeResponse(StrictBaseModel):
    fee_type: str
    fee_base_minor: int
    rate_percent: Decimal
    percentage_fee_minor: int
    fixed_fee_minor: int
    total_fee_minor: int
    currency: str
    provenance: dict = Field(default_factory=dict)


class BreakdownLineResponse(StrictBaseModel):
    label: str
    amount_minor: int
    currency: str
    note: str | None = None
    components: dict | None = None


class LandedCostResponse(StrictBaseModel):
    currency: str
    destination_country: str
    product_value_minor: int
    shipping_cost_minor: int
    insurance_minor: int
    other_additions_minor: int
    customs_value: CustomsValueResponse
    preferential: PreferentialResponse
    duty: DutyResponse
    tax: TaxResponse
    fees: CountryFeesResponse
    platform_fee: PlatformFeeResponse
    pre_platform_total_minor: int
    landed_cost_minor: int
    dnk_fees_minor: int | None = None
    customs_minor: int | None = None
    seller_receivable_minor: int | None = None
    buyer_total_minor: int | None = None
    breakdown: list[BreakdownLineResponse] | None = None
    disclaimer: str | None = None
    provenance: dict = Field(default_factory=dict)


class PricingResponse(StrictBaseModel):
    status: Literal["OPTIMAL", "FEASIBLE"]
    optimization_mode: Literal["CHEAPEST", "FASTEST", "BALANCED"]
    shipment: ShipmentBreakdownResponse
    cost: CostBreakdownResponse
    lane_breakdown: dict[Literal["ITPS", "EMS"], int]
    estimated_transit: TransitResponse
    parcels: list[ParcelResponse]
    landed_cost: LandedCostResponse | None = None
