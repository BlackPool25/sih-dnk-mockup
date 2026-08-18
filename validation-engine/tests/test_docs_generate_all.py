"""POST /docs/generate-all — ready/incomplete gating and the CN22/CN23 SDR switch.

Pins: a ready order renders all four documents (INVOICE, PACKING_LIST, CN22,
PBE_IV), each with version/checksum/pdf_url; an incomplete order returns
status "incomplete" with no documents; the customs-declaration doc_type is
CN22 below the 300-SDR threshold and auto-switches to CN23 above it.  Every
created order (and its rendered documents) is deleted at teardown.
"""

from __future__ import annotations

import uuid

from fastapi.testclient import TestClient

from app.api import app

client = TestClient(app)

SELLER_ID = "dc777c25-9f68-47d4-ba6b-959a14387d90"
BUYER_ID = "197e1aa3-8799-404d-b983-111b2108dd1e"

_ALL_DOC_TYPES = {"INVOICE", "PACKING_LIST", "CN22", "PBE_IV"}
_CUSTOMS_TYPES = {"CN22", "CN23"}


def _marker() -> str:
    return f"TEST-{uuid.uuid4().hex[:8]}"


def _full_payload(**overrides: object) -> dict:
    payload: dict = {
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
    payload.update(overrides)
    return payload


def test_generate_all_on_ready_order_renders_four_documents(order_cleanup) -> None:
    created = client.post("/validate", json=_full_payload())
    assert created.json()["validation_state"] == "ready"
    order_id = created.json()["order_id"]
    order_cleanup.append(order_id)

    response = client.post(f"/docs/generate-all?order_id={order_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "complete"
    assert body["validation_state"] == "ready"
    assert body["order_id"] == order_id
    assert {d["doc_type"] for d in body["documents"]} == _ALL_DOC_TYPES
    for doc in body["documents"]:
        assert doc["version"] >= 1
        assert doc["checksum"]
        assert doc["pdf_url"]


def test_generate_all_on_incomplete_order_returns_incomplete(order_cleanup) -> None:
    payload = _full_payload()
    payload.pop("consignee")
    payload.pop("value_minor")
    created = client.post("/validate", json=payload)
    assert created.json()["validation_state"] == "incomplete"
    order_id = created.json()["order_id"]
    order_cleanup.append(order_id)

    response = client.post(f"/docs/generate-all?order_id={order_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "incomplete"
    assert body["validation_state"] == "incomplete"
    assert "documents" not in body


def test_customs_doc_is_cn22_below_sdr_threshold(order_cleanup) -> None:
    created = client.post("/validate", json=_full_payload(value_minor=200000))
    assert created.json()["validation_state"] == "ready"
    order_id = created.json()["order_id"]
    order_cleanup.append(order_id)

    body = client.post(f"/docs/generate-all?order_id={order_id}").json()
    assert body["status"] == "complete"
    customs = next(d for d in body["documents"] if d["doc_type"] in _CUSTOMS_TYPES)
    assert customs["doc_type"] == "CN22"


def test_customs_doc_switches_to_cn23_above_sdr_threshold(order_cleanup) -> None:
    created = client.post("/validate", json=_full_payload(value_minor=4_000_000))
    assert created.json()["validation_state"] == "ready"
    order_id = created.json()["order_id"]
    order_cleanup.append(order_id)

    body = client.post(f"/docs/generate-all?order_id={order_id}").json()
    assert body["status"] == "complete"
    customs = next(d for d in body["documents"] if d["doc_type"] in _CUSTOMS_TYPES)
    assert customs["doc_type"] == "CN23"


def test_generate_all_rejects_non_latin_consignee(order_cleanup) -> None:
    """The docs API hard-rejects non-Latin free-text (F-8 English invariant).

    An order created with a Devanagari consignee must return 422 'translate
    before submit' — the caller is responsible for transliteration first.
    """
    created = client.post("/validate", json=_full_payload(consignee="शिखा"))
    order_id = created.json()["order_id"]
    order_cleanup.append(order_id)
    # The order exists but cannot validate as ready (F-8 document rule fires
    # during graded evaluation); docs must still 422 hard-reject.
    assert created.json()["validation_state"] == "invalid"

    response = client.post(f"/docs/generate-all?order_id={order_id}")
    assert response.status_code == 422
    assert "translate before submit" in response.json()["detail"]


def test_generate_rejects_non_latin_consignee(order_cleanup) -> None:
    """The single-doc endpoint applies the same guard."""
    created = client.post("/validate", json=_full_payload(consignee="रमेश कुमार"))
    order_id = created.json()["order_id"]
    order_cleanup.append(order_id)

    response = client.post(f"/docs/generate?order_id={order_id}&doc_type=INVOICE")
    assert response.status_code == 422
    assert "translate before submit" in response.json()["detail"]
