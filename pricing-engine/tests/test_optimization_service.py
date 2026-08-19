from decimal import Decimal

import pytest

from app.optimization_models import (
    LaneOption,
    OptimizationItem,
)
from app.optimization_objectives import OptimizationMode
from app.optimization_service import (
    OptimizationServiceError,
    optimize_order,
)
from app.packaging import Package


def make_item(
    item_id: str = "ITEM-1",
    quantity: int = 1,
    weight_g: int = 1000,
    splittable: bool = True,
) -> OptimizationItem:
    return OptimizationItem(
        item_id=item_id,
        quantity=quantity,
        unit_weight_g=weight_g,
        splittable=splittable,
        length_cm=Decimal("10"),
        width_cm=Decimal("10"),
        height_cm=Decimal("10"),
    )


def make_package() -> Package:
    return Package(
        package_id="BOX-1",
        name="Standard box",
        tare_weight_g=100,
        length_cm=Decimal("20"),
        width_cm=Decimal("20"),
        height_cm=Decimal("20"),
        cost_minor=50,
        max_product_weight_g=5000,
    )


def make_itps_lane() -> LaneOption:
    return LaneOption(
        name="ITPS",
        lane_data={
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
        },
    )


def make_ems_lane() -> LaneOption:
    return LaneOption(
        name="EMS",
        lane_data={
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
        },
    )


def make_landed_cost() -> dict:
    return {
        "destination_country": "US",
        "currency": "INR",
        "product_value_minor": 10000,
        "insurance_minor": 0,
        "other_additions_minor": 0,
        "standard_duty_rate_percent": Decimal("10"),
        "tax_rate_percent": Decimal("18"),
        "include_duty_in_tax_base": True,
        "additional_tax_base_minor": 0,
        "preferential_eligible": False,
        "preferential_rate_percent": None,
        "preferential_agreement": None,
        "preferential_reason": None,
        "country_fee_components": [],
        "platform_fee_rate_percent": Decimal("0"),
        "platform_fixed_fee_minor": 0,
    }


def test_optimize_order_returns_structured_result():
    result = optimize_order(
        items=[
            make_item()
        ],
        packages=[
            make_package()
        ],
        lanes=[
            make_itps_lane(),
            make_ems_lane(),
        ],
        landed_cost=make_landed_cost(),
    )

    assert result["status"] == "OPTIMAL"

    assert result[
        "optimization_mode"
    ] == "CHEAPEST"

    assert "shipment" in result
    assert "cost" in result
    assert "lane_breakdown" in result
    assert "estimated_transit" in result
    assert "parcels" in result


def test_optimize_order_accepts_string_mode():
    result = optimize_order(
        items=[
            make_item()
        ],
        packages=[
            make_package()
        ],
        lanes=[
            make_itps_lane(),
            make_ems_lane(),
        ],
        optimization_mode="FASTEST",
        landed_cost=make_landed_cost(),
    )

    assert result[
        "optimization_mode"
    ] == "FASTEST"


def test_optimize_order_returns_weight_breakdown():
    result = optimize_order(
        items=[
            make_item(
                weight_g=1000
            )
        ],
        packages=[
            make_package()
        ],
        lanes=[
            make_itps_lane()
        ],
        landed_cost=make_landed_cost(),
    )

    assert (
        result["shipment"]["product_weight_g"]
        == 1000
    )

    assert (
        result["shipment"]["packaging_weight_g"]
        == 100
    )

    assert (
        result["shipment"]["actual_weight_g"]
        == 1100
    )


def test_optimize_order_returns_cost_breakdown():
    result = optimize_order(
        items=[
            make_item()
        ],
        packages=[
            make_package()
        ],
        lanes=[
            make_itps_lane()
        ],
        landed_cost=make_landed_cost(),
    )

    cost = result["cost"]

    assert cost[
        "shipping_cost_minor"
    ] > 0

    assert cost[
        "packaging_cost_minor"
    ] == 50

    assert (
        cost["total_cost_minor"]
        ==
        cost["shipping_cost_minor"]
        + cost["packaging_cost_minor"]
    )


def test_optimize_order_returns_lane_breakdown():
    result = optimize_order(
        items=[
            make_item()
        ],
        packages=[
            make_package()
        ],
        lanes=[
            make_itps_lane(),
            make_ems_lane(),
        ],
        landed_cost=make_landed_cost(),
    )

    assert sum(
        result["lane_breakdown"].values()
    ) == result["shipment"]["parcel_count"]


def test_empty_items_are_rejected():
    with pytest.raises(
        OptimizationServiceError,
        match="At least one item is required",
    ):
        optimize_order(
            items=[],
            packages=[
                make_package()
            ],
            lanes=[
                make_itps_lane()
            ],
        )


def test_empty_packages_are_rejected():
    with pytest.raises(
        OptimizationServiceError,
        match="At least one package",
    ):
        optimize_order(
            items=[
                make_item()
            ],
            packages=[],
            lanes=[
                make_itps_lane()
            ],
        )


def test_empty_lanes_are_rejected():
    with pytest.raises(
        OptimizationServiceError,
        match="At least one shipping lane",
    ):
        optimize_order(
            items=[
                make_item()
            ],
            packages=[
                make_package()
            ],
            lanes=[],
        )


def test_duplicate_item_ids_are_rejected():
    items = [
        make_item(
            item_id="ITEM-1"
        ),
        make_item(
            item_id="ITEM-1"
        ),
    ]

    with pytest.raises(
        OptimizationServiceError,
        match="Duplicate item ID",
    ):
        optimize_order(
            items=items,
            packages=[
                make_package()
            ],
            lanes=[
                make_itps_lane()
            ],
        )


def test_invalid_quantity_is_rejected():
    items = [
        make_item(
            quantity=0
        )
    ]

    with pytest.raises(
        OptimizationServiceError,
        match="Quantity must be greater than zero",
    ):
        optimize_order(
            items=items,
            packages=[
                make_package()
            ],
            lanes=[
                make_itps_lane()
            ],
        )


def test_invalid_weight_is_rejected():
    items = [
        make_item(
            weight_g=0
        )
    ]

    with pytest.raises(
        OptimizationServiceError,
        match="Unit weight must be greater than zero",
    ):
        optimize_order(
            items=items,
            packages=[
                make_package()
            ],
            lanes=[
                make_itps_lane()
            ],
        )


def test_invalid_max_parcels_is_rejected():
    with pytest.raises(
        OptimizationServiceError,
        match="max_parcels must be greater than zero",
    ):
        optimize_order(
            items=[
                make_item()
            ],
            packages=[
                make_package()
            ],
            lanes=[
                make_itps_lane()
            ],
            max_parcels=0,
        )


def test_invalid_optimization_mode_is_rejected():
    with pytest.raises(
        OptimizationServiceError,
        match="Unsupported optimization mode",
    ):
        optimize_order(
            items=[
                make_item()
            ],
            packages=[
                make_package()
            ],
            lanes=[
                make_itps_lane()
            ],
            optimization_mode="INVALID",
        )