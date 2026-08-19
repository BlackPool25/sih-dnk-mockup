from decimal import Decimal

import pytest
from pydantic import ValidationError

from app.api_schemas import (
    LaneRequest,
    PackageRequest,
    PricingItemRequest,
    PricingRequest,
)


def valid_item() -> dict:
    return {
        "item_id": "ITEM-1",
        "quantity": 1,
        "unit_weight_g": 1000,
        "splittable": True,
        "length_cm": Decimal("10"),
        "width_cm": Decimal("10"),
        "height_cm": Decimal("10"),
    }


def valid_package() -> dict:
    return {
        "package_id": "BOX-1",
        "name": "Standard Box",
        "tare_weight_g": 100,
        "length_cm": Decimal("20"),
        "width_cm": Decimal("20"),
        "height_cm": Decimal("20"),
        "cost_minor": 50,
        "max_product_weight_g": 5000,
    }


def valid_itps_lane() -> dict:
    return {
        "name": "ITPS",
        "lane": "ITPS",
        "first_slab_g": 50,
        "first_slab_rate_minor": 100,
        "addl_slab_g": 50,
        "addl_slab_rate_minor": 20,
        "weight_cap_g": 5000,
        "volume_free": True,
        "divisor": None,
        "transit_min_days": 18,
        "transit_max_days": 28,
        "provenance": {},
    }


def valid_ems_lane() -> dict:
    return {
        "name": "EMS",
        "lane": "EMS",
        "first_slab_g": 120,
        "first_slab_rate_minor": 120,
        "addl_slab_g": 50,
        "addl_slab_rate_minor": 30,
        "weight_cap_g": 20000,
        "volume_free": False,
        "divisor": 5000,
        "transit_min_days": 7,
        "transit_max_days": 14,
        "provenance": {},
    }


def test_valid_item():
    item = PricingItemRequest(
        **valid_item()
    )

    assert item.item_id == "ITEM-1"
    assert item.quantity == 1
    assert item.unit_weight_g == 1000


def test_item_rejects_zero_quantity():
    data = valid_item()
    data["quantity"] = 0

    with pytest.raises(ValidationError):
        PricingItemRequest(**data)


def test_item_rejects_zero_weight():
    data = valid_item()
    data["unit_weight_g"] = 0

    with pytest.raises(ValidationError):
        PricingItemRequest(**data)


def test_item_rejects_extra_field():
    data = valid_item()
    data["unexpected"] = "value"

    with pytest.raises(ValidationError):
        PricingItemRequest(**data)


def test_package_rejects_negative_tare_weight():
    data = valid_package()
    data["tare_weight_g"] = -1

    with pytest.raises(ValidationError):
        PackageRequest(**data)


def test_package_rejects_negative_cost():
    data = valid_package()
    data["cost_minor"] = -1

    with pytest.raises(ValidationError):
        PackageRequest(**data)


def test_itps_lane_is_valid():
    lane = LaneRequest(
        **valid_itps_lane()
    )

    assert lane.name == "ITPS"
    assert lane.lane == "ITPS"


def test_ems_lane_is_valid():
    lane = LaneRequest(
        **valid_ems_lane()
    )

    assert lane.name == "EMS"
    assert lane.lane == "EMS"


def test_lane_name_and_lane_must_match():
    data = valid_itps_lane()
    data["lane"] = "EMS"

    with pytest.raises(ValidationError):
        LaneRequest(**data)


def test_ems_requires_divisor():
    data = valid_ems_lane()
    data["divisor"] = None

    with pytest.raises(ValidationError):
        LaneRequest(**data)


def test_invalid_transit_range_is_rejected():
    data = valid_ems_lane()

    data["transit_min_days"] = 20
    data["transit_max_days"] = 10

    with pytest.raises(ValidationError):
        LaneRequest(**data)


def test_pricing_request_accepts_valid_data():
    request = PricingRequest(
        items=[
            valid_item()
        ],
        packages=[
            valid_package()
        ],
        lanes=[
            valid_itps_lane(),
            valid_ems_lane(),
        ],
        optimization_mode="CHEAPEST",
        max_parcels=2,
    )

    assert len(request.items) == 1
    assert len(request.packages) == 1
    assert len(request.lanes) == 2
    assert request.optimization_mode == "CHEAPEST"


def test_pricing_request_rejects_duplicate_items():
    item1 = valid_item()
    item2 = valid_item()

    item2["quantity"] = 2

    with pytest.raises(ValidationError):
        PricingRequest(
            items=[
                item1,
                item2,
            ],
            packages=[
                valid_package()
            ],
            lanes=[
                valid_itps_lane()
            ],
        )


def test_pricing_request_rejects_duplicate_packages():
    package1 = valid_package()
    package2 = valid_package()

    package2["name"] = "Another Box"

    with pytest.raises(ValidationError):
        PricingRequest(
            items=[
                valid_item()
            ],
            packages=[
                package1,
                package2,
            ],
            lanes=[
                valid_itps_lane()
            ],
        )


def test_pricing_request_rejects_duplicate_lanes():
    lane1 = valid_itps_lane()
    lane2 = valid_itps_lane()

    with pytest.raises(ValidationError):
        PricingRequest(
            items=[
                valid_item()
            ],
            packages=[
                valid_package()
            ],
            lanes=[
                lane1,
                lane2,
            ],
        )


def test_pricing_request_rejects_invalid_mode():
    with pytest.raises(ValidationError):
        PricingRequest(
            items=[
                valid_item()
            ],
            packages=[
                valid_package()
            ],
            lanes=[
                valid_itps_lane()
            ],
            optimization_mode="INVALID",
        )


def test_pricing_request_rejects_extra_field():
    data = {
        "items": [
            valid_item()
        ],
        "packages": [
            valid_package()
        ],
        "lanes": [
            valid_itps_lane()
        ],
        "unknown_field": "bad",
    }

    with pytest.raises(ValidationError):
        PricingRequest(**data)