"""POST /validate — order create/update, seller/buyer ownership, binding freeze.

Pins: a full payload with seller_id=buyer_id becomes a ready order; GET
/orders/{order_id} echoes both ids; a second POST on the same order_id merges
and bumps version; a confirmed order freezes binding fields (block entry, the
stored seller_id is unchanged); a non-UUID seller_id surfaces as a report
error, never a 500.  Every created order is deleted at teardown.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy import update

from app.api import app
from app.db import SessionLocal
from app.models.order import Order, OrderStatus

client = TestClient(app)

SELLER_ID = "dc777c25-9f68-47d4-ba6b-959a14387d90"
BUYER_ID = "197e1aa3-8799-404d-b983-111b2108dd1e"
OTHER_SELLER_ID = "9d3da05f-48c0-4c5b-a471-644ba9f97591"


def _marker() -> str:
    return f"TEST-{uuid.uuid4().hex[:8]}"


def _full_payload(**overrides: object) -> dict:
    payload: dict = {
        "seller_id": SELLER_ID,
        "buyer_id": BUYER_ID,
        "destination_country": "US",
        "value_minor": 200000,
        "currency": "INR",
        "consignee": "Jane Doe, 123 Main St",
        "net_weight_g": 400,
        "gross_weight_g": 400,
        "article_id": _marker(),
        "iec": "0123456789",
        "gstin": "29ABCDE1234F1Z5",
        "exporter_name": "Acme Exporters Pvt Ltd",
        "exporter_address": "42 MG Road, Bengaluru 560001",
        "state_code": "29",
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


def test_full_payload_creates_ready_order(order_cleanup) -> None:
    response = client.post("/validate", json=_full_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["order_id"]
    assert body["validation_state"] == "ready"
    order_cleanup.append(body["order_id"])


def test_get_order_echoes_seller_and_buyer(order_cleanup) -> None:
    order_id = client.post("/validate", json=_full_payload()).json()["order_id"]
    order_cleanup.append(order_id)

    response = client.get(f"/orders/{order_id}")
    assert response.status_code == 200
    order = response.json()["order"]
    assert order["seller_id"] == SELLER_ID
    assert order["buyer_id"] == BUYER_ID


def test_update_same_order_bumps_version(order_cleanup) -> None:
    order_id = client.post("/validate", json=_full_payload()).json()["order_id"]
    order_cleanup.append(order_id)
    version_before = client.get(f"/orders/{order_id}").json()["order"]["version"]

    response = client.post(
        "/validate", json={"order_id": order_id, "destination_country": "GB"}
    )
    assert response.status_code == 200
    order = client.get(f"/orders/{order_id}").json()["order"]
    assert order["version"] == version_before + 1
    assert order["destination_country"] == "GB"


def test_binding_freeze_blocks_seller_change(order_cleanup) -> None:
    order_id = client.post("/validate", json=_full_payload()).json()["order_id"]
    order_cleanup.append(order_id)
    with SessionLocal.begin() as session:
        session.execute(
            update(Order)
            .where(Order.id == uuid.UUID(order_id))
            .values(status=OrderStatus.confirmed)
        )

    response = client.post(
        "/validate", json={"order_id": order_id, "seller_id": OTHER_SELLER_ID}
    )
    assert response.status_code == 200
    fields = {(e["field"], e["severity"]) for e in response.json()["errors"]}
    assert ("seller_id", "block") in fields

    order = client.get(f"/orders/{order_id}").json()["order"]
    assert order["seller_id"] == SELLER_ID


def test_non_uuid_seller_id_is_report_error_not_500(order_cleanup) -> None:
    order_id = client.post("/validate", json=_full_payload()).json()["order_id"]
    order_cleanup.append(order_id)

    response = client.post(
        "/validate", json={"order_id": order_id, "seller_id": "not-a-uuid"}
    )
    assert response.status_code == 200
    entry = next(e for e in response.json()["errors"] if e["field"] == "seller_id")
    assert entry["severity"] == "error"
    assert "invalid UUID" in entry["message"]

    order = client.get(f"/orders/{order_id}").json()["order"]
    assert order["seller_id"] == SELLER_ID
