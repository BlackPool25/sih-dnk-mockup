"""HTTP client for the validation-engine tool/extract/validate API.

The anti-hallucination contract boundary: backend-core never imports
validation-engine code — it calls the read-only tool surface over HTTP.  Every
method returns the engine's JSON payload; 404/422 are surfaced as typed
exceptions, connect failures as ``ServiceUnavailable``.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import httpx
from pydantic import BaseModel

from storage.config import settings

_READ_TIMEOUT = 60.0


class ValClientError(Exception):
    """Base for validation-engine client errors."""


class NotFoundError(ValClientError):
    """404 from the engine (unknown lane, state, flag)."""


class InvalidInputError(ValClientError):
    """422 from the engine (bad value for a lookup)."""


class ServiceUnavailable(ValClientError):
    """Engine unreachable (connect error or 503)."""


class ExtractResult(BaseModel):
    """POST /api/extract response."""

    draft: dict[str, object]
    category_unknown: bool
    extractor: str
    candidates: list[str] = []


class ValClient:
    """Thin async httpx wrapper over the validation-engine HTTP API."""

    def __init__(
        self,
        base_url: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = (base_url or settings.VALIDATION_ENGINE_URL).rstrip("/")
        self._transport = transport

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, object] | None = None,
        params: dict[str, str | int] | None = None,
    ) -> dict[str, object] | Sequence[dict[str, object]]:
        client_kwargs: dict[str, Any] = {"timeout": _READ_TIMEOUT}
        if self._transport is not None:
            client_kwargs["transport"] = self._transport
        try:
            async with httpx.AsyncClient(**client_kwargs) as client:
                resp = await client.request(
                    method, f"{self._base_url}{path}", json=json, params=params
                )
        except httpx.ConnectError as exc:
            raise ServiceUnavailable(f"validation-engine unreachable: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise ServiceUnavailable(f"validation-engine timed out: {exc}") from exc
        if resp.status_code == 404:
            raise NotFoundError(str(resp.json().get("detail", "not found")))
        if resp.status_code == 422:
            raise InvalidInputError(str(resp.json().get("detail", "invalid input")))
        if resp.status_code >= 500:
            raise ServiceUnavailable(f"validation-engine error {resp.status_code}")
        resp.raise_for_status()
        data: dict[str, object] | Sequence[dict[str, object]] = resp.json()
        return data

    async def _get_list(
        self, path: str, *, params: dict[str, str | int] | None = None
    ) -> list[dict[str, object]]:
        data = await self._request("GET", path, params=params)
        if not isinstance(data, list):
            raise ValClientError(f"expected a list at {path}, got {type(data).__name__}")
        return list(data)

    async def _post_json(self, path: str, *, json: dict[str, object]) -> dict[str, object]:
        data = await self._request("POST", path, json=json)
        if not isinstance(data, dict):
            raise ValClientError(f"expected an object at {path}, got {type(data).__name__}")
        return data

    async def _get_json(
        self, path: str, *, params: dict[str, str | int] | None = None
    ) -> dict[str, object]:
        data = await self._request("GET", path, params=params)
        if not isinstance(data, dict):
            raise ValClientError(f"expected an object at {path}, got {type(data).__name__}")
        return data

    async def extract(
        self,
        text: str,
        lang: str,
        previous: dict[str, object] | None = None,
        expected: str | None = None,
    ) -> ExtractResult:
        """POST /api/extract — text + prior draft → ShipmentDraft keys."""
        payload: dict[str, object] = {"text": text, "lang": lang, "previous": previous}
        if expected is not None:
            payload["expected"] = expected
        data = await self._post_json("/api/extract", json=payload)
        return ExtractResult.model_validate(data)

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
        """POST /api/validate/shipment — deterministic per-turn report."""
        payload: dict[str, object] = {
            "draft": draft,
            "form_type": form_type,
            "iec": iec,
            "gstin": gstin,
            "state_iso2": state_iso2,
        }
        if previous_db_info is not None:
            payload["previous_db_info"] = previous_db_info
        if changed_fields is not None:
            payload["changed_fields"] = changed_fields
        return await self._post_json(
            "/api/validate/shipment",
            json=payload,
        )

    async def search_categories(self, query: str) -> list[dict[str, object]]:
        """GET /api/tools/categories — category candidates for disambiguation."""
        return await self._get_list("/api/tools/categories", params={"query": query})

    async def lookup_hs_codes(self, category: str) -> list[dict[str, object]]:
        """GET /api/tools/hs-codes — HS rows for a category."""
        return await self._get_list("/api/tools/hs-codes", params={"category": category})

    async def create_order(self, payload: dict[str, object]) -> dict[str, object]:
        """POST /validate — create or update a partial order; returns the report."""
        return await self._post_json("/validate", json=payload)

    async def list_orders(
        self,
        *,
        seller_id: str | None = None,
        buyer_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict[str, object]:
        """GET /orders — paginated orders, filtered by the non-None params."""
        params: dict[str, str | int] = {"limit": limit, "offset": offset}
        if seller_id is not None:
            params["seller_id"] = seller_id
        if buyer_id is not None:
            params["buyer_id"] = buyer_id
        if status is not None:
            params["status"] = status
        return await self._get_json("/orders", params=params)

    async def get_order(self, order_id: str) -> dict[str, object]:
        """GET /orders/{order_id} — full order with last report and line items."""
        return await self._get_json(f"/orders/{order_id}")

    async def generate_docs_all(self, order_id: str) -> dict[str, object]:
        """POST /docs/generate-all — batch-render all documents for an order."""
        data = await self._request(
            "POST", "/docs/generate-all", params={"order_id": order_id}
        )
        if not isinstance(data, dict):
            raise ValClientError(
                f"expected an object at /docs/generate-all, got {type(data).__name__}"
            )
        return data

    async def get_order_documents(self, order_id: str) -> dict[str, object]:
        """GET /orders/{order_id}/documents — generated documents for an order."""
        return await self._get_json(f"/orders/{order_id}/documents")

    async def set_qr_token(self, order_id: str, jti: str) -> dict[str, object]:
        """POST /orders/{order_id}/qr-token — attach a QR token JTI to an order."""
        return await self._post_json(f"/orders/{order_id}/qr-token", json={"jti": jti})

    async def mark_paid_held(
        self,
        order_id: str,
        *,
        payment_id: str | None = None,
        payment_link_id: str | None = None,
        event: str | None = None,
        event_id: str | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {}
        if payment_id is not None:
            payload["payment_id"] = payment_id
        if payment_link_id is not None:
            payload["payment_link_id"] = payment_link_id
        if event is not None:
            payload["event"] = event
        if event_id is not None:
            payload["event_id"] = event_id
        return await self._post_json(f"/orders/{order_id}/paid_held", json=payload)

    async def patch_order_status(
        self,
        order_id: str,
        status: str,
        *,
        payment_id: str | None = None,
        payment_link_id: str | None = None,
        event: str | None = None,
        event_id: str | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {"status": status}
        if payment_id is not None:
            payload["payment_id"] = payment_id
        if payment_link_id is not None:
            payload["payment_link_id"] = payment_link_id
        if event is not None:
            payload["event"] = event
        if event_id is not None:
            payload["event_id"] = event_id
        data = await self._request("PATCH", f"/orders/{order_id}/status", json=payload)
        if not isinstance(data, dict):
            raise ValClientError(f"expected an object at PATCH /orders/{order_id}/status")
        return data

val_client = ValClient()


__all__ = [
    "ExtractResult",
    "InvalidInputError",
    "NotFoundError",
    "ServiceUnavailable",
    "ValClient",
    "ValClientError",
    "val_client",
]
