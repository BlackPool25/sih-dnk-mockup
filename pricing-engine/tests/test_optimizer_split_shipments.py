from decimal import Decimal

from app.optimization_models import (
    LaneOption,
    OptimizationItem,
)
from app.optimization_objectives import OptimizationMode
from app.optimizer import optimize_shipment
from app.packaging import Package


def make_package() -> Package:
    """
    Standard package used for the optimization tests.

    Packaging weight is deliberately included because shipping
    calculations must use:

        product weight + packaging weight
    """

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
    """
    Test ITPS pricing.

    Weight cap:
        5000g

    First slab:
        100 INR for first 50g

    Additional slabs:
        20 INR per additional 50g
    """

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
    """
    Test EMS pricing.

    Weight cap:
        20000g

    Volumetric divisor:
        5000

    EMS is intentionally made more expensive for this
    test so that the optimizer has a meaningful choice.
    """

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


def make_item(
    item_id: str,
    weight_g: int,
    quantity: int = 1,
    splittable: bool = False,
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


def test_six_kg_order_can_be_split_between_itps_and_ems():
    """
    Core business scenario.

    Order:

        Item A = 4kg
        Item B = 2kg

    Both items are individually non-splittable.

    Therefore the optimizer may choose:

        6kg EMS

    OR:

        4kg ITPS + 2kg EMS

    OR another valid combination.

    The optimizer must not split the 4kg item itself.
    """

    items = [
        make_item(
            item_id="ITEM-A",
            weight_g=4000,
            splittable=False,
        ),
        make_item(
            item_id="ITEM-B",
            weight_g=2000,
            splittable=False,
        ),
    ]

    result = optimize_shipment(
        items=items,
        packages=[make_package()],
        lanes=[
            make_itps_lane(),
            make_ems_lane(),
        ],
        optimization_mode=OptimizationMode.CHEAPEST,
        max_parcels=2,
    )

    assert result["status"] == "OPTIMAL"

    assert result["optimization_mode"] == "CHEAPEST"

    assert result["parcel_count"] >= 1

    assert result["total_cost_minor"] > 0

    # --------------------------------------------------------
    # Every item must appear exactly once.
    # --------------------------------------------------------

    assigned_quantities: dict[str, int] = {}

    for parcel in result["parcels"]:
        for item_id, quantity in parcel[
            "item_quantities"
        ].items():
            assigned_quantities[item_id] = (
                assigned_quantities.get(item_id, 0)
                + quantity
            )

    assert assigned_quantities == {
        "ITEM-A": 1,
        "ITEM-B": 1,
    }


def test_non_splittable_four_kg_item_is_not_split():
    """
    Verify that the 4kg item remains together.

    The optimizer must never return:

        ITEM-A → 2kg + 2kg

    because ITEM-A is non-splittable.
    """

    items = [
        make_item(
            item_id="ITEM-A",
            weight_g=4000,
            splittable=False,
        ),
        make_item(
            item_id="ITEM-B",
            weight_g=2000,
            splittable=False,
        ),
    ]

    result = optimize_shipment(
        items=items,
        packages=[make_package()],
        lanes=[
            make_itps_lane(),
            make_ems_lane(),
        ],
        optimization_mode=OptimizationMode.CHEAPEST,
        max_parcels=2,
    )

    item_a_parcels = []

    for parcel in result["parcels"]:
        quantity = parcel[
            "item_quantities"
        ].get("ITEM-A", 0)

        if quantity > 0:
            item_a_parcels.append(
                (
                    quantity,
                    parcel["product_weight_g"],
                )
            )

    assert len(item_a_parcels) == 1

    assert item_a_parcels[0][0] == 1

    assert item_a_parcels[0][1] >= 4000


def test_packaging_weight_is_included_in_each_parcel():
    """
    Verify packaging weight independently for every parcel.

    If two parcels are used:

        Parcel 1 packaging = 100g
        Parcel 2 packaging = 100g

    Therefore total packaging weight is 200g.
    """

    items = [
        make_item(
            item_id="ITEM-A",
            weight_g=4000,
            splittable=False,
        ),
        make_item(
            item_id="ITEM-B",
            weight_g=2000,
            splittable=False,
        ),
    ]

    result = optimize_shipment(
        items=items,
        packages=[make_package()],
        lanes=[
            make_itps_lane(),
            make_ems_lane(),
        ],
        optimization_mode=OptimizationMode.CHEAPEST,
        max_parcels=2,
    )

    total_product_weight = sum(
        parcel["product_weight_g"]
        for parcel in result["parcels"]
    )

    total_packaging_weight = sum(
        parcel["packaging_weight_g"]
        for parcel in result["parcels"]
    )

    total_actual_weight = sum(
        parcel["actual_weight_g"]
        for parcel in result["parcels"]
    )

    assert total_product_weight == 6000

    assert total_packaging_weight == (
        result["parcel_count"] * 100
    )

    assert total_actual_weight == (
        total_product_weight
        + total_packaging_weight
    )


def test_each_itps_parcel_stays_within_weight_cap():
    """
    Every selected ITPS parcel must remain within its
    5000g actual-weight cap.

    This is important because packaging weight is part of
    actual weight.
    """

    items = [
        make_item(
            item_id="ITEM-A",
            weight_g=4000,
            splittable=False,
        ),
        make_item(
            item_id="ITEM-B",
            weight_g=2000,
            splittable=False,
        ),
    ]

    result = optimize_shipment(
        items=items,
        packages=[make_package()],
        lanes=[
            make_itps_lane(),
            make_ems_lane(),
        ],
        optimization_mode=OptimizationMode.CHEAPEST,
        max_parcels=2,
    )

    for parcel in result["parcels"]:
        if parcel["lane"] == "ITPS":
            assert parcel["actual_weight_g"] <= 5000


def test_selected_parcels_have_complete_cost_breakdown():
    """
    Every parcel must expose enough information for the
    eventual API response.
    """

    items = [
        make_item(
            item_id="ITEM-A",
            weight_g=4000,
            splittable=False,
        ),
        make_item(
            item_id="ITEM-B",
            weight_g=2000,
            splittable=False,
        ),
    ]

    result = optimize_shipment(
        items=items,
        packages=[make_package()],
        lanes=[
            make_itps_lane(),
            make_ems_lane(),
        ],
        optimization_mode=OptimizationMode.CHEAPEST,
        max_parcels=2,
    )

    required_fields = {
        "parcel_id",
        "lane",
        "package_id",
        "item_quantities",
        "product_weight_g",
        "packaging_weight_g",
        "actual_weight_g",
        "volumetric_weight_g",
        "chargeable_weight_g",
        "shipping_cost_minor",
        "packaging_cost_minor",
        "total_cost_minor",
        "transit_min_days",
        "transit_max_days",
        "objective_value",
    }

    for parcel in result["parcels"]:
        assert required_fields.issubset(
            parcel.keys()
        )


def test_total_cost_equals_sum_of_parcel_costs():
    """
    Verify that the final optimization total equals the
    sum of the selected parcel costs.
    """

    items = [
        make_item(
            item_id="ITEM-A",
            weight_g=4000,
            splittable=False,
        ),
        make_item(
            item_id="ITEM-B",
            weight_g=2000,
            splittable=False,
        ),
    ]

    result = optimize_shipment(
        items=items,
        packages=[make_package()],
        lanes=[
            make_itps_lane(),
            make_ems_lane(),
        ],
        optimization_mode=OptimizationMode.CHEAPEST,
        max_parcels=2,
    )

    parcel_total = sum(
        parcel["total_cost_minor"]
        for parcel in result["parcels"]
    )

    assert result["total_cost_minor"] == parcel_total