"""GET /orders/{id}/documents + /pdf and POST /orders/{id}/qr-token.

Pins: after generate-all the documents list echoes every rendered doc with
doc_type/version/checksum/pdf_url; the PDF endpoint serves the INVOICE as an
application/pdf payload starting with %PDF and 404s for a doc_type the order
does not have; qr-token binds a JTI visible on GET /orders/{id}.  Created
orders and their documents are deleted at teardown.
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


def _ready_order() -> dict:
    return {
        "seller_id": SELLER_ID,
        "buyer_id": BUYER_ID,
        "destination_country": "US",
        "value_minor": 200000,
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


def _create_ready_order(order_cleanup: list[str]) -> str:
    created = client.post("/validate", json=_ready_order())
    assert created.json()["validation_state"] == "ready"
    order_id = created.json()["order_id"]
    order_cleanup.append(order_id)
    return order_id


def test_documents_list_echoes_rendered_docs(order_cleanup) -> None:
    order_id = _create_ready_order(order_cleanup)
    generated = client.post(f"/docs/generate-all?order_id={order_id}")
    assert generated.json()["status"] == "complete"

    response = client.get(f"/orders/{order_id}/documents")
    assert response.status_code == 200
    body = response.json()
    assert body["order_id"] == order_id
    assert body["documents"]
    for doc in body["documents"]:
        assert doc["doc_type"]
        assert doc["version"] >= 1
        assert doc["checksum"]
        assert doc["pdf_url"]


def test_invoice_pdf_served(order_cleanup) -> None:
    order_id = _create_ready_order(order_cleanup)
    client.post(f"/docs/generate-all?order_id={order_id}")

    response = client.get(f"/orders/{order_id}/pdf?doc_type=INVOICE")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")
    assert response.content


def test_pdf_unknown_doc_type_is_404(order_cleanup) -> None:
    order_id = _create_ready_order(order_cleanup)
    client.post(f"/docs/generate-all?order_id={order_id}")

    response = client.get(f"/orders/{order_id}/pdf?doc_type=NOT_A_TYPE")
    assert response.status_code == 404


def test_qr_token_binds_and_echoes(order_cleanup) -> None:
    order_id = _create_ready_order(order_cleanup)
    jti = f"jti-{uuid.uuid4().hex[:8]}"

    response = client.post(f"/orders/{order_id}/qr-token", json={"jti": jti})
    assert response.status_code == 200
    body = response.json()
    assert body["order_id"] == order_id
    assert body["qr_token_jti"] == jti

    order = client.get(f"/orders/{order_id}").json()["order"]
    assert order["qr_token_jti"] == jti
