import pytest
from pydantic import ValidationError

from app.schemas import PricingRequest


def _valid_request() -> dict:
    return {
        "destination_country": "US",
        "optimization_mode": "CHEAPEST",
        "items": [
            {
                "item_id": "item-1",
                "category_slug": "jute-products",
                "quantity": 2,
                "unit_weight_g": 500,
                "dimensions_cm": {
                    "length_cm": "20",
                    "width_cm": "15",
                    "height_cm": "5",
                },
                "unit_value": {
                    "amount_minor": 125000,
                    "currency": "INR",
                },
                "splittable": True,
            }
        ],
    }


def test_pricing_request_accepts_valid_payload() -> None:
    request = PricingRequest.model_validate(_valid_request())

    assert request.destination_country == "US"
    assert request.optimization_mode == "CHEAPEST"
    assert request.items[0].quantity == 2
    assert request.items[0].unit_weight_g == 500


def test_pricing_request_rejects_unknown_fields() -> None:
    payload = _valid_request()
    payload["unexpected"] = "not allowed"

    with pytest.raises(ValidationError):
        PricingRequest.model_validate(payload)


def test_pricing_request_rejects_empty_items() -> None:
    payload = _valid_request()
    payload["items"] = []

    with pytest.raises(ValidationError):
        PricingRequest.model_validate(payload)


def test_pricing_request_rejects_negative_weight() -> None:
    payload = _valid_request()
    payload["items"][0]["unit_weight_g"] = -1

    with pytest.raises(ValidationError):
        PricingRequest.model_validate(payload)


def test_pricing_request_rejects_zero_quantity() -> None:
    payload = _valid_request()
    payload["items"][0]["quantity"] = 0

    with pytest.raises(ValidationError):
        PricingRequest.model_validate(payload)


def test_pricing_request_rejects_invalid_dimensions() -> None:
    payload = _valid_request()
    payload["items"][0]["dimensions_cm"]["length_cm"] = "0"

    with pytest.raises(ValidationError):
        PricingRequest.model_validate(payload)


def test_pricing_request_rejects_invalid_country_code() -> None:
    payload = _valid_request()
    payload["destination_country"] = "USA"

    with pytest.raises(ValidationError):
        PricingRequest.model_validate(payload)


def test_pricing_request_rejects_invalid_currency() -> None:
    payload = _valid_request()
    payload["items"][0]["unit_value"]["currency"] = "inr"

    with pytest.raises(ValidationError):
        PricingRequest.model_validate(payload)


def test_pricing_request_rejects_invalid_optimization_mode() -> None:
    payload = _valid_request()
    payload["optimization_mode"] = "CHEAP"

    with pytest.raises(ValidationError):
        PricingRequest.model_validate(payload)