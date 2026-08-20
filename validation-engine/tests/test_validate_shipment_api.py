"""POST /api/validate/shipment — per-turn draft validation report.

Pins: partial drafts report missing fields (with bilingual prompts),
over-cap lanes set lane_error (never 500), business bounds land in
business_errors, a complete draft with IEC/GSTIN is document_ready, and an
undisambiguated category is a 200 with db_info empty.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.api import app
from app.services.sanity import TurnError, sanity_ok, sanity_violations
from app.schemas.shipment import ShipmentDraft

client = TestClient(app)


def _post(draft: dict, **extra) -> object:
    payload = {"draft": draft}
    payload.update(extra)
    return client.post("/api/validate/shipment", json=payload)


def test_partial_draft_reports_missing_required() -> None:
    response = _post(
        {"product_category": "jute-products", "destination_country": "US"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["document_ready"] is False
    keys = [m["field_key"] for m in body["missing_required"]]
    assert keys, "missing_required must be non-empty for a partial draft"
    assert "consignee_details" in keys
    consignee = next(m for m in body["missing_required"] if m["field_key"] == "consignee_details")
    assert consignee["prompt_template_hi"]
    assert consignee["prompt_template_en"]
    assert body["db_info"]["lane"] is not None
    assert body["db_info"]["category"] is not None


def test_over_cap_weight_sets_lane_error() -> None:
    response = _post(
        {
            "product_category": "jute-products",
            "quantity": 12,
            "weight_grams": 40000,  # exceeds both ITPS 5000 and EMS 31500 for US
            "destination_country": "US",
        },
        form_type="PBE_IV",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["document_ready"] is False
    assert body["db_info"]["lane_error"]
    assert body["db_info"]["lane"] is None


def test_bad_bounds_land_in_business_errors() -> None:
    response = _post(
        {
            "product_category": "jute-products",
            "quantity": 99999,
            "weight_grams": 500,
            "destination_country": "US",
        }
    )
    assert response.status_code == 200
    body = response.json()
    assert body["business_errors"]
    assert body["document_ready"] is False


def test_full_draft_with_iec_gstin_is_document_ready() -> None:
    response = _post(
        {
            "product_category": "jute-products",
            "quantity": 12,
            "weight_grams": 500,
            "destination_country": "US",
            "consignee": "John Doe, 123 Main St",
            "value_minor": 1500000,
            "confidence": "high",
        },
        form_type="PBE_IV",
        iec="0123456789",
        gstin="33ABCDE1234F1ZP",
        state_iso2="CA",
    )
    assert response.status_code == 200
    body = response.json()
    assert body["document_ready"] is True, body
    assert body["business_errors"] == []
    assert body["missing_required"] == []
    assert body["document_rules"]["errors"] == []
    assert body["db_info"]["category"]["slug"] == "jute-products"
    assert body["db_info"]["cth"]
    assert body["db_info"]["duties"]
    assert body["db_info"]["lane"]["cost_minor"] > 0
    assert body["db_info"]["state_sales_tax"]["state_iso2"] == "CA"
    assert body["db_info"]["landed_cost_minor"] is not None


def test_unknown_category_is_200_with_empty_db_info() -> None:
    response = _post({"quantity": 5, "destination_country": "US"})
    assert response.status_code == 200
    body = response.json()
    fields = {e["field"] for e in body["business_errors"]}
    assert "product_category" in fields
    assert body["document_ready"] is False
    assert body["db_info"]["category"] is None
    assert body["db_info"]["hs_codes"] == []
    assert body["db_info"]["lane"] is None


def test_sanity_bounds_reject_implausible_quantity() -> None:
    """quantity=2000 passes the business bounds (1..10000) but is implausible
    for small-woodware (sanity cap 1000) — the chat must re-ask it.

    THE bug-scenario pin: the old 'दो हजार पे → quantity 2000' would now be
    rejected/re-prompted — the report carries a business error whose message
    names the plausibility range, and document_ready stays False.
    """
    response = _post(
        {
            "product_category": "small-woodware",
            "quantity": 2000,
            "weight_grams": 500,
            "destination_country": "US",
        }
    )
    assert response.status_code == 200
    body = response.json()
    fields = {e["field"] for e in body["business_errors"]}
    assert "quantity" in fields
    qty_error = next(e for e in body["business_errors"] if e["field"] == "quantity")
    assert "plausible" in qty_error["message"] or "implausible" in qty_error["message"]
    assert body["document_ready"] is False


def test_document_ready_only_when_all_valid() -> None:
    """document_ready flips ONLY when all six fields are stated AND valid.

    - all six fields but weight over the US ITPS cap → not ready, lane_error set;
    - all six fields genuinely valid (+ iec + gstin) → ready with the full
      research surface;
    - five of six fields (quantity unstated) → NOT ready — PBE required fields
      alone miss quantity, so readiness must also gate on the draft's own
      sentinel state (Wave-1 gap this pin exposes).
    """
    base = {
        "product_category": "jute-products",
        "quantity": 12,
        "destination_country": "US",
        "consignee": "John Doe, 123 Main St",
        "value_minor": 1500000,
    }

    over = _post(
        {**base, "weight_grams": 40000},
        form_type="PBE_IV",
        iec="0123456789",
        gstin="33ABCDE1234F1ZP",
    )
    assert over.status_code == 200
    body = over.json()
    assert body["document_ready"] is False
    assert body["db_info"]["lane_error"] or body["business_errors"]

    # 2. same draft, weight within the cap → ready with the full research surface
    ok = _post(
        {**base, "weight_grams": 500},
        form_type="PBE_IV",
        iec="0123456789",
        gstin="33ABCDE1234F1ZP",
        state_iso2="CA",
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["document_ready"] is True, body
    assert body["business_errors"] == []
    assert body["missing_required"] == []
    assert body["document_rules"]["errors"] == []
    assert body["db_info"]["category"] is not None
    assert body["db_info"]["hs_codes"]
    assert body["db_info"]["cth"]
    assert body["db_info"]["product_description"]
    assert body["db_info"]["duties"]
    assert body["db_info"]["lane"] is not None
    assert body["db_info"]["landed_cost_minor"] is not None

    # 3. five of six fields (quantity unstated) → NOT ready (the Wave-1 gap:
    #    quantity is not a PBE-required field, so missing_required alone would
    #    let document_ready flip True while the chat still asks for it)
    missing_qty = _post(
        {k: v for k, v in {**base, "weight_grams": 500}.items() if k != "quantity"},
        form_type="PBE_IV",
        iec="0123456789",
        gstin="33ABCDE1234F1ZP",
    )
    assert missing_qty.status_code == 200
    body = missing_qty.json()
    assert body["document_ready"] is False
    assert body["business_errors"] == []


def test_sanity_ok_accepts_sane_values_and_sentinels() -> None:
    assert sanity_ok(12, "quantity", "jute-products") is True
    assert sanity_ok(500, "weight_grams", "jute-products") is True
    assert sanity_ok(200000, "value_minor", "small-woodware") is True
    assert sanity_ok(1_000_000_000, "weight_grams", "small-woodware") is False
    assert sanity_ok(-1, "quantity", "small-woodware") is True  # sentinel
    assert sanity_ok("जॉन डो", "consignee", "small-woodware") is True  # non-numeric


def test_sanity_violations_lists_only_out_of_range_fields() -> None:
    draft = ShipmentDraft(
        product_category="small-woodware",
        quantity=2,
        weight_grams=40_000,  # over the 30_000 EMS cap
        destination_country="US",
        consignee="unknown",
        value_minor=-1,
    )
    violations = sanity_violations(draft, draft.product_category)
    fields = {v.field for v in violations}
    assert fields == {"weight_grams"}
    assert all(isinstance(v, TurnError) for v in violations)


def test_sanity_violations_respect_category_override(monkeypatch) -> None:
    import app.services.sanity as sanity

    monkeypatch.setitem(
        sanity._CATEGORY_OVERRIDES,
        "small-woodware",
        {"quantity": (1, 50)},
    )
    draft = ShipmentDraft(
        product_category="small-woodware",
        quantity=200,  # within the default 1000 but over the override 50
        weight_grams=-1,
        destination_country="US",
        consignee="unknown",
        value_minor=-1,
    )
    violations = sanity_violations(draft, draft.product_category)
    assert {v.field for v in violations} == {"quantity"}
