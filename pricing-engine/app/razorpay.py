from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

from fastapi import HTTPException, status
from pydantic import BaseModel, Field, field_validator

RAZORPAY_API_BASE = "https://api.razorpay.com/v1"


class PaymentCreateOrderRequest(BaseModel):
    amount_minor: int = Field(gt=0, le=100_000_000_000)
    currency: str = Field(min_length=3, max_length=3)
    receipt: str = Field(min_length=1, max_length=40)
    notes: dict[str, str] = Field(default_factory=dict, max_length=15)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("currency must be a 3-letter currency code")
        return value


class PaymentCreateOrderResponse(BaseModel):
    key_id: str
    order_id: str
    amount: int
    currency: str
    receipt: str | None = None
    status: str


class PaymentLinkCreateRequest(BaseModel):
    amount_minor: int = Field(gt=0, le=100_000_000_000)
    currency: str = Field(min_length=3, max_length=3)
    reference_id: str = Field(min_length=1, max_length=40)
    description: str = Field(min_length=1, max_length=2048)
    notes: dict[str, str] = Field(default_factory=dict, max_length=15)
    customer_name: str | None = Field(default=None, max_length=100)
    customer_contact: str | None = Field(default=None, max_length=50)
    customer_email: str | None = Field(default=None, max_length=320)

    @field_validator("currency")
    @classmethod
    def validate_currency(cls, value: str) -> str:
        value = value.strip().upper()
        if len(value) != 3 or not value.isalpha():
            raise ValueError("currency must be a 3-letter currency code")
        return value


class PaymentLinkCreateResponse(BaseModel):
    payment_link_id: str
    short_url: str
    amount: int
    currency: str
    reference_id: str
    status: str
    destination: str


class PaymentLinkStatusResponse(BaseModel):
    payment_link_id: str
    reference_id: str
    status: str
    amount: int
    amount_paid: int
    currency: str
    payment_id: str | None
    destination: str
    money_location: str
    settlement_note: str


class PaymentVerifyRequest(BaseModel):
    razorpay_order_id: str = Field(min_length=1, max_length=100)
    razorpay_payment_id: str = Field(min_length=1, max_length=100)
    razorpay_signature: str = Field(min_length=1, max_length=200)


class PaymentVerifyResponse(BaseModel):
    verified: bool
    payment_id: str
    order_id: str
    payment_status: str
    order_status: str
    amount: int
    currency: str


class RazorpayWebhookResponse(BaseModel):
    status: str
    event: str | None = None
    event_id: str | None = None
    payment_id: str | None = None
    payment_link_id: str | None = None
    money_location: str | None = None


def _config() -> tuple[str, str, str]:
    key_id = os.getenv("RAZORPAY_KEY_ID", "").strip()
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "").strip()
    webhook_secret = os.getenv("RAZORPAY_WEBHOOK_SECRET", "").strip()
    if not key_id or not key_secret:
        raise HTTPException(status_code=500, detail={"error": "RAZORPAY_NOT_CONFIGURED", "message": "RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET are required"})
    return key_id, key_secret, webhook_secret


def _auth_header(key_id: str, key_secret: str) -> str:
    token = base64.b64encode(f"{key_id}:{key_secret}".encode()).decode("ascii")
    return f"Basic {token}"


def _request(method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    key_id, key_secret, _ = _config()
    body = json.dumps(payload, separators=(",", ":")).encode() if payload is not None else None
    request = Request(f"{RAZORPAY_API_BASE}{path}", data=body, headers={"Authorization": _auth_header(key_id, key_secret), "Content-Type": "application/json", "Accept": "application/json"}, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode())
    except HTTPError as exc:
        try:
            error_body = json.loads(exc.read().decode())
        except (UnicodeDecodeError, json.JSONDecodeError):
            error_body = {}
        raise HTTPException(status_code=502, detail={"error": "RAZORPAY_API_ERROR", "message": error_body.get("error", {}).get("description", "Razorpay API request failed")}) from exc
    except URLError as exc:
        raise HTTPException(status_code=502, detail={"error": "RAZORPAY_UNREACHABLE", "message": "Unable to reach Razorpay API"}) from exc


def _validate_currency(currency: str) -> None:
    configured = os.getenv("RAZORPAY_CURRENCY", "INR").strip().upper()
    if currency != configured:
        raise HTTPException(status_code=422, detail={"error": "INVALID_PAYMENT_CURRENCY", "message": f"Payment currency must be {configured}"})


def create_order(request: PaymentCreateOrderRequest) -> dict[str, Any]:
    key_id, _, _ = _config()
    _validate_currency(request.currency)
    order = _request("POST", "/orders", {"amount": request.amount_minor, "currency": request.currency, "receipt": request.receipt, "notes": request.notes})
    return {"key_id": key_id, "order_id": order["id"], "amount": order["amount"], "currency": order["currency"], "receipt": order.get("receipt"), "status": order["status"]}


def create_payment_link(request: PaymentLinkCreateRequest) -> dict[str, Any]:
    _validate_currency(request.currency)
    customer: dict[str, str] = {}
    if request.customer_name:
        customer["name"] = request.customer_name
    if request.customer_contact:
        customer["contact"] = request.customer_contact
    if request.customer_email:
        customer["email"] = request.customer_email
    payload: dict[str, Any] = {"amount": request.amount_minor, "currency": request.currency, "accept_partial": False, "reference_id": request.reference_id, "description": request.description, "reminder_enable": False, "notes": request.notes}
    if customer:
        payload["customer"] = customer
    link = _request("POST", "/payment_links", payload)
    return {"payment_link_id": link["id"], "short_url": link["short_url"], "amount": link["amount"], "currency": link["currency"], "reference_id": link["reference_id"], "status": link["status"], "destination": "RAZORPAY_MERCHANT_ACCOUNT"}


def get_payment_link_status(payment_link_id: str) -> dict[str, Any]:
    link = _request("GET", f"/payment_links/{quote(payment_link_id, safe='')}")
    payments = link.get("payments") or []
    payment_id = (payments[0].get("payment_id") or payments[0].get("id")) if payments else None
    status_value = str(link.get("status", "unknown"))
    amount_paid = int(link.get("amount_paid", 0) or 0)
    if status_value == "paid" or amount_paid > 0:
        money_location = "RAZORPAY_MERCHANT_BALANCE"
        settlement_note = "Payment is captured/received by the Razorpay merchant account. Final bank settlement is handled by Razorpay according to the merchant settlement cycle."
    elif status_value in {"cancelled", "expired"}:
        money_location = "NO_FUNDS_RECEIVED"
        settlement_note = "No successful payment is currently recorded for this Payment Link."
    else:
        money_location = "BUYER"
        settlement_note = "The customer has not completed a successful payment yet."
    return {"payment_link_id": link["id"], "reference_id": link.get("reference_id", ""), "status": status_value, "amount": int(link.get("amount", 0) or 0), "amount_paid": amount_paid, "currency": link.get("currency", ""), "payment_id": payment_id, "destination": "RAZORPAY_MERCHANT_ACCOUNT", "money_location": money_location, "settlement_note": settlement_note}


def verify_payment(request: PaymentVerifyRequest) -> dict[str, Any]:
    _, key_secret, _ = _config()
    message = f"{request.razorpay_order_id}|{request.razorpay_payment_id}".encode()
    expected = hmac.new(key_secret.encode(), message, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, request.razorpay_signature):
        raise HTTPException(status_code=400, detail={"error": "INVALID_PAYMENT_SIGNATURE", "message": "Payment signature verification failed"})
    payment = _request("GET", f"/payments/{quote(request.razorpay_payment_id, safe='')}")
    order = _request("GET", f"/orders/{quote(request.razorpay_order_id, safe='')}")
    if payment.get("order_id") != request.razorpay_order_id:
        raise HTTPException(status_code=400, detail={"error": "PAYMENT_ORDER_MISMATCH", "message": "Payment does not belong to the supplied order"})
    return {"verified": True, "payment_id": payment["id"], "order_id": order["id"], "payment_status": payment["status"], "order_status": order["status"], "amount": payment["amount"], "currency": payment["currency"]}


def verify_webhook(raw_body: bytes, signature: str) -> None:
    _, _, webhook_secret = _config()
    if not webhook_secret:
        raise HTTPException(status_code=500, detail={"error": "RAZORPAY_WEBHOOK_NOT_CONFIGURED", "message": "RAZORPAY_WEBHOOK_SECRET is required"})
    expected = hmac.new(webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail={"error": "INVALID_WEBHOOK_SIGNATURE", "message": "Webhook signature verification failed"})
