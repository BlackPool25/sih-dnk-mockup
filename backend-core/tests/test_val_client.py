"""val_client — HTTP boundary against the validation-engine tool API.

Pins: the exact request shapes (extract body, validate body, tool query
params), error mapping (404→NotFoundError, 422→InvalidInputError,
connect→ServiceUnavailable), and passthrough of engine JSON.
"""

from __future__ import annotations

import httpx
import pytest

from app.services.val_client import (
    InvalidInputError,
    NotFoundError,
    ServiceUnavailable,
    ValClient,
)

pytestmark = pytest.mark.asyncio


def _make_client(handler: object) -> ValClient:
    return ValClient(base_url="http://test-engine", transport=httpx.MockTransport(handler))


async def test_extract_posts_text_lang_previous() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/extract"
        body = request.read().decode()
        assert '"text":"नमस्ते"' in body
        assert '"lang":"hi"' in body
        return httpx.Response(
            200,
            json={
                "draft": {"product_category": "jute-products", "quantity": -1},
                "category_unknown": False,
                "extractor": "rule",
            },
        )

    client = _make_client(handler)
    result = await client.extract("नमस्ते", "hi", previous={"quantity": -1})
    assert result.extractor == "rule"
    assert result.draft["product_category"] == "jute-products"
    assert result.category_unknown is False


async def test_validate_shipment_posts_draft_and_optional_identifiers() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/validate/shipment"
        body = request.read().decode()
        assert '"form_type":"PBE_IV"' in body
        assert '"iec":"0123456789"' in body
        return httpx.Response(
            200,
            json={
                "draft": {"quantity": 12},
                "business_errors": [],
                "missing_required": [],
                "document_rules": {"errors": [], "warnings": []},
                "document_ready": True,
                "db_info": {"category_name": "Jute Products"},
            },
        )

    client = _make_client(handler)
    report = await client.validate_shipment(
        {"quantity": 12}, iec="0123456789", gstin=None, state_iso2=None
    )
    assert report["document_ready"] is True
    assert report["db_info"]["category_name"] == "Jute Products"


async def test_validate_shipment_without_identifiers() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = request.read().decode()
        assert '"iec":null' in body
        return httpx.Response(200, json={"document_ready": False, "db_info": {}})

    client = _make_client(handler)
    report = await client.validate_shipment({"quantity": 12})
    assert report["document_ready"] is False


async def test_search_categories_uses_query_param() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tools/categories"
        assert request.url.params["query"] == "jute"
        return httpx.Response(200, json=[{"slug": "jute-products", "name": "Jute Products"}])

    client = _make_client(handler)
    cats = await client.search_categories("jute")
    assert cats[0]["slug"] == "jute-products"


async def test_lookup_hs_codes_uses_category_param() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/tools/hs-codes"
        assert request.url.params["category"] == "jute-products"
        return httpx.Response(200, json=[{"hs6": "5310"}])

    client = _make_client(handler)
    rows = await client.lookup_hs_codes("jute-products")
    assert rows[0]["hs6"] == "5310"


async def test_404_maps_to_not_found() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "no ITPS lane for XX"})

    client = _make_client(handler)
    with pytest.raises(NotFoundError):
        await client.search_categories("x")


async def test_422_maps_to_invalid_input() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"detail": "weight exceeds cap"})

    client = _make_client(handler)
    with pytest.raises(InvalidInputError):
        await client.search_categories("x")


async def test_connect_error_maps_to_service_unavailable() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("boom", request=request)

    client = _make_client(handler)
    with pytest.raises(ServiceUnavailable):
        await client.search_categories("x")


async def test_create_order_posts_payload_to_validate() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/validate"
        body = request.read().decode()
        assert '"seller_id":"SELL-1"' in body
        return httpx.Response(
            200,
            json={
                "status": "valid",
                "validation_state": "validated",
                "order_id": "ORD-1",
                "errors": [],
                "missing": [],
                "warnings": [],
                "doc_ready": True,
            },
        )

    client = _make_client(handler)
    report = await client.create_order({"seller_id": "SELL-1"})
    assert report["status"] == "valid"
    assert report["order_id"] == "ORD-1"


async def test_create_order_returns_business_errors_in_200_body() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/validate"
        return httpx.Response(
            200,
            json={
                "status": "incomplete",
                "validation_state": "drafting",
                "order_id": "ORD-1",
                "errors": [{"code": "MISSING_IEC"}],
                "missing": ["iec"],
                "warnings": [],
                "doc_ready": False,
            },
        )

    client = _make_client(handler)
    report = await client.create_order({"seller_id": "SELL-1"})
    assert report["status"] == "incomplete"
    assert report["errors"][0]["code"] == "MISSING_IEC"


async def test_list_orders_sends_only_non_none_params() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/orders"
        params = request.url.params
        assert params["seller_id"] == "SELL-1"
        assert params["limit"] == "50"
        assert params["offset"] == "0"
        assert "buyer_id" not in params
        assert "status" not in params
        return httpx.Response(
            200, json={"orders": [], "total": 0, "limit": 50, "offset": 0}
        )

    client = _make_client(handler)
    data = await client.list_orders(seller_id="SELL-1")
    assert data["total"] == 0
    assert data["orders"] == []


async def test_list_orders_sends_all_params_when_given() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        params = request.url.params
        assert params["seller_id"] == "SELL-1"
        assert params["buyer_id"] == "BUY-1"
        assert params["status"] == "drafting"
        assert params["limit"] == "10"
        assert params["offset"] == "20"
        return httpx.Response(
            200,
            json={"orders": [{"id": "ORD-1"}], "total": 1, "limit": 10, "offset": 20},
        )

    client = _make_client(handler)
    data = await client.list_orders(
        seller_id="SELL-1", buyer_id="BUY-1", status="drafting", limit=10, offset=20
    )
    assert data["orders"][0]["id"] == "ORD-1"


async def test_get_order_paths_order_id() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/orders/ORD-1"
        return httpx.Response(
            200,
            json={
                "order": {"id": "ORD-1"},
                "last_report": {"status": "valid"},
                "line_items": [],
            },
        )

    client = _make_client(handler)
    data = await client.get_order("ORD-1")
    assert data["order"]["id"] == "ORD-1"
    assert data["last_report"]["status"] == "valid"


async def test_generate_docs_all_uses_query_param() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/docs/generate-all"
        assert request.url.params["order_id"] == "ORD-1"
        return httpx.Response(
            200,
            json={
                "order_id": "ORD-1",
                "validation_state": "validated",
                "status": "complete",
                "documents": [
                    {
                        "doc_type": "PBE",
                        "version": 1,
                        "checksum": "abc",
                        "pdf_url": "http://x/pbe.pdf",
                        "generated_at": "2026-01-01T00:00:00Z",
                    }
                ],
            },
        )

    client = _make_client(handler)
    data = await client.generate_docs_all("ORD-1")
    assert data["status"] == "complete"
    assert data["documents"][0]["doc_type"] == "PBE"


async def test_generate_docs_all_accepts_incomplete_status() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "order_id": "ORD-1",
                "validation_state": "drafting",
                "status": "incomplete",
                "documents": [],
                "message": "cannot render until order is validated",
            },
        )

    client = _make_client(handler)
    data = await client.generate_docs_all("ORD-1")
    assert data["status"] == "incomplete"
    assert data["documents"] == []


async def test_get_order_documents_paths_order_id() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/orders/ORD-1/documents"
        return httpx.Response(
            200,
            json={
                "documents": [{"doc_type": "PBE", "pdf_url": "http://x/pbe.pdf"}],
                "order_id": "ORD-1",
            },
        )

    client = _make_client(handler)
    data = await client.get_order_documents("ORD-1")
    assert data["documents"][0]["doc_type"] == "PBE"
    assert data["order_id"] == "ORD-1"


async def test_set_qr_token_posts_jti() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/orders/ORD-1/qr-token"
        body = request.read().decode()
        assert '"jti":"abc-123"' in body
        return httpx.Response(200, json={"order_id": "ORD-1", "qr_token_jti": "abc-123"})

    client = _make_client(handler)
    data = await client.set_qr_token("ORD-1", "abc-123")
    assert data["qr_token_jti"] == "abc-123"


async def test_404_on_get_order_maps_to_not_found() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, json={"detail": "order not found"})

    client = _make_client(handler)
    with pytest.raises(NotFoundError):
        await client.get_order("NOPE")
