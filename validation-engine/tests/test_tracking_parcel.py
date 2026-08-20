from __future__ import annotations

import uuid
from unittest.mock import patch, MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)

SELLER_ID = "dc777c25-9f68-47d4-ba6b-959a14387d90"
BUYER_ID = "197e1aa3-8799-404d-b983-111b2108dd1e"


def _marker() -> str:
    return f"TRK-{uuid.uuid4().hex[:8]}"


def _ready_payload(article: str | None = None) -> dict:
    return {
        "seller_id": SELLER_ID,
        "buyer_id": BUYER_ID,
        "destination_country": "US",
        "value_minor": 200000,
        "consignee": "Jane Doe, 123 Main St",
        "net_weight_g": 800,
        "gross_weight_g": 800,
        "article_id": article or _marker(),
        "iec": "0123456789",
        "gstin": "29ABCDE1234F1Z5",
        "exporter_name": "Acme Exporters Pvt Ltd",
        "exporter_address": "42 MG Road, Bengaluru 560001",
        "state_code": "29",
        "line_items": [
            {"category_slug": "jute-products", "quantity": 2, "weight_g": 400, "hs_code": "5310", "value_minor": 100000, "dimensions": {"length_cm": 10, "width_cm": 10, "height_cm": 10}},
            {"category_slug": "small-woodware", "quantity": 1, "weight_g": 400, "hs_code": "4421", "value_minor": 100000, "dimensions": {"length_cm": 12, "width_cm": 12, "height_cm": 12}},
        ],
    }


def _pricing_2parcels() -> dict:
    return {
        "status": "OPTIMAL",
        "optimization_mode": "CHEAPEST",
        "shipment": {"parcel_count": 2, "product_weight_g": 800, "packaging_weight_g": 200, "actual_weight_g": 1000},
        "cost": {"shipping_cost_minor": 30000, "packaging_cost_minor": 10000, "total_cost_minor": 40000, "currency": "INR"},
        "lane_breakdown": {"ITPS": 15000, "EMS": 15000},
        "estimated_transit": {"min_days": 5, "max_days": 14},
        "parcels": [
            {"parcel_id": "parcel-1", "lane": "ITPS", "package_id": "BOX-STD", "item_quantities": {"1": 2}, "product_weight_g": 400, "packaging_weight_g": 100, "actual_weight_g": 500, "volumetric_weight_g": None, "chargeable_weight_g": 500, "shipping_cost_minor": 15000, "packaging_cost_minor": 5000, "total_cost_minor": 20000, "transit_min_days": 18, "transit_max_days": 28, "objective_value": 15000},
            {"parcel_id": "parcel-2", "lane": "EMS", "package_id": "BOX-STD", "item_quantities": {"2": 1}, "product_weight_g": 400, "packaging_weight_g": 100, "actual_weight_g": 500, "volumetric_weight_g": 1000, "chargeable_weight_g": 1000, "shipping_cost_minor": 15000, "packaging_cost_minor": 5000, "total_cost_minor": 20000, "transit_min_days": 5, "transit_max_days": 14, "objective_value": 15000},
        ],
        "landed_cost": {
            "currency": "INR", "destination_country": "US", "product_value_minor": 200000, "shipping_cost_minor": 30000, "insurance_minor": 0, "other_additions_minor": 0,
            "customs_value": {"basis": "CIF", "product_value_minor": 200000, "shipping_cost_minor": 30000, "insurance_minor": 0, "other_additions_minor": 0, "customs_value_minor": 230000, "currency": "INR", "provenance": {}},
            "preferential": {"eligible": False, "standard_rate_percent": "10", "preferential_rate_percent": None, "effective_rate_percent": "10", "rate_type": "STANDARD", "provenance": {}},
            "duty": {"customs_value_minor": 230000, "duty_rate_percent": "10", "duty_minor": 23000, "currency": "INR", "basis": "CIF", "provenance": {}, "standard_duty_rate_percent": "10", "preferential_duty_rate_percent": None, "rate_type": "STANDARD"},
            "tax": {"tax_type": "GST", "tax_base_minor": 253000, "tax_rate_percent": "18", "tax_minor": 45540, "currency": "INR", "destination_country": "US", "provenance": {}, "customs_value_minor": 230000, "duty_minor": 23000, "include_duty_in_tax_base": True, "additional_tax_base_minor": 0},
            "fees": {"country_code": "US", "components": [], "total_fee_minor": 0, "currency": "INR"},
            "platform_fee": {"fee_type": "PLATFORM", "fee_base_minor": 298540, "rate_percent": "0", "percentage_fee_minor": 0, "fixed_fee_minor": 0, "total_fee_minor": 0, "currency": "INR", "provenance": {}},
            "pre_platform_total_minor": 298540, "landed_cost_minor": 298540, "provenance": {},
        },
    }


def _mock_pricing(payload: dict):
    mock_resp = MagicMock()
    mock_resp.json.return_value = payload
    mock_resp.raise_for_status.return_value = None
    mock_resp.status_code = 200
    mock_client = MagicMock()
    mock_client.post.return_value = mock_resp
    mock_client.__enter__ = lambda s: s
    mock_client.__exit__ = lambda s, *a: False
    return mock_client


def test_split_order_registers_N_shipments_idempotent(order_cleanup):
    marker = _marker()
    payload_2 = _pricing_2parcels()
    calls: list[dict] = []

    def fake_post(url, json=None, **kw):
        calls.append(json or {})
        r = MagicMock()
        r.status_code = 200
        r.text = ""
        r.json.return_value = {"tracking_number": json["tracking_number"], "carrier": json["carrier"], "order_id": json["order_id"], "parcel_id": json["parcel_id"]}
        r.raise_for_status.return_value = None
        return r

    mock_tracking = MagicMock()
    mock_tracking.post.side_effect = fake_post
    mock_tracking.__enter__ = lambda s: s
    mock_tracking.__exit__ = lambda s, *a: False

    with patch("app.services.pricing_client.query_optimal_assignment_sync", return_value=payload_2):
        with patch("app.services.tracking_client.httpx.Client", return_value=mock_tracking):
            resp = client.post("/validate", json=_ready_payload(article=marker))
            assert resp.json()["validation_state"] == "ready"
            order_id = resp.json()["order_id"]
            order_cleanup.append(order_id)

    assert len(calls) == 2
    assert {c["parcel_id"] for c in calls} == {"parcel-1", "parcel-2"}
    assert {c["order_id"] for c in calls} == {order_id}
    carriers = {c["parcel_id"]: c["carrier"] for c in calls}
    assert carriers["parcel-1"] == "IndiaPost"
    assert carriers["parcel-2"] == "EMS"

    calls2: list[dict] = []

    def fake_post2(url, json=None, **kw):
        calls2.append(json or {})
        r = MagicMock()
        r.status_code = 200
        r.text = ""
        r.json.return_value = {"tracking_number": json["tracking_number"], "carrier": json["carrier"]}
        r.raise_for_status.return_value = None
        return r

    mock_tracking2 = MagicMock()
    mock_tracking2.post.side_effect = fake_post2
    mock_tracking2.__enter__ = lambda s: s
    mock_tracking2.__exit__ = lambda s, *a: False

    with patch("app.services.tracking_client.httpx.Client", return_value=mock_tracking2):
        resp2 = client.post("/validate", json={"order_id": order_id, "seller_id": SELLER_ID})
        assert resp2.json()["order_id"] == order_id

    assert len(calls2) == 2
