"""Tests for document-pack generation — CI, PL, CN22/CN23, PBE.

Covers:
- CI has exporter name + line items
- PL has net/gross weights
- CN22 auto-selected for ≤ 300 SDR
- CN23 auto-selected for > 300 SDR
- POST /orders/{order_id}/generate-docs → 201 with all 4 docs
- Non-owner cannot generate docs
"""

from __future__ import annotations

import pytest
from app.main import app
from app.services.doc_generator import (
    SDR_MINOR_PER_UNIT,
    SDR_THRESHOLD,
    generate_ci,
    generate_cn,
    generate_pbe,
    generate_pl,
)
from httpx import ASGITransport, AsyncClient

# ---------------------------------------------------------------------------
# Test data
# ---------------------------------------------------------------------------

PROFILE_PAYLOAD: dict[str, str] = {
    "firm_name": "Test Exports Ltd",
    "owner_name": "John Doe",
    "pan": "ABCDE1234F",
    "bank_name": "State Bank of India",
    "bank_account": "12345678901",
    "ifsc": "SBIN0001234",
    "bank_branch": "Mumbai Main",
    "iec": "1234567890",
    "ad_code": "9876543",
    "gstin": "22AAAAA0000A1Z5",
    "address_line1": "123 Shipping Lane",
    "address_line2": "Andheri East",
    "city": "Mumbai",
    "state": "Maharashtra",
    "pincode": "400069",
    "phone": "9876543210",
}

SAMPLE_ORDER_DATA: dict = {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "exporter_name": "Acme Exports Pvt Ltd",
    "exporter_address": "42 MG Road, Bengaluru 560001",
    "iec": "1234567890",
    "consignee": "Jane Doe, 123 Main St, New York, NY 10001, USA",
    "destination_country": "US",
    "currency": "INR",
    "value_minor": 200_000,  # ₹2,000
    "net_weight_g": 350.0,
    "gross_weight_g": 400.0,
    "line_items": [
        {
            "description": "Handwoven Silk Scarf",
            "hsn_code": "5007.20",
            "quantity": 5,
            "unit_price_minor": 25_000,
            "total_minor": 125_000,
        },
        {
            "description": "Brass Diya Set",
            "hsn_code": "7419.80",
            "quantity": 3,
            "unit_price_minor": 25_000,
            "total_minor": 75_000,
        },
    ],
    "bank_name": "State Bank of India",
    "ifsc": "SBIN0001234",
    "bank_account": "12345678901",
    "ad_code": "A1234567",
    "state_code": "29",
    "article_id": None,
}

ORDER_PAYLOAD_LOW: dict = {
    "destination_country": "US",
    "value_minor": 200_000,  # ₹2,000 (~18 SDR → CN22)
    "consignee": "Jane Doe, 123 Main St",
    "net_weight_g": 350.0,
    "gross_weight_g": 400.0,
    "line_items": [
        {
            "description": "Handwoven Silk Scarf",
            "hsn_code": "5007.20",
            "quantity": 5,
            "unit_price_minor": 25_000,
            "total_minor": 125_000,
        },
        {
            "description": "Brass Diya Set",
            "hsn_code": "7419.80",
            "quantity": 3,
            "unit_price_minor": 25_000,
            "total_minor": 75_000,
        },
    ],
}

ORDER_PAYLOAD_HIGH: dict = {
    "destination_country": "US",
    "value_minor": 4_000_000,  # ₹40,000 (~365 SDR → CN23)
    "consignee": "Jane Doe, 123 Main St",
    "net_weight_g": 350.0,
    "gross_weight_g": 400.0,
    "line_items": [
        {
            "description": "Handwoven Silk Scarf",
            "hsn_code": "5007.20",
            "quantity": 5,
            "unit_price_minor": 500_000,
            "total_minor": 2_500_000,
        },
        {
            "description": "Brass Diya Set",
            "hsn_code": "7419.80",
            "quantity": 3,
            "unit_price_minor": 500_000,
            "total_minor": 1_500_000,
        },
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_profile(client: AsyncClient, token: str) -> None:
    resp = await client.post(
        "/profile",
        json=PROFILE_PAYLOAD,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"Profile creation failed: {resp.text}"


async def _create_order(
    client: AsyncClient, token: str, payload: dict
) -> str:
    resp = await client.post(
        "/orders",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 201, f"Order creation failed: {resp.text}"
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Unit tests — doc generator functions
# ---------------------------------------------------------------------------


class TestCommercialInvoice:
    """CI must include exporter name and line items."""

    def test_ci_has_exporter_name(self) -> None:
        ci = generate_ci(SAMPLE_ORDER_DATA)
        assert ci["exporter_name"] == "Acme Exports Pvt Ltd"
        assert ci["exporter_address"] == "42 MG Road, Bengaluru 560001"

    def test_ci_has_line_items(self) -> None:
        ci = generate_ci(SAMPLE_ORDER_DATA)
        items = ci["line_items"]
        assert len(items) == 2
        assert items[0]["description"] == "Handwoven Silk Scarf"
        assert items[0]["hsn_code"] == "5007.20"
        assert items[0]["quantity"] == 5
        assert items[0]["unit_price_minor"] == 25_000
        assert items[0]["total_minor"] == 125_000

    def test_ci_has_iec_and_bank_details(self) -> None:
        ci = generate_ci(SAMPLE_ORDER_DATA)
        assert ci["iec"] == "1234567890"
        assert ci["bank_details"]["bank_name"] == "State Bank of India"
        assert ci["bank_details"]["ifsc"] == "SBIN0001234"

    def test_ci_has_consignee(self) -> None:
        ci = generate_ci(SAMPLE_ORDER_DATA)
        assert ci["consignee"] == "Jane Doe, 123 Main St, New York, NY 10001, USA"
        assert ci["destination_country"] == "US"

    def test_ci_has_correct_fob_total(self) -> None:
        ci = generate_ci(SAMPLE_ORDER_DATA)
        assert ci["fob_value_minor"] == 200_000  # 125k + 75k

    def test_ci_handles_empty_line_items(self) -> None:
        data = {**SAMPLE_ORDER_DATA, "line_items": []}
        ci = generate_ci(data)
        assert ci["line_items"] == []
        assert ci["total_items"] == 0
        assert ci["fob_value_minor"] == 0


class TestPackingList:
    """PL must include net/gross weights and item details."""

    def test_pl_has_weights(self) -> None:
        pl = generate_pl(SAMPLE_ORDER_DATA)
        assert pl["net_weight_g"] == 350.0
        assert pl["gross_weight_g"] == 400.0

    def test_pl_has_item_descriptions(self) -> None:
        pl = generate_pl(SAMPLE_ORDER_DATA)
        items = pl["items"]
        assert len(items) == 2
        assert items[0]["description"] == "Handwoven Silk Scarf"
        assert items[0]["hsn_code"] == "5007.20"

    def test_pl_has_quantities(self) -> None:
        pl = generate_pl(SAMPLE_ORDER_DATA)
        assert pl["total_quantity"] == 8  # 5 + 3
        assert pl["total_pieces"] == 2


class TestCnAutoSelection:
    """CN22 for values ≤ 300 SDR, CN23 for > 300 SDR."""

    def test_cn22_for_low_value(self) -> None:
        """Value of 200,000 paise (₹2,000 ≈ 18.3 SDR) → CN22."""
        cn = generate_cn(SAMPLE_ORDER_DATA)
        assert cn["cn_type"] == "CN22"
        assert cn["document_type"] == "CN22"
        assert cn["sdr_value"] < SDR_THRESHOLD

    def test_cn23_for_high_value(self) -> None:
        """Value of 4,000,000 paise (₹40,000 ≈ 365 SDR) → CN23."""
        data = {**SAMPLE_ORDER_DATA, "value_minor": 4_000_000}
        cn = generate_cn(data)
        assert cn["cn_type"] == "CN23"
        assert cn["document_type"] == "CN23"
        assert cn["sdr_value"] > SDR_THRESHOLD

    def test_cn22_at_exact_threshold(self) -> None:
        """Exactly 300 SDR → CN22 (≤ threshold)."""
        exact_value = SDR_THRESHOLD * SDR_MINOR_PER_UNIT  # 3,282,600 paise
        data = {**SAMPLE_ORDER_DATA, "value_minor": exact_value}
        cn = generate_cn(data)
        assert cn["cn_type"] == "CN22"

    def test_cn23_just_above_threshold(self) -> None:
        """300 SDR + 1 paise → CN23 (> threshold)."""
        just_over = SDR_THRESHOLD * SDR_MINOR_PER_UNIT + 1
        data = {**SAMPLE_ORDER_DATA, "value_minor": just_over}
        cn = generate_cn(data)
        assert cn["cn_type"] == "CN23"

    def test_cn22_has_basic_fields(self) -> None:
        cn = generate_cn(SAMPLE_ORDER_DATA)
        assert "content_description" in cn
        assert "total_value_minor" in cn
        assert "gross_weight_g" in cn
        assert cn["origin_country"] == "IN"

    def test_cn23_has_detailed_fields(self) -> None:
        data = {**SAMPLE_ORDER_DATA, "value_minor": 4_000_000}
        cn = generate_cn(data)
        assert "item_details" in cn
        assert len(cn["item_details"]) == 2
        assert "hs_code" in cn["item_details"][0]
        assert "net_weight_g" in cn
        assert cn["exporter_name"] == "Acme Exports Pvt Ltd"


class TestPbe:
    """PBE-III/IV document generation."""

    def test_pbe_defaults_to_pbe_iv(self) -> None:
        pbe = generate_pbe(SAMPLE_ORDER_DATA)
        assert pbe["form_type"] == "PBE-IV"
        assert "ecommerce_columns" not in pbe

    def test_pbe_iii_with_ecommerce_info(self) -> None:
        ecom_data = {
            **SAMPLE_ORDER_DATA,
            "ecommerce_info": {
                "ecomm_gstin": "29AABCT1332L1ZI",
                "marketplace_url": "https://www.amazon.in",
                "payment_txn_id": "PAY-001",
                "sku_no": "SKU-1246",
                "tracking_number": "IN123456789",
            },
        }
        pbe = generate_pbe(ecom_data)
        assert pbe["form_type"] == "PBE-III"
        assert "ecommerce_columns" in pbe
        ec = pbe["ecommerce_columns"]
        assert ec["marketplace_url"] == "https://www.amazon.in"
        assert ec["sku_no"] == "SKU-1246"

    def test_pbe_has_iec_and_ad_code(self) -> None:
        pbe = generate_pbe(SAMPLE_ORDER_DATA)
        assert pbe["iec"] == "1234567890"
        assert pbe["ad_code"] == "A1234567"

    def test_pbe_has_cth_codes(self) -> None:
        pbe = generate_pbe(SAMPLE_ORDER_DATA)
        items = pbe["line_items"]
        assert items[0]["cth_code"] == "5007.20"
        assert items[1]["cth_code"] == "7419.80"

    def test_pbe_has_2026_additional_fields(self) -> None:
        pbe = generate_pbe(SAMPLE_ORDER_DATA)
        add = pbe["additional_details_2026"]
        assert add["igst_payment_status"] == "not_paid"
        assert add["end_use"] == "Export"
        assert add["nature_of_contract"] == "FOB"

    def test_pbe_has_declarations(self) -> None:
        pbe = generate_pbe(SAMPLE_ORDER_DATA)
        decl = pbe["declarations"]
        assert decl["zero_rated_export_u_s16_igst"] is True
        assert decl["fema_undertaking"] is True
        assert "drawback" in decl

    def test_pbe_drawback_scheme_claimed(self) -> None:
        data = {**SAMPLE_ORDER_DATA, "scheme_code": "drawback"}
        pbe = generate_pbe(data)
        assert pbe["declarations"]["drawback"]["claimed"] is True
        assert pbe["declarations"]["rodtep"]["claimed"] is False

    def test_pbe_parcel_summary(self) -> None:
        pbe = generate_pbe(SAMPLE_ORDER_DATA)
        summary = pbe["parcel_summary"]
        assert summary["gross_weight_g"] == 400.0
        assert summary["net_weight_g"] == 350.0
        assert summary["fob_value_minor"] == 200_000
        assert summary["total_items"] == 2


# ---------------------------------------------------------------------------
# Integration tests — POST /orders/{order_id}/generate-docs
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_docs_endpoint_returns_201(test_seller: dict[str, str]) -> None:
    """POST generate-docs → 201 with all 4 document types."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"], ORDER_PAYLOAD_LOW)

        resp = await client.post(
            f"/orders/{order_id}/generate-docs",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp.status_code == 201, resp.text
    data = resp.json()

    assert "id" in data
    assert data["order_id"] == order_id
    assert "generated_at" in data

    docs = data["documents"]
    assert "commercial_invoice" in docs
    assert "packing_list" in docs
    assert "customs_declaration" in docs
    assert "postal_bill_of_export" in docs

    # Spot-check CI
    ci = docs["commercial_invoice"]
    assert ci["exporter_name"] == "Test Exports Ltd"
    assert len(ci["line_items"]) == 2

    # Spot-check PL
    pl = docs["packing_list"]
    assert pl["net_weight_g"] == 350.0
    assert pl["gross_weight_g"] == 400.0

    # Spot-check CN auto-selection for low value
    cn = docs["customs_declaration"]
    assert cn["cn_type"] == "CN22"

    # Spot-check PBE
    pbe = docs["postal_bill_of_export"]
    assert pbe["form_type"] == "PBE-IV"
    assert pbe["iec"] == "1234567890"


@pytest.mark.asyncio
async def test_generate_docs_high_value_is_cn23(test_seller: dict[str, str]) -> None:
    """High-value order → CN23 in generated docs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"], ORDER_PAYLOAD_HIGH)

        resp = await client.post(
            f"/orders/{order_id}/generate-docs",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp.status_code == 201
    cn = resp.json()["documents"]["customs_declaration"]
    assert cn["cn_type"] == "CN23"


@pytest.mark.asyncio
async def test_orders_status_updated_after_generation(
    test_seller: dict[str, str],
) -> None:
    """After generation, order status should be docs_generated."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"], ORDER_PAYLOAD_LOW)

        # Generate docs
        resp = await client.post(
            f"/orders/{order_id}/generate-docs",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
        assert resp.status_code == 201

        # Fetch order — status should be docs_generated
        get_resp = await client.get(
            f"/orders/{order_id}",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
        assert get_resp.status_code == 200
        assert get_resp.json()["status"] == "docs_generated"
        assert get_resp.json()["doc_pack_id"] is not None


@pytest.mark.asyncio
async def test_non_owner_cannot_generate(
    test_seller: dict[str, str],
    test_buyer: dict[str, str],
) -> None:
    """A buyer (non-owner) cannot generate documents for a seller's order."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"], ORDER_PAYLOAD_LOW)

        # Seller role but NOT the owner
        resp = await client.post(
            f"/orders/{order_id}/generate-docs",
            headers={"Authorization": f"Bearer {test_buyer['token']}"},
        )

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_cannot_generate_docs_twice(test_seller: dict[str, str]) -> None:
    """Generating docs for an order that already has them → 409 conflict."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await _create_profile(client, test_seller["token"])
        order_id = await _create_order(client, test_seller["token"], ORDER_PAYLOAD_LOW)

        # First generation
        resp1 = await client.post(
            f"/orders/{order_id}/generate-docs",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
        assert resp1.status_code == 201

        # Duplicate generation
        resp2 = await client.post(
            f"/orders/{order_id}/generate-docs",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )

    assert resp2.status_code == 409
    assert "already generated" in resp2.json()["detail"].lower()


@pytest.mark.asyncio
async def test_unauthenticated_rejected() -> None:
    """No auth token → 401."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/orders/550e8400-e29b-41d4-a716-446655440000/generate-docs",
        )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_order_id_returns_400(test_seller: dict[str, str]) -> None:
    """Malformed UUID → 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/orders/not-a-uuid/generate-docs",
            headers={"Authorization": f"Bearer {test_seller['token']}"},
        )
    assert resp.status_code == 400
