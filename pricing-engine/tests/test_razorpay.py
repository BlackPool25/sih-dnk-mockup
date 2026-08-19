import hashlib
import hmac
import json

import pytest
from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_create_order_requires_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("RAZORPAY_KEY_ID", raising=False)
    monkeypatch.delenv("RAZORPAY_KEY_SECRET", raising=False)

    response = client.post(
        "/payment/create-order",
        json={"amount_minor": 10000, "currency": "INR", "receipt": "test-001"},
    )

    assert response.status_code == 500
    assert response.json()["detail"]["error"] == "RAZORPAY_NOT_CONFIGURED"


def test_webhook_rejects_invalid_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_example")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "example-secret")
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "webhook-secret")

    response = client.post(
        "/payment/webhook",
        headers={"X-Razorpay-Signature": "invalid"},
        json={"event": "payment.captured"},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "INVALID_WEBHOOK_SIGNATURE"


def test_webhook_accepts_valid_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "webhook-secret"
    body = json.dumps({"event": "payment.captured"}, separators=(",", ":")).encode()
    signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()

    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_example")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "example-secret")
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", secret)

    response = client.post(
        "/payment/webhook",
        content=body,
        headers={
            "Content-Type": "application/json",
            "X-Razorpay-Signature": signature,
            "x-razorpay-event-id": "evt_test_001",
        },
    )

    assert response.status_code == 200
    assert response.json() == {
        "status": "accepted",
        "event": "payment.captured",
        "event_id": "evt_test_001",
        "payment_id": None,
        "payment_link_id": None,
        "money_location": "RAZORPAY_MERCHANT_BALANCE",
    }
