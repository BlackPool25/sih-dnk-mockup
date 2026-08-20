"""Typed httpx client for pricing — via validation-engine order pricing + direct pricing-engine.

- query_pricing(order_id)  → GET  /orders/{id}/pricing  (validation-engine)
- trigger_pricing(order_id) → POST /orders/{id}/pricing (validation-engine)
- calculate(payload)        → POST /pricing             (pricing-engine direct)

Mirrors ``val_client`` error mapping: 404 → NotFoundError, 422/400 → InvalidInputError,
connect/timeout/5xx → ServiceUnavailable. 10s timeout, 1 retry, optional auth forwarding.
"""

from __future__ import annotations

from typing import Any

import httpx

from storage.config import settings

_TIMEOUT = 10.0
_RETRY = 1


class PricingClientError(Exception):
    """Base for pricing client errors."""


class NotFoundError(PricingClientError):
    """404 from downstream."""


class InvalidInputError(PricingClientError):
    """400/422 from downstream."""


class ServiceUnavailable(PricingClientError):
    """Downstream unreachable or 5xx."""


def _forward_headers(extra: dict[str, str] | None) -> dict[str, str]:
    """Build headers to propagate Authorization and X-Request-Id when present."""
    if not extra:
        return {}
    out: dict[str, str] = {}
    for k in ("Authorization", "X-Request-Id", "X-Request-ID", "x-request-id"):
        if k in extra:
            out[k] = extra[k]
            if k.lower() == "x-request-id":
                out["X-Request-Id"] = extra[k]
    # normalize lower-case variants
    if "authorization" in extra and "Authorization" not in out:
        out["Authorization"] = extra["authorization"]
    return out


class PricingClient:
    """Thin async httpx wrapper for pricing endpoints."""

    def __init__(
        self,
        base_url: str | None = None,
        validation_url: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._pricing_base = (base_url or settings.PRICING_ENGINE_URL).rstrip("/")
        self._validation_base = (validation_url or settings.VALIDATION_ENGINE_URL).rstrip("/")
        self._transport = transport

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        *,
        json: dict[str, object] | None = None,
        params: dict[str, str | int] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        last_exc: Exception | None = None
        for attempt in range(_RETRY + 1):
            client_kwargs: dict[str, Any] = {"timeout": httpx.Timeout(_TIMEOUT, connect=5.0)}
            if self._transport is not None:
                client_kwargs["transport"] = self._transport
            try:
                async with httpx.AsyncClient(**client_kwargs) as client:
                    resp = await client.request(method, url, json=json, params=params, headers=headers)
                    return resp
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt < _RETRY:
                    continue
                raise ServiceUnavailable(f"pricing downstream unreachable: {exc}") from exc
        assert last_exc is not None
        raise ServiceUnavailable(str(last_exc))

    def _handle_status(self, resp: httpx.Response) -> None:
        if resp.status_code == 404:
            try:
                detail = resp.json().get("detail", "not found")
            except Exception:
                detail = resp.text or "not found"
            raise NotFoundError(str(detail))
        if resp.status_code in (400, 422):
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text or "invalid input"
            raise InvalidInputError(str(detail))
        if resp.status_code >= 500:
            raise ServiceUnavailable(f"pricing downstream error {resp.status_code}")
        if resp.status_code >= 400:
            # generic 4xx -> InvalidInput for 422/400, else NotFound/InvalidInput best-effort
            try:
                detail = resp.json().get("detail", resp.text)
            except Exception:
                detail = resp.text
            raise InvalidInputError(str(detail))

    async def query_pricing(
        self,
        order_id: str,
        headers: dict[str, str] | None = None,
    ) -> dict[str, object]:
        """GET /orders/{order_id}/pricing via validation-engine."""
        url = f"{self._validation_base}/orders/{order_id}/pricing"
        resp = await self._request_with_retry("GET", url, headers=_forward_headers(headers))
        self._handle_status(resp)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise PricingClientError(f"expected object at /orders/{order_id}/pricing")
        return data

    async def trigger_pricing(
        self,
        order_id: str,
        headers: dict[str, str] | None = None,
    ) -> dict[str, object]:
        """POST /orders/{order_id}/pricing via validation-engine."""
        url = f"{self._validation_base}/orders/{order_id}/pricing"
        resp = await self._request_with_retry("POST", url, headers=_forward_headers(headers))
        self._handle_status(resp)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise PricingClientError(f"expected object at POST /orders/{order_id}/pricing")
        return data

    async def calculate(
        self,
        payload: dict[str, object],
        headers: dict[str, str] | None = None,
    ) -> dict[str, object]:
        """Ad-hoc quote via validation-engine or full optimization via pricing-engine."""
        if "items" in payload:
            url = f"{self._pricing_base}/pricing"
        else:
            url = f"{self._validation_base}/pricing/calculate"
        resp = await self._request_with_retry("POST", url, json=payload, headers=_forward_headers(headers))
        self._handle_status(resp)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise PricingClientError(f"expected object at POST {url}")
        return data

    # Backwards compat alias
    async def query_pricing_direct(
        self,
        payload: dict[str, object],
        headers: dict[str, str] | None = None,
    ) -> dict[str, object]:
        return await self.calculate(payload, headers=headers)


pricing_client = PricingClient()

__all__ = [
    "InvalidInputError",
    "NotFoundError",
    "PricingClient",
    "PricingClientError",
    "ServiceUnavailable",
    "pricing_client",
]
