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
        "first_slab_g": 250,
        "first_slab_rate_minor": 100,
        "addl_slab_g": 250,
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


# ---------------------------------------------------------------------------
# TDD edge 280g — ITPS 50g slabs vs EMS 250g slabs (ceil), plus boundaries
# ---------------------------------------------------------------------------

def _billable_weight_g(lane: dict, additional_slabs: int) -> int:
    return lane["first_slab_g"] + additional_slabs * lane["addl_slab_g"]


def test_shipping_280g_edge():
    """ITPS 280g → 300g billable (50g slabs), EMS 280g → 500g billable (250g slabs)."""
    itps = itps_lane()
    r_itps = calculate_itps(lane=itps, actual_weight_g=280)
    assert r_itps["feasible"] is True
    assert r_itps["actual_weight_g"] == 280
    assert r_itps["chargeable_weight_g"] == 280
    assert r_itps["additional_slabs"] == 5  # ceil((280-50)/50)=5
    assert _billable_weight_g(itps, r_itps["additional_slabs"]) == 300
    assert r_itps["shipping_cost_minor"] == 100 + 5 * 20  # 200

    ems = ems_lane()
    r_ems = calculate_ems(
        lane=ems,
        actual_weight_g=280,
        length_cm=Decimal("10"),
        width_cm=Decimal("10"),
        height_cm=Decimal("10"),
    )
    assert r_ems["feasible"] is True
    assert r_ems["actual_weight_g"] == 280
    assert r_ems["volumetric_weight_g"] == 200
    assert r_ems["chargeable_weight_g"] == 280
    assert r_ems["additional_slabs"] == 1  # ceil((280-250)/250)=1
    assert _billable_weight_g(ems, r_ems["additional_slabs"]) == 500
    assert r_ems["shipping_cost_minor"] == 100 + 1 * 20  # 120


def test_shipping_itps_boundaries():
    itps = itps_lane()
    r50 = calculate_itps(lane=itps, actual_weight_g=50)
    assert r50["additional_slabs"] == 0
    assert _billable_weight_g(itps, r50["additional_slabs"]) == 50
    assert r50["shipping_cost_minor"] == 100

    r51 = calculate_itps(lane=itps, actual_weight_g=51)
    assert r51["additional_slabs"] == 1
    assert _billable_weight_g(itps, r51["additional_slabs"]) == 100
    assert r51["shipping_cost_minor"] == 120

    r100 = calculate_itps(lane=itps, actual_weight_g=100)
    assert r100["additional_slabs"] == 1
    assert _billable_weight_g(itps, r100["additional_slabs"]) == 100


def test_shipping_ems_boundaries():
    ems = ems_lane()
    r250 = calculate_ems(lane=ems, actual_weight_g=250, length_cm=Decimal("10"), width_cm=Decimal("10"), height_cm=Decimal("10"))
    assert r250["additional_slabs"] == 0
    assert _billable_weight_g(ems, r250["additional_slabs"]) == 250
    assert r250["shipping_cost_minor"] == 100
    assert r250["chargeable_weight_g"] == 250

    r251 = calculate_ems(lane=ems, actual_weight_g=251, length_cm=Decimal("10"), width_cm=Decimal("10"), height_cm=Decimal("10"))
    assert r251["additional_slabs"] == 1
    assert _billable_weight_g(ems, r251["additional_slabs"]) == 500
    assert r251["shipping_cost_minor"] == 120

    r500 = calculate_ems(lane=ems, actual_weight_g=500, length_cm=Decimal("10"), width_cm=Decimal("10"), height_cm=Decimal("10"))
    assert r500["additional_slabs"] == 1
    assert _billable_weight_g(ems, r500["additional_slabs"]) == 500
    assert r500["chargeable_weight_g"] == 500
    assert r500["shipping_cost_minor"] == 120

    r501 = calculate_ems(lane=ems, actual_weight_g=501, length_cm=Decimal("10"), width_cm=Decimal("10"), height_cm=Decimal("10"))
    assert r501["additional_slabs"] == 2
    assert _billable_weight_g(ems, r501["additional_slabs"]) == 750
    assert r501["shipping_cost_minor"] == 140


def test_shipping_ems_volumetric_280g_blowup():
    """EMS volumetric dominates: 50x50x30 @ divisor 5000 → 15000g → billable 15000."""
    ems = ems_lane()
    r = calculate_ems(lane=ems, actual_weight_g=280, length_cm=Decimal("50"), width_cm=Decimal("50"), height_cm=Decimal("30"))
    assert r["volumetric_weight_g"] == 15000
    assert r["chargeable_weight_g"] == 15000
    # 15000g → (15000-250)/250=59 → ceil 59 → billable 250+59*250=15000
    assert r["additional_slabs"] == 59
    assert _billable_weight_g(ems, r["additional_slabs"]) == 15000