"""Typed httpx client for tracking-api.

Endpoints (tracking-api port 8004, container 8000):
- POST /shipments
- GET  /shipments/{tracking_number}
- POST /shipments/{tracking_number}/events
- GET  /shipments/{tracking_number}/events
- GET  /shipments?order_id=... (list per order if supported)

30s timeout, propagates Authorization/X-Request-Id.
"""

from __future__ import annotations

from typing import Any

import httpx

from storage.config import settings

_TIMEOUT = 30.0


class TrackingClientError(Exception):
    """Base for tracking client errors."""


class NotFoundError(TrackingClientError):
    """404 from tracking-api."""


class DuplicateError(TrackingClientError):
    """400 duplicate shipment."""


class InvalidInputError(TrackingClientError):
    """400/422 invalid input."""


class ServiceUnavailable(TrackingClientError):
    """tracking-api unreachable or 5xx."""


def _forward_headers(extra: dict[str, str] | None) -> dict[str, str]:
    if not extra:
        return {}
    out: dict[str, str] = {}
    for k in ("Authorization", "X-Request-Id", "X-Request-ID", "x-request-id"):
        if k in extra:
            out["X-Request-Id"] = extra[k] if k.lower() == "x-request-id" else extra[k]
            if k == "Authorization":
                out["Authorization"] = extra[k]
    if "authorization" in extra and "Authorization" not in out:
        out["Authorization"] = extra["authorization"]
    # keep Authorization case
    if extra.get("Authorization"):
        out["Authorization"] = extra["Authorization"]
    # deduplicate X-Request-Id
    if "X-Request-Id" not in out:
        for kk, vv in extra.items():
            if kk.lower() == "x-request-id":
                out["X-Request-Id"] = vv
    return out


class TrackingClient:
    """Async httpx wrapper over tracking-api."""

    def __init__(
        self,
        base_url: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = (base_url or settings.TRACKING_API_URL).rstrip("/")
        self._transport = transport

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, object] | None = None,
        params: dict[str, str | int] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        url = f"{self._base_url}{path}"
        client_kwargs: dict[str, Any] = {"timeout": httpx.Timeout(_TIMEOUT, connect=10.0)}
        if self._transport is not None:
            client_kwargs["transport"] = self._transport
        try:
            async with httpx.AsyncClient(**client_kwargs) as client:
                resp = await client.request(method, url, json=json, params=params, headers=headers)
                return resp
        except httpx.ConnectError as exc:
            raise ServiceUnavailable(f"tracking-api unreachable: {exc}") from exc
        except httpx.TimeoutException as exc:
            raise ServiceUnavailable(f"tracking-api timed out: {exc}") from exc

    def _handle_status(self, resp: httpx.Response) -> None:
        if resp.status_code == 404:
            try:
                detail = resp.json().get("detail", "not found")
            except Exception:
                detail = resp.text or "not found"
            raise NotFoundError(str(detail))
        if resp.status_code == 400:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            msg = str(detail)
            if "already registered" in msg.lower() or "duplicate" in msg.lower():
                raise DuplicateError(msg)
            raise InvalidInputError(msg)
        if resp.status_code == 422:
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise InvalidInputError(str(detail))
        if resp.status_code >= 500:
            raise ServiceUnavailable(f"tracking-api error {resp.status_code}")

    async def register_shipment(
        self,
        tracking_number: str,
        carrier: str,
        order_id: str | None = None,
        parcel_id: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {"tracking_number": tracking_number, "carrier": carrier}
        if order_id is not None:
            payload["order_id"] = order_id
        if parcel_id is not None:
            payload["parcel_id"] = parcel_id
        resp = await self._request("POST", "/shipments", json=payload, headers=_forward_headers(headers))
        self._handle_status(resp)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise TrackingClientError("expected object at POST /shipments")
        return data

    async def get_shipment(
        self,
        tracking_number: str,
        headers: dict[str, str] | None = None,
    ) -> dict[str, object]:
        resp = await self._request("GET", f"/shipments/{tracking_number}", headers=_forward_headers(headers))
        self._handle_status(resp)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise TrackingClientError(f"expected object at GET /shipments/{tracking_number}")
        return data

    async def list_order_shipments(
        self,
        order_id: str,
        headers: dict[str, str] | None = None,
    ) -> list[dict[str, object]] | dict[str, object]:
        # tracking-api may expose GET /shipments?order_id=...
        resp = await self._request("GET", "/shipments", params={"order_id": order_id}, headers=_forward_headers(headers))
        # 404 on list is empty, not error; but handle gracefully
        if resp.status_code == 404:
            return []
        self._handle_status(resp)
        resp.raise_for_status()
        data = resp.json()
        # support both list and {shipments: [...]} shapes
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data
        raise TrackingClientError("expected list or object at GET /shipments")

    async def add_event(
        self,
        tracking_number: str,
        status: str,
        location: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {"status": status}
        if location is not None:
            payload["location"] = location
        resp = await self._request(
            "POST", f"/shipments/{tracking_number}/events", json=payload, headers=_forward_headers(headers)
        )
        self._handle_status(resp)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise TrackingClientError(f"expected object at POST /shipments/{tracking_number}/events")
        return data

    async def get_events(
        self,
        tracking_number: str,
        headers: dict[str, str] | None = None,
    ) -> list[dict[str, object]]:
        resp = await self._request("GET", f"/shipments/{tracking_number}/events", headers=_forward_headers(headers))
        self._handle_status(resp)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, list):
            raise TrackingClientError(f"expected list at GET /shipments/{tracking_number}/events")
        return data


tracking_client = TrackingClient()

__all__ = [
    "DuplicateError",
    "InvalidInputError",
    "NotFoundError",
    "ServiceUnavailable",
    "TrackingClient",
    "TrackingClientError",
    "tracking_client",
]
