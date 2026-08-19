from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def _valid_payload() -> dict:
    return {
        "destination_country": "US",
        "optimization_mode": "CHEAPEST",
        "items": [
            {
                "item_id": "item-1",
                "category_slug": "jute-products",
                "quantity": 1,
                "unit_weight_g": 500,
                "dimensions_cm": {
                    "length_cm": "20",
                    "width_cm": "15",
                    "height_cm": "5",
                },
                "unit_value": {
                    "amount_minor": 10000,
                    "currency": "INR",
                },
                "splittable": True,
            }
        ],
    }


def test_pricing_calculate_accepts_valid_payload() -> None:
    response = client.post("/pricing/calculate", json=_valid_payload())

    assert response.status_code == 501
    assert response.json()["status"] == "not_implemented"
    assert response.json()["accepted_request"]["destination_country"] == "US"


def test_pricing_calculate_rejects_unknown_top_level_field() -> None:
    payload = _valid_payload()
    payload["unexpected"] = "not allowed"

    response = client.post("/pricing/calculate", json=payload)

    assert response.status_code == 422


def test_pricing_calculate_rejects_empty_items() -> None:
    payload = _valid_payload()
    payload["items"] = []

    response = client.post("/pricing/calculate", json=payload)

    assert response.status_code == 422


def test_pricing_calculate_rejects_invalid_optimization_mode() -> None:
    payload = _valid_payload()
    payload["optimization_mode"] = "CHEAP"

    response = client.post("/pricing/calculate", json=payload)

    assert response.status_code == 422