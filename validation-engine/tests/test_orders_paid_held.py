from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)

SELLER_ID = "dc777c25-9f68-47d4-ba6b-959a14387d90"
BUYER_ID = "197e1aa3-8799-404d-b983-111b2108dd1e"


def _marker() -> str:
    return f"TEST-PAID-{uuid.uuid4().hex[:8]}"


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


def _create_order(order_cleanup) -> str:
    resp = client.post("/validate", json=_payload())
    assert resp.status_code == 200
    oid = resp.json()["order_id"]
    order_cleanup.append(oid)
    return oid


def test_paid_held_transition(order_cleanup) -> None:
    oid = _create_order(order_cleanup)
    before = client.get(f"/orders/{oid}").json()["order"]["status"]
    assert before == "quote_accepted"
    resp = client.post(f"/orders/{oid}/paid_held", json={"payment_id": "pay_123", "payment_link_id": "plink_456", "event": "payment.captured", "event_id": "evt_1"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "paid_held"
    assert resp.json()["changed"] is True
    after = client.get(f"/orders/{oid}").json()
    assert after["order"]["status"] == "paid_held"
    assert after["order"]["last_report"]["payment"]["payment_id"] == "pay_123"
    assert after["order"]["last_report"]["payment"]["money_location"] == "RAZORPAY_MERCHANT_BALANCE"


def test_paid_held_idempotent_same_key(order_cleanup) -> None:
    oid = _create_order(order_cleanup)
    body = {"payment_id": "pay_dup", "payment_link_id": "plink_dup", "event": "payment.captured", "event_id": "evt_dup"}
    r1 = client.post(f"/orders/{oid}/paid_held", json=body)
    assert r1.status_code == 200
    assert r1.json()["changed"] is True
    r2 = client.post(f"/orders/{oid}/paid_held", json=body)
    assert r2.status_code == 200
    assert r2.json()["changed"] is False
    assert r2.json()["status"] == "paid_held"
    fetched = client.get(f"/orders/{oid}").json()["order"]["status"]
    assert fetched == "paid_held"


def test_paid_held_already_in_transit_no_downgrade(order_cleanup) -> None:
    oid = _create_order(order_cleanup)
    client.post(f"/orders/{oid}/paid_held", json={"payment_id": "pay_1"})
    from app.db import SessionLocal
    from app.models.order import OrderStatus

    with SessionLocal.begin() as s:
        from sqlalchemy import select

        o = s.execute(select(__import__("app.models.order", fromlist=["Order"]).Order).where(__import__("app.models.order", fromlist=["Order"]).Order.id == uuid.UUID(oid))).scalar_one()
        o.status = OrderStatus.in_transit
    resp = client.post(f"/orders/{oid}/paid_held", json={"payment_id": "pay_2"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "in_transit"
    assert resp.json()["changed"] is False


def test_patch_status_paid_held(order_cleanup) -> None:
    oid = _create_order(order_cleanup)
    resp = client.patch(f"/orders/{oid}/status", json={"status": "paid_held", "payment_id": "pay_patch"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "paid_held"


def test_patch_status_invalid_rejects(order_cleanup) -> None:
    oid = _create_order(order_cleanup)
    resp = client.patch(f"/orders/{oid}/status", json={"status": "settled"})
    assert resp.status_code == 422


def test_paid_held_404() -> None:
    fake = str(uuid.uuid4())
    resp = client.post(f"/orders/{fake}/paid_held", json={"payment_id": "pay_x"})
    assert resp.status_code == 404
