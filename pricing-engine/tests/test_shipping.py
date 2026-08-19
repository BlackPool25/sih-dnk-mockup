from decimal import Decimal

from app.shipping import (
    ShippingCalculationError,
    calculate_ems,
    calculate_itps,
)


def itps_lane(
    weight_cap_g: int = 5000,
) -> dict:
    return {
        "lane": "ITPS",
        "first_slab_g": 50,
        "first_slab_rate_minor": 100,
        "addl_slab_g": 50,
        "addl_slab_rate_minor": 20,
        "weight_cap_g": weight_cap_g,
        "volume_free": True,
        "divisor": None,
        "transit_min_days": 18,
        "transit_max_days": 28,
        "provenance": {},
    }


def ems_lane(
    weight_cap_g: int = 20000,
) -> dict:
    return {
        "lane": "EMS",
        "first_slab_g": 50,
        "first_slab_rate_minor": 100,
        "addl_slab_g": 50,
        "addl_slab_rate_minor": 20,
        "weight_cap_g": weight_cap_g,
        "volume_free": False,
        "divisor": 5000,
        "transit_min_days": 7,
        "transit_max_days": 14,
        "provenance": {},
    }


def test_itps_first_slab():
    result = calculate_itps(
        lane=itps_lane(),
        actual_weight_g=50,
    )

    assert result["feasible"] is True
    assert result["additional_slabs"] == 0
    assert result["chargeable_weight_g"] == 50
    assert result["shipping_cost_minor"] == 100


def test_itps_additional_slab():
    result = calculate_itps(
        lane=itps_lane(),
        actual_weight_g=51,
    )

    assert result["feasible"] is True
    assert result["additional_slabs"] == 1
    assert result["shipping_cost_minor"] == 120


def test_itps_multiple_additional_slabs():
    result = calculate_itps(
        lane=itps_lane(),
        actual_weight_g=151,
    )

    assert result["additional_slabs"] == 3
    assert result["shipping_cost_minor"] == 160


def test_itps_exact_weight_cap():
    result = calculate_itps(
        lane=itps_lane(weight_cap_g=5000),
        actual_weight_g=5000,
    )

    assert result["feasible"] is True


def test_itps_above_weight_cap():
    result = calculate_itps(
        lane=itps_lane(weight_cap_g=5000),
        actual_weight_g=5001,
    )

    assert result["feasible"] is False
    assert result["shipping_cost_minor"] is None


def test_itps_rejects_zero_weight():
    try:
        calculate_itps(
            lane=itps_lane(),
            actual_weight_g=0,
        )
        assert False
    except ShippingCalculationError:
        assert True


def test_ems_uses_actual_weight_when_greater():
    result = calculate_ems(
        lane=ems_lane(),
        actual_weight_g=6000,
        length_cm=Decimal("10"),
        width_cm=Decimal("10"),
        height_cm=Decimal("10"),
    )

    assert result["actual_weight_g"] == 6000
    assert result["volumetric_weight_g"] == 200
    assert result["chargeable_weight_g"] == 6000


def test_ems_uses_volumetric_weight_when_greater():
    result = calculate_ems(
        lane=ems_lane(),
        actual_weight_g=1000,
        length_cm=Decimal("50"),
        width_cm=Decimal("50"),
        height_cm=Decimal("20"),
    )

    assert result["actual_weight_g"] == 1000
    assert result["volumetric_weight_g"] == 10000
    assert result["chargeable_weight_g"] == 10000


def test_ems_exact_weight_cap():
    result = calculate_ems(
        lane=ems_lane(weight_cap_g=10000),
        actual_weight_g=10000,
        length_cm=Decimal("10"),
        width_cm=Decimal("10"),
        height_cm=Decimal("10"),
    )

    assert result["feasible"] is True


def test_ems_above_weight_cap():
    result = calculate_ems(
        lane=ems_lane(weight_cap_g=5000),
        actual_weight_g=1000,
        length_cm=Decimal("50"),
        width_cm=Decimal("50"),
        height_cm=Decimal("20"),
    )

    assert result["feasible"] is False
    assert result["shipping_cost_minor"] is None


def test_ems_rejects_invalid_dimensions():
    try:
        calculate_ems(
            lane=ems_lane(),
            actual_weight_g=1000,
            length_cm=Decimal("0"),
            width_cm=Decimal("20"),
            height_cm=Decimal("20"),
        )
        assert False
    except ShippingCalculationError:
        assert True