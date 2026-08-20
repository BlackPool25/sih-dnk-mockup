"""In-memory double for ``app.services.val_client.ValClient``.

Shared by the backend-core test suite: ``conftest._mock_val_client`` installs
an instance in place of the real client (and patches each router's imported
reference); tests inspect it via the ``val_fake`` fixture.
"""

from __future__ import annotations

import uuid

from app.services.chat import _SENTINELS, pending_fields
from app.services.val_client import ExtractResult, NotFoundError

# The seeded category slugs → display names (the real engine resolves these
# from the DB; the double carries the same lookup so db_info matches).
_CATEGORY_DISPLAY: dict[str, str] = {
    "jute-products": "Jute Products",
    "small-woodware": "Small Woodware",
    "small-brass-metalware": "Small Brass Metalware",
    "embroidered-home-textiles": "Embroidered Home Textiles",
    "embroidered-bags-pouches": "Embroidered Bags & Pouches",
    "handloom-scarves-stoles": "Handloom Scarves & Stoles",
    "block-printed-textiles": "Block Printed Textiles",
    "imitation-artisan-jewellery": "Imitation Artisan Jewellery",
}


class FakeValClient:
    """Implements the whole proxy surface — chat-era methods (extract,
    validate_shipment, search_categories) plus the order / document / QR-token
    methods — and records every call as a method name in ``calls``.

    Per-case overrides (set on the instance before driving the API):

    - ``report``            — canned ``create_order`` response (its ``order_id``
                              is also wired into the fake's order store)
    - ``order``             — canned unified ``get_order`` response
    - ``orders_payload``    — canned ``list_orders`` response
    - ``generate_payload``  — canned ``generate_docs_all`` response
    - ``documents_payload`` — canned ``get_order_documents`` response
    - ``not_found``         — order_ids for which ``get_order`` raises
                              ``NotFoundError``

    When no override is set, ``create_order`` stores the payload as a unified
    order (so a subsequent ``get_order`` returns it) and document methods
    return the four standard documents (INVOICE, PACKING_LIST, CN22, PBE_IV).
    """

    def __init__(self) -> None:
        self.calls: list[str] = []
        self.category_unknown = False

        # Per-call report overrides (mirror the real engine's per-turn report)
        self.business_errors: list[dict[str, object]] = []  # injected into the report
        self.lane_error: str | None = None  # when set: db_info.lane_error + not ready

        # Canned overrides
        self.report: dict[str, object] | None = None
        self.order: dict[str, object] | None = None
        self.orders_payload: dict[str, object] | None = None
        self.generate_payload: dict[str, object] | None = None
        self.documents_payload: dict[str, object] | None = None
        self.not_found: set[str] = set()

        # Observation hooks
        self.last_payload: dict[str, object] = {}
        self.last_list_kwargs: dict[str, object] = {}
        self.qr_jti: str | None = None

    # ------------------------------------------------------------------ #
    # Chat-era surface (unchanged behaviour)
    # ------------------------------------------------------------------ #

    async def extract(
        self,
        text: str,
        lang: str,
        previous: dict[str, object] | None = None,
        expected: str | None = None,
    ) -> ExtractResult:
        self.calls.append("extract")
        draft: dict[str, object] = {}
        lower = text.lower()
        if "jute" in lower or "जूट" in text:
            draft["product_category"] = "jute-products"
        if "wood" in lower or "लकड़ी" in text:
            draft["product_category"] = "small-woodware"
        if "12" in text:
            draft["quantity"] = 12
        if "500" in text:
            draft["weight_grams"] = 500
        if "germany" in lower or "जर्मनी" in text:
            draft["destination_country"] = "DE"
        if "₹" in text or "inr" in lower or "रुपये" in text:
            draft["value_minor"] = 1500000
        if "john" in lower or "जॉन" in text:
            draft["consignee"] = "John Doe, 123 Berlin Str"
        return ExtractResult(
            draft=draft,
            category_unknown=self.category_unknown,
            extractor="rule",
        )

    def _db_info_for(self, draft: dict[str, object]) -> dict[str, object]:
        slug = draft.get("product_category")
        name = _CATEGORY_DISPLAY.get(str(slug)) if slug else None
        if name is None and slug:
            name = str(slug)
        return {
            "category_name": name,
            "category": {"slug": slug, "name": name} if name else None,
            "product_description": name,
            "hs_codes": [],
        }

    async def validate_shipment(
        self,
        draft: dict[str, object],
        *,
        form_type: str = "PBE_IV",
        iec: str | None = None,
        gstin: str | None = None,
        state_iso2: str | None = None,
        previous_db_info: dict[str, object] | None = None,
        changed_fields: list[str] | None = None,
    ) -> dict[str, object]:
        self.calls.append("validate")
        # The real ValidationTurnReport emits PBE field keys in missing_required
        # (consignee_details ← draft.consignee, assessable_value ←
        # draft.value_minor), never the draft keys themselves.
        pbe_missing: list[str] = []
        if draft.get("consignee") in _SENTINELS:
            pbe_missing.append("consignee_details")
        if draft.get("value_minor") in _SENTINELS:
            pbe_missing.append("assessable_value")
        missing = [
            {
                "field_key": key,
                "label": key,
                "prompt_template_hi": f"कृपया {key} बताएं",
                "prompt_template_en": f"Please provide {key}",
            }
            for key in pbe_missing
        ]
        errors = [dict(e) for e in self.business_errors]
        if changed_fields is not None and changed_fields:
            errors = [e for e in errors if e.get("field") in set(changed_fields)]
        db_info = self._db_info_for(draft)
        if previous_db_info is not None and not db_info.get("category"):
            prev_cat = previous_db_info.get("category")  # type: ignore[union-attr]
            if isinstance(prev_cat, dict):
                db_info["category"] = prev_cat
                db_info["category_name"] = prev_cat.get("name")  # type: ignore[union-attr]
        if self.lane_error is not None:
            db_info["lane_error"] = self.lane_error
        self.last_previous_db_info = previous_db_info  # type: ignore[attr-defined]
        self.last_changed_fields = changed_fields  # type: ignore[attr-defined]
        if self.lane_error is not None:
            db_info["lane_error"] = self.lane_error
        return {
            "draft": draft,
            "business_errors": errors,
            "missing_required": missing,
            "document_rules": {"errors": [], "warnings": []},
            "document_ready": not errors and self.lane_error is None and not pending_fields(draft),
            "db_info": db_info,
        }

    async def search_categories(self, query: str) -> list[dict[str, object]]:
        self.calls.append("search_categories")
        return [{"slug": "jute-products", "name": "Jute Products"}]

    async def lookup_hs_codes(self, category: str) -> list[dict[str, object]]:
        return [{"hs6": "5310", "description": "Jute fibres raw"}]

    # ------------------------------------------------------------------ #
    # Order / document / QR-token proxy surface
    # ------------------------------------------------------------------ #

    def _default_order(
        self, order_id: str, payload: dict[str, object]
    ) -> dict[str, object]:
        """Build a unified ``{order, last_report, line_items}`` response."""
        items: list[dict[str, object]] = []
        raw_items = payload.get("line_items")
        for item in raw_items if isinstance(raw_items, list) else []:
            it = dict(item) if isinstance(item, dict) else {}
            it.setdefault("dimensions", None)
            items.append(it)
        order: dict[str, object] = {
            "id": order_id,
            "seller_id": payload.get("seller_id"),
            "buyer_id": payload.get("buyer_id"),
            "status": "created",
            "validation_state": "drafting",
            "destination_country": payload.get("destination_country"),
            "value_minor": payload.get("value_minor"),
            "currency": payload.get("currency") or "INR",
            "consignee": payload.get("consignee"),
            "net_weight_g": payload.get("net_weight_g"),
            "gross_weight_g": payload.get("gross_weight_g"),
            "article_id": payload.get("article_id"),
            "iec": payload.get("iec"),
            "gstin": payload.get("gstin"),
            "ad_code": payload.get("ad_code"),
            "bank_account": payload.get("bank_account"),
            "bank_name": payload.get("bank_name"),
            "ifsc": payload.get("ifsc"),
            "quote_id": None,
            "exporter_name": payload.get("exporter_name"),
            "exporter_address": payload.get("exporter_address"),
            "state_code": payload.get("state_code"),
            "qr_token_jti": None,
            "version": 1,
            "last_report": {"status": "valid", "validation_state": "validated"},
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
        return {
            "order": order,
            "last_report": {"status": "valid", "validation_state": "validated"},
            "line_items": items,
        }

    def _default_docs(self) -> list[dict[str, object]]:
        """The four standard generated documents (doc_type-keyed)."""
        return [
            {
                "doc_type": "INVOICE",
                "version": 1,
                "checksum": "sha256-invoice",
                "pdf_url": "http://engine/docs/invoice.pdf",
                "generated_at": "2026-01-01T00:00:00Z",
            },
            {
                "doc_type": "PACKING_LIST",
                "version": 1,
                "checksum": "sha256-pl",
                "pdf_url": "http://engine/docs/pl.pdf",
                "generated_at": "2026-01-01T00:00:00Z",
            },
            {
                "doc_type": "CN22",
                "version": 1,
                "checksum": "sha256-cn22",
                "pdf_url": "http://engine/docs/cn22.pdf",
                "generated_at": "2026-01-01T00:00:00Z",
            },
            {
                "doc_type": "PBE_IV",
                "version": 1,
                "checksum": "sha256-pbe",
                "pdf_url": "http://engine/docs/pbe.pdf",
                "generated_at": "2026-01-01T00:00:00Z",
            },
        ]

    async def create_order(self, payload: dict[str, object]) -> dict[str, object]:
        self.calls.append("create_order")
        self.last_payload = payload
        if self.report is not None:
            order_id = str(self.report.get("order_id") or uuid.uuid4())
            self.order = self._default_order(order_id, payload)
            return dict(self.report)
        order_id = str(uuid.uuid4())
        self.order = self._default_order(order_id, payload)
        return {
            "order_id": order_id,
            "status": "valid",
            "validation_state": "validated",
            "errors": [],
            "missing": [],
            "warnings": [],
            "doc_ready": True,
        }

    async def list_orders(
        self,
        *,
        seller_id: str | None = None,
        buyer_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, object]:
        self.calls.append("list_orders")
        self.last_list_kwargs = {
            "seller_id": seller_id,
            "buyer_id": buyer_id,
            "status": status,
            "limit": limit,
            "offset": offset,
        }
        if self.orders_payload is not None:
            return self.orders_payload
        orders: list[dict[str, object]] = []
        if self.order is not None:
            entry = self.order.get("order")
            if isinstance(entry, dict):
                matches = True
                if seller_id is not None and str(entry.get("seller_id")) != seller_id:
                    matches = False
                if buyer_id is not None and str(entry.get("buyer_id")) != buyer_id:
                    matches = False
                if status is not None and str(entry.get("status")) != status:
                    matches = False
                if matches:
                    orders.append(
                        {"order": entry, "line_items": self.order.get("line_items", [])}
                    )
        return {"orders": orders, "total": len(orders), "limit": limit, "offset": offset}

    async def get_order(self, order_id: str) -> dict[str, object]:
        self.calls.append("get_order")
        if self.order is None or order_id in self.not_found:
            raise NotFoundError(f"order {order_id} not found")
        inner = self.order.get("order")
        if not isinstance(inner, dict) or str(inner.get("id")) != order_id:
            raise NotFoundError(f"order {order_id} not found")
        return self.order

    async def generate_docs_all(self, order_id: str) -> dict[str, object]:
        self.calls.append("generate_docs_all")
        if self.generate_payload is not None:
            return dict(self.generate_payload)
        return {
            "order_id": order_id,
            "status": "complete",
            "validation_state": "validated",
            "generated_at": "2026-01-01T00:00:00Z",
            "documents": self._default_docs(),
        }

    async def get_order_documents(self, order_id: str) -> dict[str, object]:
        self.calls.append("get_order_documents")
        if self.documents_payload is not None:
            return dict(self.documents_payload)
        return {"order_id": order_id, "documents": self._default_docs()}

    async def set_qr_token(self, order_id: str, jti: str) -> dict[str, object]:
        self.calls.append("set_qr_token")
        self.qr_jti = jti
        if self.order is not None:
            inner = self.order.get("order")
            if isinstance(inner, dict):
                inner["qr_token_jti"] = jti
        return {"order_id": order_id, "qr_token_jti": jti}

    async def mark_paid_held(
        self,
        order_id: str,
        payment_id: str | None = None,
        payment_link_id: str | None = None,
        event: str | None = None,
        event_id: str | None = None,
    ) -> dict[str, object]:
        self.calls.append("mark_paid_held")
        if self.order is not None:
            inner = self.order.get("order")
            if isinstance(inner, dict) and str(inner.get("id")) == order_id:
                inner["status"] = "paid_held"
                inner["last_report"] = {
                    "payment": {
                        "payment_id": payment_id,
                        "payment_link_id": payment_link_id,
                        "event": event,
                        "event_id": event_id,
                        "money_location": "RAZORPAY_MERCHANT_BALANCE",
                    }
                }
        return {"order_id": order_id, "status": "paid_held", "changed": True}

    async def patch_order_status(
        self, order_id: str, status: str, payment_id: str | None = None, payment_link_id: str | None = None, event: str | None = None, event_id: str | None = None
    ) -> dict[str, object]:
        return await self.mark_paid_held(order_id, payment_id=payment_id, payment_link_id=payment_link_id, event=event, event_id=event_id)
