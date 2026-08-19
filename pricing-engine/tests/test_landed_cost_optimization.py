from decimal import Decimal

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def payload(mode: str = "CHEAPEST") -> dict:
    return {
        "items": [{
            "item_id": "ITEM-1",
            "quantity": 1,
            "unit_weight_g": 1000,
            "splittable": True,
            "length_cm": "10",
            "width_cm": "10",
            "height_cm": "10",
        }],
        "packages": [{
            "package_id": "BOX-1",
            "name": "Standard Box",
            "tare_weight_g": 100,
            "length_cm": "20",
            "width_cm": "20",
            "height_cm": "20",
            "cost_minor": 50,
            "max_product_weight_g": 5000,
        }],
        "lanes": [{
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
        }, {
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
        }],
        "optimization_mode": mode,
        "max_parcels": 2,
        "landed_cost": {
            "destination_country": "US",
            "currency": "INR",
            "product_value_minor": 10000,
            "insurance_minor": 0,
            "other_additions_minor": 0,
            "standard_duty_rate_percent": "10",
            "tax_rate_percent": "18",
            "include_duty_in_tax_base": True,
            "additional_tax_base_minor": 0,
            "preferential_eligible": False,
            "preferential_rate_percent": None,
            "preferential_agreement": None,
            "preferential_reason": None,
            "country_fee_components": [],
            "platform_fee_rate_percent": "0",
            "platform_fixed_fee_minor": 0,
        },
    }


def test_pricing_returns_complete_landed_cost():
    response = client.post("/pricing", json=payload())
    assert response.status_code == 200

    body = response.json()
    assert body["status"] in {"OPTIMAL", "FEASIBLE"}
    assert body["landed_cost"]["landed_cost_minor"] > 0
    assert body["landed_cost"]["shipping_cost_minor"] == body["cost"]["shipping_cost_minor"]
    assert body["landed_cost"]["customs_value"]["customs_value_minor"] > 0
    assert body["landed_cost"]["duty"]["duty_minor"] >= 0
    assert body["landed_cost"]["tax"]["tax_minor"] >= 0


def test_fastest_uses_existing_ems_transit_range():
    response = client.post("/pricing", json=payload("FASTEST"))
    assert response.status_code == 200
    body = response.json()
    assert body["estimated_transit"]["max_days"] == 14
    assert all(parcel["lane"] == "EMS" for parcel in body["parcels"])


def test_only_supplied_lane_data_is_used():
    request = payload()
    request["lanes"][0]["transit_min_days"] = None
    request["lanes"][0]["transit_max_days"] = None
    request["lanes"] = [request["lanes"][0]]

    response = client.post("/pricing", json=request)
    assert response.status_code == 200
    assert response.json()["optimization_mode"] == "CHEAPEST"
