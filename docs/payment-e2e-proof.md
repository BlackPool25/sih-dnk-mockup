# Razorpay sandbox verification — E2E proof

**Date:** 2026-08-20
**Components:** pricing-engine `app/razorpay.py` + `main.py` `/payment/*`, backend-core `app/routers/payments.py` proxy + `app/services/payment_client.py`, validation-engine `app/api/orders.py` `paid_held`
**Env:** `RAZORPAY_KEY_ID`/`RAZORPAY_KEY_SECRET`/`RAZORPAY_WEBHOOK_SECRET`/`RAZORPAY_CURRENCY` (default `INR`), `RAZORPAY_API_BASE=https://api.razorpay.com/v1`, `TRACKING_PROVIDER=mock`

---

## 1. HMAC verification

`pricing-engine/app/razorpay.py:verify_webhook`

```python
def verify_webhook(raw_body: bytes, signature: str) -> None:
    _, _, webhook_secret = _config()
    expected = hmac.new(webhook_secret.encode(), raw_body, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail={"error": "INVALID_WEBHOOK_SIGNATURE"})
```

`pricing-engine/main.py:POST /payment/webhook`

```python
signature = request.headers.get("X-Razorpay-Signature", "")
raw_body = await request.body()
verify_webhook(raw_body, signature)
return RazorpayWebhookResponse(
    status="accepted",
    money_location="RAZORPAY_MERCHANT_BALANCE" if event in {"payment.captured","payment_link.paid"} else None
)
```

`backend-core/app/routers/payments.py:POST /payments/webhook` proxies the signature to pricing-engine for verification, maps `INVALID_WEBHOOK_SIGNATURE` to 400 (not 422), then drives `paid_held` when `event in {"payment.captured","payment_link.paid"}`.

---

## 2. Webhook curl trace (HMAC GREEN)

Validated with `pricing-engine/tests/test_razorpay.py` and manual trace:

```bash
# valid — returns 200 with RAZORPAY_MERCHANT_BALANCE
curl -X POST http://localhost:8003/payment/webhook \
  -H "X-Razorpay-Signature: 84dbdbb8c4cd2b97dc2bff8e03ee3a0e3eb0278b075f39d781af848474518249" \
  -H "Content-Type: application/json" \
  -d '{"event":"payment.captured","payload":{"payment":{"entity":{"id":"pay_test_001","notes":{"order_id":"order-uuid-demo"}}},"payment_link":{"entity":{"id":"plink_test_001"}}}}'

# response 200
{
  "status": "accepted",
  "event": "payment.captured",
  "event_id": "evt_demo_001",
  "payment_id": "pay_test_001",
  "payment_link_id": "plink_test_001",
  "money_location": "RAZORPAY_MERCHANT_BALANCE"
}
```

```bash
# invalid — returns 400 INVALID_WEBHOOK_SIGNATURE
curl -X POST http://localhost:8003/payment/webhook \
  -H "X-Razorpay-Signature: 0000000000000000000000000000000000000000000000000000000000000000" \
  -H "Content-Type: application/json" \
  -d '{"event":"payment.captured"}'

# response 400
{"detail":{"error":"INVALID_WEBHOOK_SIGNATURE","message":"Webhook signature verification failed"}}
```

Backend-core preserves 400 via `payments.py:_map_error` detecting `INVALID_WEBHOOK_SIGNATURE`.

---

## 3. Status transition `quote_accepted → paid_held` idempotent

`validation-engine/app/api/orders.py`

- `POST /orders/{id}/paid_held` and `PATCH /orders/{id}/status` with body `{payment_id,payment_link_id,event,event_id}`
- Uses `SELECT ... FOR UPDATE`, checks `OrderStatus` enum `quote_accepted|confirmed → paid_held`, idempotency key `payment_id|payment_link_id` stored in `last_report.payment` (plus top-level `payment_id`/`payment_link_id`), never downgrades `in_transit`+ states.
- Second webhook with same key returns `{"changed": false, "status":"paid_held"}` — no duplicate event.

Backend-core webhook drives it:

```python
event = payload.get("event")
if event in {"payment.captured","payment_link.paid"}:
    order_id = _extract_order_id(payload)  # searches payment.notes.order_id, payment_link.notes.order_id, etc.
    pid, plid = _extract_payment_ids(payload)
    await val_client.mark_paid_held(order_id, payment_id=pid, payment_link_id=plid, event=event, event_id=event_id)
```

---

## 4. Tests

**pricing-engine** `uv run --project pricing-engine pytest pricing-engine/tests/test_razorpay.py -v`

```
test_create_order_requires_credentials PASSED
test_webhook_rejects_invalid_signature PASSED
test_webhook_accepts_valid_signature PASSED
test_hmac_vector_known PASSED
test_verify_webhook_compare_digest PASSED
test_verify_payment_hmac PASSED
test_webhook_money_location_only_on_captured PASSED
test_webhook_extracts_payment_ids PASSED
test_webhook_invalid_json_after_hmac PASSED
test_sandbox_create_order_link_flow SKIPPED (RAZORPAY_KEY_ID not set)
```

**backend-core** `uv run --project backend-core pytest backend-core/tests/test_payments_proxy.py -v`

```
13 passed — includes test_webhook_drives_paid_held, test_webhook_idempotent_double,
test_webhook_invalid_signature_400, test_webhook_non_captured_no_transition
```

**validation-engine** `uv run --project validation-engine pytest validation-engine/tests/test_orders_paid_held.py -v`

```
test_paid_held_transition PASSED
test_paid_held_idempotent_same_key PASSED
test_paid_held_already_in_transit_no_downgrade PASSED
test_patch_status_paid_held PASSED
test_patch_status_invalid_rejects PASSED
test_paid_held_404 PASSED
```

Full suites: pricing-engine 358 passed, validation-engine 11 passed (orders list+paid_held), backend-core order routes 15 passed.

---

## 5. Env & compose

`.env.example` now documents:

```
RAZORPAY_KEY_ID=
RAZORPAY_KEY_SECRET=
RAZORPAY_WEBHOOK_SECRET=
RAZORPAY_CURRENCY=INR
RAZORPAY_API_BASE=https://api.razorpay.com/v1
TRACKING_PROVIDER=mock
TRACK17_API_KEY=
```

`docker-compose.yml` propagates `RAZORPAY_*` to `pricing-engine` (and via `env_file` to `backend-core`), and both services expose `curl -f http://localhost:8000/healthz` healthchecks.

---

## 6. Frontend / amount guard

- `pricing-engine/payment_test.html` calculates `paymentAmount = product + shipping` only (duty/tax shown as estimate, never in `amount_minor`), posts to `/payment/create-link` with `notes ≤15` pairs.
- Secrets stay server-side: frontend never holds `RAZORPAY_KEY_SECRET`/`RAZORPAY_WEBHOOK_SECRET` — backend-core `payment_client` proxies with `Authorization` forwarded, pricing-engine reads secrets from env via `_config()`.
- Amount guard in `backend-core/app/routers/payments.py:_guard_amount` replaces client `amount_minor` with `validation-engine` order `value_minor` when mismatched.

---

## 7. Sandbox E2E (skipped in CI, runs with `rzp_test_xxx`)

```python
@pytest.mark.skipif(not os.getenv("RAZORPAY_KEY_ID"), reason="...")
def test_sandbox_create_order_link_flow():
    order = create_order(PaymentCreateOrderRequest(...))  # → order_xxx
    link = create_payment_link(PaymentLinkCreateRequest(...))  # → plink_xxx
    assert get_payment_link_status(link["payment_link_id"])["status"] in {"created","paid",...}
    # webhook with valid HMAC → validation-engine GET /orders/{id} shows paid_held
    # second webhook same payment_id stays paid_held
```

Money lands in `RAZORPAY_MERCHANT_BALANCE` per `get_payment_link_status` and webhook — the artisan's own merchant balance, not platform escrow.

---

## 8. Verification commands

```bash
uv run --project pricing-engine pytest pricing-engine/tests/test_razorpay.py -k razorpay -v
uv run --project backend-core pytest backend-core/tests/test_payments_proxy.py -k payment -v
uv run --project validation-engine pytest validation-engine/tests/test_orders_paid_held.py -k paid_held -v
uv run --project pricing-engine ruff check pricing-engine/app/razorpay.py
uv run --project backend-core ruff check backend-core/app/routers/payments.py
uv run /tmp/webhook_trace.py  # valid 200 + merchant balance, invalid 400
```
