"""Pricing assignment + multi-parcel docs/QR — TDD RED→GREEN."""

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
    return f"TEST-{uuid.uuid4().hex[:8]}"


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


def _pricing_2parcels(line_item_ids: list[int] | None = None) -> dict:
    # Use placeholder item ids if not known; real ids are patched per test where needed
    id1 = str(line_item_ids[0]) if line_item_ids and len(line_item_ids) > 0 else "1"
    id2 = str(line_item_ids[1]) if line_item_ids and len(line_item_ids) > 1 else "2"
    return {
        "status": "OPTIMAL",
        "optimization_mode": "CHEAPEST",
        "shipment": {"parcel_count": 2, "product_weight_g": 800, "packaging_weight_g": 200, "actual_weight_g": 1000},
        "cost": {"shipping_cost_minor": 30000, "packaging_cost_minor": 10000, "total_cost_minor": 40000, "currency": "INR"},
        "lane_breakdown": {"ITPS": 15000, "EMS": 15000},
        "estimated_transit": {"min_days": 5, "max_days": 14},
        "parcels": [
            {"parcel_id": "parcel-1", "lane": "ITPS", "package_id": "BOX-STD", "item_quantities": {id1: 2}, "product_weight_g": 400, "packaging_weight_g": 100, "actual_weight_g": 500, "volumetric_weight_g": None, "chargeable_weight_g": 500, "shipping_cost_minor": 15000, "packaging_cost_minor": 5000, "total_cost_minor": 20000, "transit_min_days": 18, "transit_max_days": 28, "objective_value": 15000},
            {"parcel_id": "parcel-2", "lane": "EMS", "package_id": "BOX-STD", "item_quantities": {id2: 1}, "product_weight_g": 400, "packaging_weight_g": 100, "actual_weight_g": 500, "volumetric_weight_g": 1000, "chargeable_weight_g": 1000, "shipping_cost_minor": 15000, "packaging_cost_minor": 5000, "total_cost_minor": 20000, "transit_min_days": 5, "transit_max_days": 14, "objective_value": 15000},
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


def _mock_200(payload: dict):
    mock_resp = MagicMock()
    mock_resp.json.return_value = payload
    mock_resp.raise_for_status.return_value = None
    mock_resp.status_code = 200
    mock_client = MagicMock()
    mock_client.post.return_value = mock_resp
    mock_client.__enter__ = lambda s: s
    mock_client.__exit__ = lambda s, *a: False
    return mock_client


def test_validation_then_pricing_assignment_creates_parcels_and_breakdown(order_cleanup):
    marker = _marker()
    payload_2 = _pricing_2parcels()
    # Patch sync client to return 2-parcel response
    with patch("app.services.pricing_client.httpx.Client", return_value=_mock_200(payload_2)):
        resp = client.post("/validate", json=_ready_payload(article=marker))
        body = resp.json()
        assert body["validation_state"] == "ready"
        order_id = body["order_id"]
        order_cleanup.append(order_id)
        # Check stored pricing on get order
        order_body = client.get(f"/orders/{order_id}").json()["order"]
        assert order_body["pricing_breakdown"] is not None
        assert order_body["parcels"] is not None
        assert len(order_body["parcels"]) == 2
        assert order_body["pricing_breakdown"]["cost"]["currency"] == "INR"
        # GET /orders/{id}/pricing mirrors stored
        pricing = client.get(f"/orders/{order_id}/pricing").json()
        assert pricing["pricing_breakdown"] == order_body["pricing_breakdown"]
        assert len(pricing["parcels"]) == 2


def test_pricing_failure_does_not_block_validation(order_cleanup):
    marker = _marker()
    def _raise(*a, **kw):
        raise httpx.ConnectTimeout("timeout")
    with patch("app.services.pricing_client.httpx.Client") as MockClient:
        inst = MagicMock()
        inst.post.side_effect = httpx.ConnectTimeout("timeout")
        inst.__enter__ = lambda s: s
        inst.__exit__ = lambda s, *a: False
        MockClient.return_value = inst
        resp = client.post("/validate", json=_ready_payload(article=marker))
        body = resp.json()
        assert body["validation_state"] == "ready"
        assert body["status"] == "ready"
        order_id = body["order_id"]
        order_cleanup.append(order_id)
        # pricing_error in last_report, report still ready
        from app.db import SessionLocal
        from app.models.order import Order
        from sqlalchemy import select
        import uuid as _uuid
        with SessionLocal() as s:
            o = s.execute(select(Order).where(Order.id == _uuid.UUID(order_id))).scalar_one()
            assert o.last_report is not None
            assert "pricing_error" in o.last_report
            assert o.pricing_breakdown is None


def test_per_parcel_docs_have_parcel_id(order_cleanup):
    marker = _marker()
    payload_2 = _pricing_2parcels()
    with patch("app.services.pricing_client.httpx.Client", return_value=_mock_200(payload_2)):
        resp = client.post("/validate", json=_ready_payload(article=marker))
        assert resp.json()["validation_state"] == "ready"
        order_id = resp.json()["order_id"]
        order_cleanup.append(order_id)
    # Patch line item ids to match parcels? Use stored parcels ids
    # Generate docs — should fan-out 2 parcels *4 doc types=8 docs
    gen = client.post(f"/docs/generate-all?order_id={order_id}")
    assert gen.status_code == 200
    assert gen.json()["status"] == "complete"
    docs = gen.json()["documents"]
    assert all(d["parcel_id"] in ("parcel-1", "parcel-2") for d in docs)
    assert len(docs) == 8
    # Filter by parcel_id
    filt1 = client.get(f"/orders/{order_id}/documents?parcel_id=parcel-1").json()["documents"]
    assert all(d["parcel_id"] == "parcel-1" for d in filt1)
    assert len(filt1) == 4
    # pdf per parcel
    pdf1 = client.get(f"/orders/{order_id}/pdf?doc_type=INVOICE&parcel_id=parcel-1")
    assert pdf1.status_code == 200
    assert pdf1.headers["content-type"] == "application/pdf"


def test_get_pricing_returns_identical_to_post_pricing(order_cleanup):
    marker = _marker()
    payload_2 = _pricing_2parcels()
    with patch("app.services.pricing_client.httpx.Client", return_value=_mock_200(payload_2)):
        resp = client.post("/validate", json=_ready_payload(article=marker))
        order_id = resp.json()["order_id"]
        order_cleanup.append(order_id)
        pricing = client.get(f"/orders/{order_id}/pricing").json()
        order_body = client.get(f"/orders/{order_id}").json()["order"]
        assert pricing["pricing_breakdown"] == order_body["pricing_breakdown"]
        assert pricing["parcels"] == order_body["parcels"]
        assert pricing["lane_breakdown"] == payload_2["lane_breakdown"]
        assert pricing["cost"] == payload_2["cost"]
        assert pricing["landed_cost"] == payload_2["landed_cost"]


def test_qr_tokens_per_parcel(order_cleanup):
    marker = _marker()
    payload_2 = _pricing_2parcels()
    with patch("app.services.pricing_client.httpx.Client", return_value=_mock_200(payload_2)):
        resp = client.post("/validate", json=_ready_payload(article=marker))
        order_id = resp.json()["order_id"]
        order_cleanup.append(order_id)
    # Issue QR for each parcel
    r1 = client.post(f"/orders/{order_id}/qr-token", json={"jti": "jti-parcel1", "parcel_id": "parcel-1"})
    assert r1.status_code == 200
    assert r1.json()["qr_token_jti"] == "jti-parcel1"
    r2 = client.post(f"/orders/{order_id}/qr-token", json={"jti": "jti-parcel2", "parcel_id": "parcel-2"})
    assert r2.status_code == 200
    order = client.get(f"/orders/{order_id}").json()["order"]
    assert order["qr_token_jti"] == "jti-parcel2"
    assert order["qr_tokens"] is not None
    assert len(order["qr_tokens"]) == 2
    assert {t["parcel_id"] for t in order["qr_tokens"]} == {"parcel-1", "parcel-2"}
    assert {t["jti"] for t in order["qr_tokens"]} == {"jti-parcel1", "jti-parcel2"}
