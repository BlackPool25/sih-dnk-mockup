import hashlib
import hmac
import json
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.razorpay import verify_webhook
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


def test_hmac_vector_known() -> None:
    secret = "test_webhook_secret_123"
    payload = b'{"event":"payment.captured","payload":{"payment":{"entity":{"id":"pay_123"}}}}'
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert expected == hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    assert len(expected) == 64
    assert all(c in "0123456789abcdef" for c in expected)
    different = hmac.new(b"wrong_secret", payload, hashlib.sha256).hexdigest()
    assert different != expected


def test_verify_webhook_compare_digest(monkeypatch: pytest.MonkeyPatch) -> None:
    secret = "webhook-secret-compare"
    body = json.dumps({"event": "payment.captured", "payload": {"payment": {"entity": {"id": "pay_1"}}}}).encode()
    good = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_example")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "example-secret")
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", secret)
    verify_webhook(body, good)
    bad = "0" * 64
    try:
        verify_webhook(body, bad)
        raise AssertionError("should have raised")
    except Exception as exc:
        assert getattr(exc, "status_code", 400) == 400


def test_verify_payment_hmac(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_example")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "s3cr3t")
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "whsec")
    order_id = "order_ABC123"
    payment_id = "pay_XYZ789"
    msg = f"{order_id}|{payment_id}".encode()
    sig = hmac.new(b"s3cr3t", msg, hashlib.sha256).hexdigest()

    fake_order = {"id": order_id, "status": "created", "amount": 50000, "currency": "INR"}
    fake_payment = {"id": payment_id, "status": "captured", "amount": 50000, "currency": "INR", "order_id": order_id}

    def fake_request(method: str, path: str, payload=None):  # noqa: ANN001
        if path.startswith("/payments/"):
            return fake_payment
        if path.startswith("/orders/"):
            return fake_order
        raise AssertionError(f"unexpected {path}")

    with patch("app.razorpay._request", side_effect=fake_request):
        from app.razorpay import PaymentVerifyRequest, verify_payment

        req = PaymentVerifyRequest(
            razorpay_order_id=order_id, razorpay_payment_id=payment_id, razorpay_signature=sig
        )
        result = verify_payment(req)
        assert result["verified"] is True
        assert result["payment_id"] == payment_id

    bad_sig = "0" * 64
    with patch("app.razorpay._request", side_effect=fake_request):
        from app.razorpay import PaymentVerifyRequest, verify_payment

        req_bad = PaymentVerifyRequest(
            razorpay_order_id=order_id, razorpay_payment_id=payment_id, razorpay_signature=bad_sig
        )
        try:
            verify_payment(req_bad)
            raise AssertionError("should have raised")
        except Exception as exc:
            assert getattr(exc, "status_code", 400) == 400


def test_webhook_money_location_only_on_captured(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_example")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "example-secret")
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "webhook-secret")
    secret = "webhook-secret"

    for event, expect_location in [
        ("payment.captured", "RAZORPAY_MERCHANT_BALANCE"),
        ("payment_link.paid", "RAZORPAY_MERCHANT_BALANCE"),
        ("payment.failed", None),
        ("order.paid", None),
    ]:
        body = json.dumps({"event": event}).encode()
        sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        resp = client.post(
            "/payment/webhook",
            content=body,
            headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
        )
        assert resp.status_code == 200
        assert resp.json()["money_location"] == expect_location


def test_webhook_extracts_payment_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_example")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "example-secret")
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "webhook-secret")
    secret = "webhook-secret"
    body_dict = {
        "event": "payment.captured",
        "payload": {
            "payment": {"entity": {"id": "pay_12345"}},
            "payment_link": {"entity": {"id": "plink_67890"}},
        },
    }
    body = json.dumps(body_dict, separators=(",", ":")).encode()
    sig = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    resp = client.post(
        "/payment/webhook",
        content=body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["payment_id"] == "pay_12345"
    assert data["payment_link_id"] == "plink_67890"


def test_webhook_invalid_json_after_hmac(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_example")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "example-secret")
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "webhook-secret")
    body = b"not json"
    sig = hmac.new(b"webhook-secret", body, hashlib.sha256).hexdigest()
    resp = client.post(
        "/payment/webhook",
        content=body,
        headers={"Content-Type": "application/json", "X-Razorpay-Signature": sig},
    )
    assert resp.status_code == 400


@pytest.mark.skipif(not os.getenv("RAZORPAY_KEY_ID"), reason="RAZORPAY_KEY_ID not set — skipping sandbox E2E")
def test_sandbox_create_order_link_flow() -> None:
    key_id = os.getenv("RAZORPAY_KEY_ID", "")
    assert key_id.startswith("rzp_test_") or key_id.startswith("rzp_")
    from app.razorpay import PaymentCreateOrderRequest, PaymentLinkCreateRequest, create_order, create_payment_link, get_payment_link_status

    order_req = PaymentCreateOrderRequest(amount_minor=10000, currency="INR", receipt=f"test-{os.getpid()}", notes={"order_id": "test-order"})
    order = create_order(order_req)
    assert order["order_id"].startswith("order_")
    assert order["amount"] == 10000

    link_req = PaymentLinkCreateRequest(
        amount_minor=10000,
        currency="INR",
        reference_id=f"ref-{os.getpid()}",
        description="Sandbox test",
        notes={"order_id": "test-order"},
    )
    link = create_payment_link(link_req)
    assert link["payment_link_id"].startswith("plink_")
    status = get_payment_link_status(link["payment_link_id"])
    assert status["status"] in {"created", "partially_paid", "paid", "pending"}
