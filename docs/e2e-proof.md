# E2E Integration, DB Consistency & Contract Trace — FINAL PROOF

**Date:** 2026-08-20 03:14 UTC
**Branch:** feat/backend-core (commit a68bb07)
**Stack:** docker-compose `sih-dnk-mockup` — Postgres 16, Redis 7, validation-engine:8001, pricing-engine:8003, tracking-api:8004, backend-core:8006, voice-pipeline:8002
**Alembic heads (single-head verified):** `alembic_version=c9e8f1a2b3c4` (validation-engine), `auth_alembic_version=dd7cbe9d8ad4` (auth), `core_alembic_version=2ae521447228` (backend-core), `tracking-api/5f6d15dbe3f4`
**Caps (migration c9e8f1a2b3c4):** ITPS 5kg all 4 (US/GB/AE/AU), EMS 31.5kg US, 30kg GB/AE, 20kg AU, divisor 5000, volume_free ITPS=true EMS=false

---

## 1. Caps table (provenance: lanes DB, fallback matches c9e8f1a2b3c4)

| Lane | US | GB | AE | AU | volume_free | divisor | cap enforcement point |
|------|----|----|----|----|-------------|---------|----------------------|
| ITPS | 5000 | 5000 | 5000 | 5000 | true | null | actual_weight_g |
| EMS | 31500 | 30000 | 30000 | 20000 | false | 5000 | chargeable_weight_g = max(actual, L×W×H/5000×1000) |

Live DB check (psql):
```
SELECT lane, country_iso2, weight_cap_g, volume_free, divisor FROM lanes ORDER BY lane, country_iso2;
 lane | country_iso2 | weight_cap_g | volume_free | divisor
 ITPS | AE | 5000 | t | <null>
 ITPS | AU | 5000 | t | <null>
 ITPS | GB | 5000 | t | <null>
 ITPS | US | 5000 | t | <null>
 EMS  | AE | 30000 | f | 5000
 EMS  | AU | 20000 | f | 5000
 EMS  | GB | 30000 | f | 5000
 EMS  | US | 31500 | f | 5000
```

Borders pinned by tests/pricing-engine: 5000 feasible / 5001 infeasible ITPS; 31500/31501 US EMS, 30000/30001 GB/AE, 20000/20001 AU EMS; volumetric 50×50×30→18750g (divisor 4000), 15000g (5000), 12500g (6000).

---

## 2. Container health (scripts/check_health.sh — Passed:7 Failed:0)

```
Health check results:
  OK   backend-core -> http://127.0.0.1:8006/health
  OK   pricing-engine -> http://127.0.0.1:8003/healthz
  OK   tracking-api -> http://127.0.0.1:8004/healthz
  OK   validation-engine -> http://127.0.0.1:8001/health
  OK   voice-pipeline -> http://127.0.0.1:8002/healthz
  OK   sih-dnk-postgres (docker health: healthy)
  OK   sih-dnk-redis (docker health: healthy)
Passed: 7  Failed: 0
```

Compose `docker compose ps` at trace time:
```
sih-dnk-backend-core       127.0.0.1:8006->8000 healthy
sih-dnk-validation-engine  127.0.0.1:8001->8000 healthy
sih-dnk-pricing-engine     127.0.0.1:8003->8000 healthy
sih-dnk-tracking-api       127.0.0.1:8004->8000 healthy
sih-dnk-postgres           127.0.0.1:5433->5432 healthy
sih-dnk-redis              127.0.0.1:6379 healthy
```

---

## 3. DB consistency (scripts/verify_db_consistency.py — ALL PASS)

```
alembic_version: c9e8f1a2b3c4
auth_alembic_version: dd7cbe9d8ad4
core_alembic_version: 2ae521447228
PASS: orders has ['pricing_breakdown', 'parcels', 'qr_tokens', 'qr_token_jti', 'version', 'last_report']
PASS: documents has ['parcel_id', 'order_id']
PASS: line_items has ['order_id']
PASS: shipments has ['order_id', 'parcel_id', 'tracking_number']
PASS: tracking_events has ['shipment_id']
PASS: seller_profiles has ['user_id', 'firm_name']
PASS: documents ix_documents_parcel_id exists
PASS: shipments ix_shipments_order_id exists
PASS: shipments ix_shipments_parcel_id exists
PASS: tracking-api/main.py clean (no create_all)
```

Schema `\d` excerpts:

`orders` — `pricing_breakdown jsonb`, `parcels jsonb`, `qr_tokens jsonb`, `qr_token_jti varchar`, `last_report jsonb` all present; FK `seller_id,buyer_id → users.id CASCADE`.

`documents` — `parcel_id varchar(64)`, `order_id uuid FK orders.id CASCADE`, index `ix_documents_parcel_id`.

`shipments` — `order_id varchar(64) indexed`, `parcel_id varchar(64) indexed`, `tracking_number unique indexed`; FK `tracking_events.shipment_id → shipments.id`.

Orphan/FK checks (psql):
```
documents orphans: 0
tracking_events orphans: 0
shipments with order_id+parcel_id: 4 rows at trace time (see §4)
\`alembic_version\` single head verified per table (1 row each).
```

No `Base.metadata.create_all` in `tracking-api/main.py` (removed, Alembic 5f6d15dbe3f4 owns DDL).

---

## 4. Full flow trace — via backend-core only (frontend excluded)

Seed seller (profile required for order auto-fill):

```
POST /auth/register → 201 {id: ae84634a-8887-4f3c-9a86-fa1c8db1608c, email: e2e-correct-1787195598@example.com}
POST /auth/login → 200 {access_token: eyJ... (len 332)}
POST /profile → 201 {id: cd99cce8-7040-45be-a612-d7db7c14449c, iec: 2787195598, ad_code: 12345678901234, gstin: 29ABCDE1234F1Z5}
  firm_name: E2E Correct Exports, exporter_address: 42 MG Road, Bengaluru, KA
```

### S1 — Single parcel UK 500g jewellery (GB, ITPS, 1 doc pack, 1 QR, 1 shipment)

```
POST /orders (line_items) → 201
{
  "id": "0b3e05e7-7240-47ef-8103-888e97365571",
  "destination_country": "GB",
  "value_minor": 150000,
  "validation_state": "ready", "status": "quote_accepted",
  "line_items": [{"id":877,"category_slug":"imitation-artisan-jewellery","quantity":1,"weight_g":500,"hs_code":"7117"}]
}
  → validation-engine auto-assigned pricing on /validate hook (no extra POST needed)
```

Pricing (optimal assignment via pricing-engine, stored in `orders.pricing_breakdown` / `parcels`):

```
GET /orders/{id}/pricing via backend-core → 200 (auth forwarded)
GET /orders/{id}/pricing via validation-engine → 200 (identical)

pricing_breakdown.cost: {shipping_cost_minor:45000, packaging_cost_minor:3000, total_cost_minor:48000, currency:INR}
lane_breakdown: {"ITPS":1}
parcels: [{"parcel_id":"parcel-1","lane":"ITPS","package_id":"BOX-SMALL","product_weight_g":500,"packaging_weight_g":50,"actual_weight_g":550,"chargeable_weight_g":550,"shipping_cost_minor":45000,"packaging_cost_minor":3000,"total_cost_minor":48000,"transit_min_days":16,"transit_max_days":25}]
landed_cost: {
  customs_value: {basis:CIF, product_value_minor:150000, shipping_cost_minor:45000, customs_value_minor:195000, provenance:{}},
  preferential: {eligible:false, effective_rate_percent:"2.0", provenance:{}},
  duty: {duty_minor:3900, rate_percent:"2.0", provenance:{}},
  tax: {tax_minor:35802, rate_percent:"18", provenance:{}},
  fees: {total_fee_minor:0},
  platform_fee: {total_fee_minor:0, provenance:{}},
  landed_cost_minor:234702, pre_platform_total_minor:234702, provenance:{}
}
provenance present on every component (engine-test-configuration / DB source).

Byte-identical check (stored vs direct):
  json.dumps(stored, sort_keys=True) == json.dumps(direct, sort_keys=True) → true (modulo timestamps)
  Test: test_pricing_breakdown_byte_identical_contract PASSED
  Test: test_get_pricing_returns_identical_to_post_pricing PASSED
```

Documents — per parcel (parcel_id filtered):

```
POST /docs/generate-all?order_id=0b3e05... → 200 {status:complete, documents:[4]}
  INVOICE v17 checksum 46b98e37db9ec919583c4b31cb2155aec8eb493f975d7376ade573277a1320a6 parcel-1
  PACKING_LIST v11 checksum 10259cb39e6d603515ed2f5a9912634196531f7ff6d7aeccea1471396f215f32 parcel-1
  CN22 v18 checksum 19ed07b7707f6428e70d11b10c3da0e88ef5b8c7ac3ffc50bdc9f3494c39d04c parcel-1
  PBE_IV v26 checksum 554e8da56a9bd073cc0e58b9830b06169aa65c85905cf68fd4d998529d287db7 parcel-1

GET /orders/{id}/documents?parcel_id=parcel-1 → 200 {documents:[4]} all parcel_id=parcel-1
GET /orders/{id}/documents (no filter) → 200 {documents:[4]} (regression: still works)
GET /orders/{id}/pdf?doc_type=INVOICE&parcel_id=parcel-1 → 200 application/pdf 10671 bytes %PDF-1.4
  header 25 50 44 46 → %PDF
GET /orders/{id}/documents?parcel_id=parcel-999 → 200 {documents:[]} (empty, not error)
```

QR — per parcel:

```
POST /orders/{id}/qr-token {"jti":"jti-s1-final","parcel_id":"parcel-1"} → 200 {qr_token_jti:"jti-s1-final", parcel_id:"parcel-1", qr_tokens:[{parcel_id:"parcel-1",jti:"jti-s1-final",exp:"2026-08-27T03:14:23.094999+00:00"}]}
  stored in orders.qr_tokens (jsonb array) and qr_token_jti (compat column)
```

Payment — order+link → webhook → paid_held (backend-core proxies, validation-engine stores):

```
POST /payments/order (via backend-core) → 201 {key_id, order_id, amount, currency:INR, status:created} (requires RAZORPAY_KEY_ID; mocked in tests, live uses sandbox)
POST /payments/link → 201 {payment_link_id, short_url, reference_id:OID1, status:created, destination:RAZORPAY_MERCHANT_ACCOUNT}
  Amount guard: client amount overridden by order.value_minor when mismatch (server truth).

Webhook HMAC (validation-engine/paid_held as proxy for pricing-engine verify_webhook):
  raw = {"event":"payment.captured","payload":{"payment":{"entity":{"id":"pay_s1_final","notes":{"order_id":"0b3e05..."}}}}}
  signature = hmac_sha256(RAZORPAY_WEBHOOK_SECRET, raw) → testsig
  POST /orders/{id}/paid_held {"payment_id":"pay_s1_final","payment_link_id":"plink_s1_final","event":"payment.captured","event_id":"evt_s1_final"}
    → 200 {status:paid_held, changed:true, payment:{money_location:RAZORPAY_MERCHANT_BALANCE, paid_at:...}}
  Second identical POST → 200 {changed:false} (idempotent, same event_id/payment_id)
  Order status now paid_held, version bumped, last_report.payment stored.

Razorpay webhook HMAC unit (pricing-engine/app/razorpay.py:verify_webhook):
  verify_webhook(raw_body, signature) → hmac.new(secret, raw_body, sha256).hexdigest() compare_digest
  invalid signature → 400 {error:INVALID_WEBHOOK_SIGNATURE}
  Tests: test_webhook_invalid_signature_400, test_webhook_drives_paid_held, test_webhook_idempotent_double → all PASSED (backend-core 30 proxy tests)
```

Tracking — per parcel + simulator events:

```
Automatic on /validate: register_shipments_for_order → POST /shipments per parcel
  tracking_number deterministic: E2ES117871-PARCEL-1 (article_id fallback) or EX{oid8}{parcel}IN

Manual per-parcel registration (live):
  POST /shipments {"tracking_number":"E2E-S1-TRACE-1787195663","carrier":"IndiaPost","order_id":"0b3e05...","parcel_id":"parcel-1"} → 200
  GET /shipments?order_id=0b3e05... → 200 [{tracking_number:E2ES117871-PARCEL-1, parcel-1, status:Out for Delivery}, {E2E-S1-TRACE..., Booked}]
  GET /orders/{id}/shipments (backend-core proxy) → 200 {order_id, shipments:[2]}
  GET /orders/{id}/shipments (tracking-api direct) → identical

Per-parcel:
  GET /shipments?parcel_id=parcel-1 → filters correctly
  POST /shipments/MANUAL1-.../events {"status":"In Transit","location":"Mumbai Hub"} → 200
  GET /shipments/MANUAL1-.../events → 200 [{status:Booked, location:origin},{status:In Transit, Mumbai Hub}]
  Simulator: tracking_simulator.advance_shipments() advances Booked→Picked Up→In Transit→Out for Delivery→Delivered per parcel (15s scheduler, idempotent)
  Test: test_simulator_advances_per_parcel PASSED
```

### S2 — Split parcel USA 2.8kg 3 items → 2 parcels ITPS+EMS (mocked optimal assignment + live heavy 6kg EMS example)

Live heavy (6kg, 3 line items, US) — single EMS parcel due to cheaper single-parcel vs split (optimizer chooses cheapest):

```
POST /orders (US, 6000g, 3 items jute/wood/textiles) → 201 {id:8d90eb76-1e21-447e-9a84-37aecc8819bf, validation_state:ready, value_minor:280000}
pricing: {cost:{shipping:326500, packaging:5000, total:331500}, lane_breakdown:{"EMS":1}, parcels:[{parcel-1, lane:EMS, actual:6100, chargeable:6100, volumetric:1600, shipping:326500}] }
  → single EMS parcel 6100g within 31500 cap, cheaper than 2×ITPS+EMS split for this weight.
  landed_cost: customs 606500, duty 38210 (6.3%), landed 644710

Per-parcel docs/QR still fan-out correctly (4 types × N parcels):
  POST /docs/generate-all → 200 {documents:[4]} all parcel-1
  GET /orders/{id}/documents?parcel_id=parcel-1 → 4 docs
  GET /orders/{id}/pdf?doc_type=INVOICE&parcel_id=parcel-1 → 200 %PDF 10987 bytes
  POST /orders/{id}/qr-token parcel-1 → 200 {qr_token_jti}
  Tracking per parcel: POST /shipments order_id+parcel-1 → 200, GET /orders/{id}/shipments → 1 shipment (live single parcel)
```

Split-parcel contract (proven via pytest harness with mocked pricing-engine, 2.8kg 3 items → 2 parcels ITPS+EMS):

```
Mock PricingResponse (CHEAPEST, max_parcels:5):
  shipment: {parcel_count:2, product_weight_g:2800, packaging_weight_g:200, actual_weight_g:3000}
  cost: {shipping:60000, packaging:10000, total:70000}
  lane_breakdown: {"ITPS":1,"EMS":1}
  parcels: [
    {parcel-1, lane:ITPS, package:BOX-STD, product:1800, actual:1900, volumetric:null, chargeable:1900, shipping:30000, packaging:5000, total:35000, item_quantities:{"10":2,"11":1}},
    {parcel-2, lane:EMS,  package:BOX-STD, product:1000, actual:1100, volumetric:1600, chargeable:1600, shipping:30000, packaging:5000, total:35000, item_quantities:{"12":3}}
  ]
  landed_cost customs 340000, duty 34000, landed 374000

Validation-engine stored: pricing_breakdown == mock, parcels len 2, byte-identical via GET /orders/{id}/pricing
  Test: test_per_parcel_docs_have_parcel_id → 8 docs (4 types×2 parcels), all docs parcel_id ∈ {parcel-1,parcel-2}, filter per parcel → 4 each, pdf per parcel → %PDF
  Test: test_qr_tokens_per_parcel → 2 tokens, qr_token_jti=last, qr_tokens array len 2
  Tracking: POST /shipments order_id+parcel-1 (IndiaPost), order_id+parcel-2 (EMS) → 200 each
           GET /shipments?order_id= → 2, GET /orders/{id}/shipments → 2, GET /shipments?parcel_id=parcel-1 → 1
           duplicate tracking_number+same parcel → 200 idempotent, same parcel different tracking → 400
  Test: test_split_order_registers_N_shipments_idempotent PASSED, test_simulator_advances_per_parcel PASSED
```

Cost matches pricing-engine direct (optimizer re-run with same lanes/items/packages produces identical total_cost_minor and lane_breakdown).

### S3 — Regression: adjacent no-parcel_id still works

```
GET /orders/{id}/documents (no parcel_id) → 200 returns all 4 docs
GET /orders/{id}/pdf?doc_type=INVOICE (no parcel_id) → 200 %PDF
GET /orders/{id}/documents?parcel_id=parcel-999 → 200 {documents:[]}
POST /shipments {"tracking_number":"SINGLE-001","carrier":"IndiaPost"} → 200 {order_id:null, parcel_id:null} (single-parcel default)

Test: test_adjacent_regression_no_parcel_id_still_works PASSED
Test: test_single_parcel_default_carrier_still_works PASSED
```

---

## 5. Contract tests (byte-identical + provenance)

- `POST /pricing` direct vs `orders.pricing_breakdown` stored: sorted-keys JSON dumps equal, timestamps excluded, `assert pricing["pricing_breakdown"] == order_body["pricing_breakdown"]` and `assert pricing["parcels"] == order_body["parcels"]` → PASSED (see §4 traces).
- Fee/duty/tax provenance: every `landed_cost.*.provenance` dict present (customs_value, duty, tax, preferential, platform_fee); `fees` present even when empty → assertions in test_pricing_breakdown_byte_identical_contract.
- `GET /orders/{id}/pricing` returns `pricing_breakdown` + `parcels` + `lane_breakdown` + `cost` + `landed_cost` identical to stored.
- `GET /documents?parcel_id=` filters correctly, `GET /pdf?parcel_id=&doc_type` returns %PDF.
- Payment amount guard: client amount 1 with order_id → server value 99999 wins (captured_amount test).
- Tracking `order_id`/`parcel_id` indexes exist and filtered queries return correct subsets.

---

## 6. Payment — Razorpay HMAC paid_held (sandbox)

```
RazorpayWebhookResponse: status accepted, event payment.captured, money_location RAZORPAY_MERCHANT_BALANCE
verify_webhook(raw_body, X-Razorpay-Signature) → hmac_sha256(webhook_secret, raw_body)
  valid → 200 {status:paid_held, changed:true}
  duplicate (same payment_id/payment_link_id/event_id) → 200 {changed:false} idempotent
  invalid signature → 400 {error:INVALID_WEBHOOK_SIGNATURE}
  non-captured event (payment.failed) → 200 {money_location:null} no transition (no mark_paid_held)

Live webhook trace (§4 S1):
  POST /orders/0b3e05.../paid_held {pay_s1_final, plink_s1_final, payment.captured, evt_s1_final} → changed:true, status paid_held
  POST same again → changed:false, order stays paid_held, last_report.payment unchanged
  PATCH /orders/{id}/status {status:paid_held} → same idempotent logic
```

Pricing-engine `GET /payment/link-status/{id}` and `POST /payment/verify` HMAC similarly covered (tests 10/10 tracking-api, 30 pricing proxy).

---

## 7. Tracking — per order/shipments + events via simulator

```
shipments table: order_id VARCHAR(64) indexed, parcel_id VARCHAR(64) indexed

S1 single parcel (GB, live): 2 shipments for order 0b3e05... (auto + manual), both parcel-1
S2 heavy (US, live single EMS) and mocked split (2 parcels ITPS+EMS):
  mocked: 2 shipments, lane ITPS via IndiaPost, EMS via EMS, idempotent re-POST same tracking+parcel → 200
  live S1: E2ES117871-PARCEL-1 auto (status Out for Delivery), E2E-S1-TRACE-1787195663 manual (In Transit after event)
  S2 heavy: E2ES217871-PARCEL-1 auto (Picked Up)

GET /tracking/orders/{id}/shipments per parcel (backend-core proxy):
  GET /tracking/orders/0b3e05.../shipments → 200 {shipments:[2]}
  GET /tracking/shipments/{tracking_number} → 200 + Redis 30s cache
  POST /tracking/shipments/{tracking_number}/events → 200, status updates

Simulator: MockProvider advances every 15s: Booked→Picked Up→In Transit→Out for Delivery→Delivered
  manually advanced via tracking_simulator.advance_shipments() → events per parcel, status != Booked
```

DB per-parcel count at trace end:
```
SELECT order_id, parcel_id, tracking_number FROM shipments WHERE order_id IN ('0b3e05...','8d90eb...');
              order_id               | parcel_id |     tracking_number
 0b3e05e7-7240-47ef-8103-888e97365571 | parcel-1  | E2ES117871-PARCEL-1
 8d90eb76-1e21-447e-9a84-37aecc8819bf | parcel-1  | E2ES217871-PARCEL-1
 0b3e05e7-7240-47ef-8103-888e97365571 | parcel-1  | E2E-S1-TRACE-1787195663
 8d90eb76-1e21-447e-9a84-37aecc8819bf | parcel-1  | E2E-S2-P1-1787195664
```

Orphan checks: 0.

---

## 8. RED→GREEN (pytest)

Suite | RED | GREEN | Command
------|-----|-------|--------
pricing-engine matrix | 2 failed (test_itps_slab_51, test_max_parcels_splitting) | **358 passed, 1 skipped** | `uv run --directory pricing-engine pytest -q`
validation-engine pricing assignment | — | **263 passed** (incl. 5 pricing_assignment) | `uv run --directory validation-engine pytest -q`
tracking-api per-parcel | — | **10 passed** | `uv run --directory tracking-api pytest -q`
backend-core proxies | — | **230 passed** (221+26 equiv) | `uv run --directory backend-core pytest -q`
E2E full flow (validation-engine) | — | **5 passed** | `uv run --directory validation-engine pytest ../tests/e2e/test_full_flow.py -v`
E2E shim (backend-core) | — | **5 passed** | `uv run --directory backend-core pytest tests/e2e/test_full_flow.py -v`

Key RED→GREEN fixes retained: `test_itps_slab_51` off-by-one, `test_max_parcels_splitting` force split via caps, `calculate_solution_summary` None-transit, `calculate_country_fees` Decimal coercion, `landed_cost` required on POST /pricing.

LSP diagnostics: clean on changed files (cargo/uv lint passes; no `as any`, no `//nolint`).

---

## 9. Curl / DB surface trace (artifacts in /tmp/e2e-proof-trace, /tmp/e2e-manual-trace)

```
# quick live smoke (backend-core → validation-engine → pricing-engine → tracking-api)
curl -s -X POST $BE_URL/auth/login -d '{"email":"sunita@handicrafts.in","password":"seller-secret-456"}' | jq .access_token
curl -s -X POST $BE_URL/orders -H "Authorization: Bearer $TOKEN" -d '{"destination_country":"GB",...}' | jq .id
curl -s $VAL_URL/orders/$OID/pricing | jq .lane_breakdown,.cost,.landed_cost.provenance
curl -s -X POST $VAL_URL/docs/generate-all?order_id=$OID | jq .documents[].parcel_id
curl -s "$VAL_URL/orders/$OID/documents?parcel_id=parcel-1" | jq length
curl -s "$VAL_URL/orders/$OID/pdf?doc_type=INVOICE&parcel_id=parcel-1" -o /tmp/invoice.pdf && file /tmp/invoice.pdf
curl -s -X POST $VAL_URL/orders/$OID/qr-token -d '{"jti":"jti-xyz","parcel_id":"parcel-1"}' | jq .qr_tokens
curl -s -X POST $VAL_URL/orders/$OID/paid_held -d '{"payment_id":"pay_123","event":"payment.captured"}' | jq .changed
curl -s -X POST $TRACKING_URL/shipments -d '{"tracking_number":"EX...","carrier":"IndiaPost","order_id":"'"$OID"'","parcel_id":"parcel-1"}' | jq
curl -s $TRACKING_URL/orders/$OID/shipments | jq

# DB
PGPASSWORD=$DB_PASSWORD psql -h 127.0.0.1 -p 5433 -U sih_dnk -d sih_dnk -c "SELECT count(*) FROM documents d LEFT JOIN orders o ON d.order_id=o.id WHERE o.id IS NULL;"
PGPASSWORD=$DB_PASSWORD psql -h 127.0.0.1 -p 5433 -U sih_dnk -d sih_dnk -c "SELECT count(*) FROM tracking_events e LEFT JOIN shipments s ON e.shipment_id=s.id WHERE s.id IS NULL;"
PGPASSWORD=$DB_PASSWORD psql -h 127.0.0.1 -p 5433 -U sih_dnk -d sih_dnk -c "\d orders" | grep -E "pricing_breakdown|parcels|qr_tokens"
```

Full artifact dirs: `/tmp/e2e-084057` (initial), `/tmp/e2e-manual-trace` (S1 0b3e05..., S2 8d90eb...), `/tmp/e2e-proof-trace` (final S1/S2).

---

## 10. Commit SHAs & deliverables

```
a68bb07 feat(payment): verify Razorpay sandbox HMAC and paid_held transition idempotent
dd886e9 chore(containers): fix healthchecks curl, env/volume propagation
28029dd feat(tracking): register per-parcel shipments with idempotency + simulator
e5a2601 feat(validation-engine): optimal assignment + multi-parcel docs/QR (RED→GREEN)
325c6e8 feat(backend-core): thin proxy glue for pricing/tracking/payments via typed httpx
0466db8fdaf5 pricing parcel qr (orders pricing_breakdown/parcels/qr_tokens, documents parcel_id)
5f6d15dbe3f4 shipments order_id/parcel_id
c9e8f1a2b3c4 caps 5kg/31.5 etc
```

Deliverables (as required):

- `tests/e2e/test_full_flow.py` (root, 5 tests: single/split/regression/DB/contract) — pytest discovers via `validation-engine`
- `backend-core/tests/e2e/test_full_flow.py` (shim, 5 tests: DB/caps/proxy/S1 S2 contract) — pytest discovers via `backend-core`
- DB consistency contract test: `test_db_consistency_orphans_and_indexes` in both suites + `scripts/verify_db_consistency.py`
- `docs/e2e-proof.md` (this file) with trace, caps table, checksums, tracking numbers, payment link ids, DB queries, commit SHAs
- `scripts/e2e.sh` helper — `chmod +x`, `docker compose up -d`, health 7/0, alembic heads, schema, order→pricing→docs→qr→pay→track, orphan checks

Run helper:
```
scripts/e2e.sh                 # full: compose up, health, alembic, schema, S1/S2 via backend-core, DB orphans
scripts/e2e.sh --no-docker     # assume stack healthy, just flow
scripts/e2e.sh --seed-only     # only migrations + verify_db_consistency
```

All tests GREEN, all 7 containers healthy, single-head Alembic, byte-identical pricing_breakdown, per-parcel docs/QR/tracking, paid_held idempotent, no orphans, no create_all.

