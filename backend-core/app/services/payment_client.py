"""Typed httpx client for payments — proxies to pricing-engine /payment/*.

- POST /payment/create-order
- POST /payment/create-link
- GET  /payment/link-status/{id}
- POST /payment/verify
- POST /payment/webhook (raw body + signature)

Server-side secret stays in pricing-engine; backend-core only proxies.
10s timeout, 1 retry, propagates Authorization/X-Request-Id.
"""

from __future__ import annotations

from typing import Any

import httpx

from storage.config import settings

_TIMEOUT = 10.0
_RETRY = 1


class PaymentClientError(Exception):
    """Base for payment client errors."""


class NotFoundError(PaymentClientError):
    """404 from downstream."""


class InvalidInputError(PaymentClientError):
    """400/422 invalid input."""


class ServiceUnavailable(PaymentClientError):
    """pricing-engine unreachable or 5xx / Razorpay error."""


def _forward_headers(extra: dict[str, str] | None) -> dict[str, str]:
    if not extra:
        return {}
    out: dict[str, str] = {}
    for kk, vv in extra.items():
        low = kk.lower()
        if low == "authorization":
            out["Authorization"] = vv
        elif low == "x-request-id":
            out["X-Request-Id"] = vv
    # also direct
    if extra.get("Authorization"):
        out["Authorization"] = extra["Authorization"]
    if extra.get("X-Request-Id"):
        out["X-Request-Id"] = extra["X-Request-Id"]
    return out


class PaymentClient:
    """Async httpx wrapper over pricing-engine payment endpoints."""

    def __init__(
        self,
        base_url: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = (base_url or settings.PRICING_ENGINE_URL).rstrip("/")
        self._transport = transport

    async def _request_with_retry(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, object] | None = None,
        content: bytes | None = None,
        params: dict[str, str | int] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        url = f"{self._base_url}{path}"
        last_exc: Exception | None = None
        for attempt in range(_RETRY + 1):
            client_kwargs: dict[str, Any] = {"timeout": httpx.Timeout(_TIMEOUT, connect=5.0)}
            if self._transport is not None:
                client_kwargs["transport"] = self._transport
            try:
                async with httpx.AsyncClient(**client_kwargs) as client:
                    # content vs json: httpx handles one; prefer content if provided
                    kwargs: dict[str, Any] = {"headers": headers, "params": params}
                    if content is not None:
                        kwargs["content"] = content
                    elif json is not None:
                        kwargs["json"] = json
                    resp = await client.request(method, url, **kwargs)
                    return resp
            except (httpx.ConnectError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt < _RETRY:
                    continue
                raise ServiceUnavailable(f"pricing-engine unreachable: {exc}") from exc
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
                j = resp.json()
                detail = j.get("detail", j) if isinstance(j, dict) else j
            except Exception:
                detail = resp.text
            raise InvalidInputError(str(detail))
        if resp.status_code >= 500:
            # pricing-engine surfaces Razorpay errors as 502 with JSON detail
            try:
                detail = resp.json()
                raise ServiceUnavailable(str(detail))
            except ServiceUnavailable:
                raise
            except Exception:
                raise ServiceUnavailable(f"pricing-engine error {resp.status_code}")

    async def create_order(
        self,
        amount_minor: int,
        currency: str,
        receipt: str,
        notes: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "amount_minor": amount_minor,
            "currency": currency,
            "receipt": receipt,
            "notes": notes or {},
        }
        resp = await self._request_with_retry(
            "POST", "/payment/create-order", json=payload, headers=_forward_headers(headers)
        )
        self._handle_status(resp)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise PaymentClientError("expected object at POST /payment/create-order")
        return data

    async def create_link(
        self,
        amount_minor: int,
        currency: str,
        reference_id: str,
        description: str,
        customer: dict[str, str] | None = None,
        notes: dict[str, str] | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "amount_minor": amount_minor,
            "currency": currency,
            "reference_id": reference_id,
            "description": description,
            "notes": notes or {},
        }
        if customer:
            for k in ("customer_name", "customer_contact", "customer_email"):
                if customer.get(k):
                    payload[k] = customer[k]
        resp = await self._request_with_retry(
            "POST", "/payment/create-link", json=payload, headers=_forward_headers(headers)
        )
        self._handle_status(resp)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise PaymentClientError("expected object at POST /payment/create-link")
        return data

    async def get_link_status(
        self,
        payment_link_id: str,
        headers: dict[str, str] | None = None,
    ) -> dict[str, object]:
        resp = await self._request_with_retry(
            "GET", f"/payment/link-status/{payment_link_id}", headers=_forward_headers(headers)
        )
        self._handle_status(resp)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise PaymentClientError(f"expected object at GET /payment/link-status/{payment_link_id}")
        return data

    async def verify_payment(
        self,
        razorpay_order_id: str,
        razorpay_payment_id: str,
        razorpay_signature: str,
        headers: dict[str, str] | None = None,
    ) -> dict[str, object]:
        payload: dict[str, object] = {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        }
        resp = await self._request_with_retry(
            "POST", "/payment/verify", json=payload, headers=_forward_headers(headers)
        )
        self._handle_status(resp)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise PaymentClientError("expected object at POST /payment/verify")
        return data

    async def proxy_webhook(
        self,
        raw_body: bytes,
        signature: str,
        event_id: str | None = None,
        headers: dict[str, str] | None = None,
    ) -> dict[str, object]:
        fwd = _forward_headers(headers)
        fwd["X-Razorpay-Signature"] = signature
        if event_id:
            fwd["x-razorpay-event-id"] = event_id
        fwd["Content-Type"] = "application/json"
        resp = await self._request_with_retry(
            "POST", "/payment/webhook", content=raw_body, headers=fwd
        )
        self._handle_status(resp)
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            raise PaymentClientError("expected object at POST /payment/webhook")
        return data


payment_client = PaymentClient()

__all__ = [
    "InvalidInputError",
    "NotFoundError",
    "PaymentClient",
    "PaymentClientError",
    "ServiceUnavailable",
    "payment_client",
]
