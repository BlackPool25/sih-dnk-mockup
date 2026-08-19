from decimal import Decimal

from fastapi.testclient import TestClient

from main import app


client = TestClient(app)


def valid_request() -> dict:
    return {
        "items": [
            {
                "item_id": "ITEM-1",
                "quantity": 1,
                "unit_weight_g": 1000,
                "splittable": True,
                "length_cm": 10,
                "width_cm": 10,
                "height_cm": 10,
            }
        ],
        "packages": [
            {
                "package_id": "BOX-1",
                "name": "Standard Box",
                "tare_weight_g": 100,
                "length_cm": 20,
                "width_cm": 20,
                "height_cm": 20,
                "cost_minor": 50,
                "max_product_weight_g": 5000,
            }
        ],
        "lanes": [
            {
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
            },
            {
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
            },
        ],
        "optimization_mode": "CHEAPEST",
        "max_parcels": 2,
    }


def test_health_endpoint():
    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok"
    }


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200

    body = response.json()

    assert body["service"] == "pricing-engine"
    assert body["status"] == "ok"


def test_pricing_endpoint():
    response = client.post(
        "/pricing",
        json=valid_request(),
    )

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "OPTIMAL"

    assert body[
        "optimization_mode"
    ] == "CHEAPEST"

    assert "shipment" in body
    assert "cost" in body
    assert "lane_breakdown" in body
    assert "estimated_transit" in body
    assert "parcels" in body


def test_pricing_returns_weight_breakdown():
    response = client.post(
        "/pricing",
        json=valid_request(),
    )

    assert response.status_code == 200

    body = response.json()

    shipment = body["shipment"]

    assert shipment[
        "product_weight_g"
    ] == 1000

    assert shipment[
        "packaging_weight_g"
    ] == 100

    assert shipment[
        "actual_weight_g"
    ] == 1100


def test_pricing_returns_cost_breakdown():
    response = client.post(
        "/pricing",
        json=valid_request(),
    )

    assert response.status_code == 200

    body = response.json()

    cost = body["cost"]

    assert cost[
        "shipping_cost_minor"
    ] > 0

    assert cost[
        "packaging_cost_minor"
    ] == 50

    assert cost[
        "total_cost_minor"
    ] == (
        cost["shipping_cost_minor"]
        + cost["packaging_cost_minor"]
    )


def test_pricing_returns_parcel_details():
    response = client.post(
        "/pricing",
        json=valid_request(),
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body["parcels"]) >= 1

    parcel = body["parcels"][0]

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

    assert required_fields.issubset(
        parcel.keys()
    )


def test_pricing_fastest_mode():
    request = valid_request()

    request[
        "optimization_mode"
    ] = "FASTEST"

    response = client.post(
        "/pricing",
        json=request,
    )

    assert response.status_code == 200

    body = response.json()

    assert body[
        "optimization_mode"
    ] == "FASTEST"


def test_pricing_balanced_mode():
    request = valid_request()

    request[
        "optimization_mode"
    ] = "BALANCED"

    response = client.post(
        "/pricing",
        json=request,
    )

    assert response.status_code == 200

    body = response.json()

    assert body[
        "optimization_mode"
    ] == "BALANCED"


def test_invalid_optimization_mode_is_rejected():
    request = valid_request()

    request[
        "optimization_mode"
    ] = "INVALID"

    response = client.post(
        "/pricing",
        json=request,
    )

    assert response.status_code == 422


def test_missing_items_is_rejected():
    request = valid_request()

    del request["items"]

    response = client.post(
        "/pricing",
        json=request,
    )

    assert response.status_code == 422


def test_empty_items_is_rejected():
    request = valid_request()

    request["items"] = []

    response = client.post(
        "/pricing",
        json=request,
    )

    assert response.status_code == 422


def test_zero_weight_is_rejected():
    request = valid_request()

    request["items"][0][
        "unit_weight_g"
    ] = 0

    response = client.post(
        "/pricing",
        json=request,
    )

    assert response.status_code == 422


def test_negative_package_cost_is_rejected():
    request = valid_request()

    request["packages"][0][
        "cost_minor"
    ] = -1

    response = client.post(
        "/pricing",
        json=request,
    )

    assert response.status_code == 422


def test_unknown_request_field_is_rejected():
    request = valid_request()

    request["unexpected"] = "bad"

    response = client.post(
        "/pricing",
        json=request,
    )

    assert response.status_code == 422


def test_duplicate_item_ids_are_rejected():
    request = valid_request()

    second_item = dict(
        request["items"][0]
    )

    second_item["quantity"] = 2

    request["items"].append(
        second_item
    )

    response = client.post(
        "/pricing",
        json=request,
    )

    assert response.status_code == 422


def test_invalid_lane_configuration_is_rejected():
    request = valid_request()

    request["lanes"][0][
        "lane"
    ] = "EMS"

    response = client.post(
        "/pricing",
        json=request,
    )

    assert response.status_code == 422


def test_ems_without_divisor_is_rejected():
    request = valid_request()

    request["lanes"][1][
        "divisor"
    ] = None

    response = client.post(
        "/pricing",
        json=request,
    )

    assert response.status_code == 422


def test_invalid_transit_range_is_rejected():
    request = valid_request()

    request["lanes"][0][
        "transit_min_days"
    ] = 30

    request["lanes"][0][
        "transit_max_days"
    ] = 10

    response = client.post(
        "/pricing",
        json=request,
    )

    assert response.status_code == 422