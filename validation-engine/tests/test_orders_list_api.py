"""GET /orders — pagination, seller/status filters, and validated-order findability.

Pins: the list envelope {orders, total, limit, offset}; the limit cap
(>200 is a 422); seller/status filters return only matching rows; an order
created via POST /validate is findable through its seller filter.  Tests run
against the live seeded DB — every created order is deleted at teardown.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)

SELLER_ID = "dc777c25-9f68-47d4-ba6b-959a14387d90"
BUYER_ID = "197e1aa3-8799-404d-b983-111b2108dd1e"


def _marker() -> str:
    return f"TEST-{uuid.uuid4().hex[:8]}"


def _payload(**overrides: object) -> dict:
    payload: dict = {
        "seller_id": SELLER_ID,
        "buyer_id": BUYER_ID,
        "destination_country": "US",
        "value_minor": 200000,
        "consignee": "Jane Doe, 123 Main St",
        "net_weight_g": 400,
        "gross_weight_g": 400,
        "article_id": _marker(),
        "line_items": [
            {
                "category_slug": "jute-products",
                "quantity": 2,
                "weight_g": 400,
                "hs_code": "5310",
                "value_minor": 200000,
            }
        ],
    }
    payload.update(overrides)
    return payload


def test_list_returns_paginated_envelope() -> None:
    response = client.get("/orders?limit=2")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"orders", "total", "limit", "offset"}
    assert body["limit"] == 2
    assert body["offset"] == 0
    assert len(body["orders"]) <= 2


def test_list_rejects_limit_over_cap() -> None:
    response = client.get("/orders?limit=1000")
    assert response.status_code == 422


def test_list_filters_by_seller(order_cleanup) -> None:
    order_id = client.post("/validate", json=_payload()).json()["order_id"]
    order_cleanup.append(order_id)

    response = client.get(f"/orders?seller_id={SELLER_ID}")
    assert response.status_code == 200
    orders = response.json()["orders"]
    assert {o["id"] for o in orders} >= {order_id}
    assert all(o["seller_id"] == SELLER_ID for o in orders)


def test_list_filters_by_status(order_cleanup) -> None:
    order_id = client.post("/validate", json=_payload()).json()["order_id"]
    order_cleanup.append(order_id)

    response = client.get("/orders?status=quote_accepted")
    assert response.status_code == 200
    orders = response.json()["orders"]
    assert {o["id"] for o in orders} >= {order_id}
    assert all(o["status"] == "quote_accepted" for o in orders)


def test_validated_order_findable_by_seller(order_cleanup) -> None:
    created = client.post("/validate", json=_payload())
    assert created.status_code == 200
    order_id = created.json()["order_id"]
    assert order_id
    order_cleanup.append(order_id)

    response = client.get(f"/orders?seller_id={SELLER_ID}&limit=200")
    assert response.status_code == 200
    ids = {o["id"] for o in response.json()["orders"]}
    assert order_id in ids
