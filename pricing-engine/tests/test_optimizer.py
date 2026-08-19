from decimal import Decimal

import pytest

from app.optimization_models import LaneOption, OptimizationItem
from app.optimization_objectives import OptimizationMode
from app.optimizer import OptimizationError, optimize_shipment
from app.packaging import Package


def itps_lane() -> LaneOption:
    return LaneOption(name="ITPS", lane_data={"lane": "ITPS", "first_slab_g": 50, "first_slab_rate_minor": 100, "addl_slab_g": 50, "addl_slab_rate_minor": 20, "weight_cap_g": 5000, "volume_free": True, "divisor": None, "transit_min_days": 18, "transit_max_days": 28, "provenance": {}})


def ems_lane() -> LaneOption:
    return LaneOption(name="EMS", lane_data={"lane": "EMS", "first_slab_g": 120, "first_slab_rate_minor": 120, "addl_slab_g": 50, "addl_slab_rate_minor": 30, "weight_cap_g": 20000, "volume_free": False, "divisor": 5000, "transit_min_days": 7, "transit_max_days": 14, "provenance": {}})


def package() -> Package:
    return Package(package_id="BOX-1", name="Standard box", tare_weight_g=100, length_cm=Decimal("20"), width_cm=Decimal("20"), height_cm=Decimal("20"), cost_minor=50, max_product_weight_g=5000)


def make_item(weight_g: int = 1000) -> OptimizationItem:
    return OptimizationItem(item_id="item-1", quantity=1, unit_weight_g=weight_g, splittable=True, length_cm=Decimal("10"), width_cm=Decimal("10"), height_cm=Decimal("10"))


def landed_cost() -> dict:
    return {"destination_country": "US", "currency": "INR", "product_value_minor": 10000, "insurance_minor": 0, "other_additions_minor": 0, "standard_duty_rate_percent": Decimal("10"), "tax_rate_percent": Decimal("18"), "include_duty_in_tax_base": True, "additional_tax_base_minor": 0, "preferential_eligible": False, "preferential_rate_percent": None, "preferential_agreement": None, "preferential_reason": None, "country_fee_components": [], "platform_fee_rate_percent": Decimal("0"), "platform_fixed_fee_minor": 0}


def optimize(mode: OptimizationMode, lanes=None):
    return optimize_shipment(items=[make_item()], packages=[package()], lanes=lanes or [itps_lane(), ems_lane()], optimization_mode=mode, landed_cost=landed_cost())


def test_cheapest_optimizes_final_landed_cost():
    result = optimize(OptimizationMode.CHEAPEST)
    assert result["status"] == "OPTIMAL"
    assert result["optimization_mode"] == "CHEAPEST"
    assert result["landed_cost"]["landed_cost_minor"] > 0
    assert result["landed_cost"]["shipping_cost_minor"] == result["shipping_cost_minor"]


def test_fastest_uses_only_existing_lane_transit_data():
    result = optimize(OptimizationMode.FASTEST)
    assert result["status"] == "OPTIMAL"
    assert result["optimization_mode"] == "FASTEST"
    assert result["estimated_transit_max_days"] == 14
    assert all(parcel["lane"] == "EMS" for parcel in result["parcels"])


def test_balanced_returns_landed_cost_and_transit():
    result = optimize(OptimizationMode.BALANCED)
    assert result["status"] == "OPTIMAL"
    assert result["optimization_mode"] == "BALANCED"
    assert result["landed_cost"]["landed_cost_minor"] > 0
    assert result["estimated_transit_max_days"] in (14, 28)


def test_optimizer_accepts_string_mode():
    result = optimize("CHEAPEST")
    assert result["optimization_mode"] == "CHEAPEST"


def test_optimizer_includes_packaging_weight():
    result = optimize_shipment(items=[make_item(4900)], packages=[package()], lanes=[itps_lane()], optimization_mode=OptimizationMode.CHEAPEST, landed_cost=landed_cost())
    parcel = result["parcels"][0]
    assert parcel["product_weight_g"] == 4900
    assert parcel["packaging_weight_g"] == 100
    assert parcel["actual_weight_g"] == 5000


def test_optimizer_rejects_missing_landed_cost():
    with pytest.raises(OptimizationError):
        optimize_shipment(items=[make_item()], packages=[package()], lanes=[itps_lane(), ems_lane()], optimization_mode=OptimizationMode.CHEAPEST)


def test_final_landed_cost_changes_when_shipping_changes():
    cheap = optimize(OptimizationMode.CHEAPEST, lanes=[itps_lane()])
    fast = optimize(OptimizationMode.FASTEST, lanes=[ems_lane()])
    assert cheap["landed_cost"]["shipping_cost_minor"] == cheap["shipping_cost_minor"]
    assert fast["landed_cost"]["shipping_cost_minor"] == fast["shipping_cost_minor"]
    assert cheap["landed_cost"]["landed_cost_minor"] != fast["landed_cost"]["landed_cost_minor"]


def test_cheapest_accounts_for_packaging_cost():
    expensive_box = Package(package_id="EXPENSIVE", name="Expensive box", tare_weight_g=100, length_cm=Decimal("20"), width_cm=Decimal("20"), height_cm=Decimal("20"), cost_minor=10000, max_product_weight_g=5000)
    cheap_box = package()
    result = optimize_shipment(items=[make_item()], packages=[expensive_box, cheap_box], lanes=[itps_lane()], optimization_mode=OptimizationMode.CHEAPEST, landed_cost=landed_cost())
    assert result["parcels"][0]["package_id"] == "BOX-1"
