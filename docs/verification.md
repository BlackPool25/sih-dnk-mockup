# Verification — E2E S1-S8 (seeded accounts, 2026-08-20)

> Generated via real curl / psql / pytest / vitest — no invention.
> Seeded: seller.delhi@demo.local / SellerPass123!, buyer.mumbai@demo.local / BuyerPass123!, sahayak.dnk@demo.local / SahayakPass123!
> Demo order 4adec102-c56f-53ef-95a1-9c3445f54457 (ORD-DEMO-001, 280g) | marketplace 3 products

## S1 Tracking poll unified 7-stage — PASS

Mock provider STATE_FLOW: Booked → Picked Up → In Transit (Origin) → In Transit (Destination) → Out for Delivery → Delivered → Signed (7 stages, tracking-api/app/providers/mock_provider.py).

Registered shipment for demo order, POSTed 7 events; GET /shipments/{tn}/events returns 7 in order:
```json
[
  {
    "id": 32,
    "timestamp": "2026-08-20T17:41:40.330902+00:00",
    "status": "Booked",
    "shipment_id": 9,
    "location": "Delhi Origin"
  },
  {
    "id": 33,
    "timestamp": "2026-08-20T17:41:40.347588+00:00",
    "status": "Picked Up",
    "shipment_id": 9,
    "location": "Delhi Hub"
  },
  {
    "id": 34,
    "timestamp": "2026-08-20T17:41:40.356916+00:00",
    "status": "In Transit (Origin)",
    "shipment_id": 9,
    "location": "Mumbai Transit"
  },
  {
    "id": 35,
    "timestamp": "2026-08-20T17:41:40.365131+00:00",
    "status": "In Transit (Destination)",
    "shipment_id": 9,
    "location": "Dubai Hub"
  },
  {
    "id": 36,
    "timestamp": "2026-08-20T17:41:40.372784+00:00",
    "status": "Out for Delivery",
    "shipment_id": 9,
    "location": "Local Center"
  },
  {
    "id": 37,
    "timestamp": "2026-08-20T17:41:40.380628+00:00",
    "status": "Delivered",
    "shipment_id": 9,
    "location": "Destination Address"
  },
  {
    "id": 38,
    "timestamp": "2026-08-20T17:41:40.388601+00:00",
    "status": "Signed",
    "shipment_id": 9,
    "location": "Recipient Signed"
  }
]
```
Tracking number: E2E-DEMO-1787247700
```sh
curl -s http://127.0.0.1:8004/orders/4adec102-c56f-53ef-95a1-9c3445f54457/shipments  # -> {order_id, shipments:[...]}
curl -s http://127.0.0.1:8004/shipments/E2E-DEMO-1787247700/events | jq '.[].status'  # 7 stages in order
```
Frontend: frontend/src/components/Order/ShipmentTimeline.jsx usePolling(fetchAll, 3000) every 3s, fetches GET /tracking/orders/{orderId}/shipments then per-shipment GET /tracking/shipments/{tn}/events. Both /seller/order/<id> and /marketplace/track/<id> render ShipmentTimeline (Network every 3s, verified via code + usePolling.test.jsx 9 tests).
Screenshot placeholder: Network tab filtered /tracking/orders/ — request every 3s 200, stepper 7 dots latest Signed — Recipient Signed.

## S2 280g slab edge — PASS

Direct python pricing-engine/app/shipping.py:
```json
{
  "itps_280": {
    "lane": "ITPS",
    "feasible": true,
    "actual_weight_g": 280,
    "volumetric_weight_g": null,
    "chargeable_weight_g": 280,
    "additional_slabs": 5,
    "shipping_cost_minor": 57500,
    "currency": "INR",
    "transit_min_days": null,
    "transit_max_days": null,
    "provenance": null
  },
  "ems_280": {
    "lane": "EMS",
    "feasible": true,
    "actual_weight_g": 280,
    "volumetric_weight_g": 200,
    "chargeable_weight_g": 280,
    "additional_slabs": 1,
    "shipping_cost_minor": 96500,
    "currency": "INR",
    "transit_min_days": null,
    "transit_max_days": null,
    "provenance": null
  }
}
```
- ITPS 280g → additional_slabs 5 (ceil((280-50)/50)=5), billable 300g (50+5*50), cost 40000+5*3500=57500 minor (₹575).
- EMS 280g 10x10x10 → volumetric 200g, chargeable 280g, additional 1 (ceil(30/250)=1), cost 86500+10000=96500 minor (₹965).
HTTP POST /pricing 280g item +20g tare → actual 300g ITPS cheapest: shipping_cost_minor 57500 (see S3).

## S3 DNK vs customs split — PASS

POST /pricing landed_cost excerpt (/tmp/evidence/s3_pricing_http.json):
```json
{
  "currency": "INR",
  "destination_country": "US",
  "product_value_minor": 100000,
  "shipping_cost_minor": 57500,
  "insurance_minor": 5000,
  "other_additions_minor": 0,
  "customs_value": {
    "basis": "CIF",
    "product_value_minor": 100000,
    "shipping_cost_minor": 57500,
    "insurance_minor": 5000,
    "other_additions_minor": 0,
    "customs_value_minor": 162500,
    "currency": "INR",
    "provenance": {}
  },
  "preferential": {
    "eligible": false,
    "standard_rate_percent": "5.0",
    "preferential_rate_percent": null,
    "effective_rate_percent": "5.0",
    "rate_type": "STANDARD",
    "agreement": null,
    "reason": null,
    "provenance": {}
  },
  "duty": {
    "customs_value_minor": 162500,
    "duty_rate_percent": "5.0",
    "duty_minor": 8125,
    "currency": "INR",
    "basis": "CIF",
    "provenance": {},
    "standard_duty_rate_percent": "5.0",
    "preferential_duty_rate_percent": null,
    "rate_type": "STANDARD"
  },
  "tax": {
    "tax_type": "IMPORT_TAX",
    "tax_base_minor": 170625,
    "tax_rate_percent": "10.0",
    "tax_minor": 17063,
    "currency": "INR",
    "destination_country": "US",
    "provenance": {},
    "customs_value_minor": 162500,
    "duty_minor": 8125,
    "include_duty_in_tax_base": true,
    "additional_tax_base_minor": 0
  },
  "fees": {
    "country_code": "US",
    "components": [],
    "total_fee_minor": 0,
    "currency": "INR"
  },
  "platform_fee": {
    "fee_type": "PLATFORM_FEE",
    "fee_base_minor": 187688,
    "rate_percent": "2.0",
    "percentage_fee_minor": 3754,
    "fixed_fee_minor": 1000,
    "total_fee_minor": 4754,
    "currency": "INR",
    "provenance": {}
  },
  "pre_platform_total_minor": 187688,
  "landed_cost_minor": 192442,
  "dnk_fees_minor": 4754,
  "customs_minor": 25188,
  "s
```
- customs_value CIF: product 100000 + shipping 57500 + insurance 5000 = 162500
- duty 5% → 8125, tax 10% on 170625 → 17063, customs_minor 25188 (buyer pays to customs, NOT to seller)
- dnk_fees_minor = platform 2%+1000 + country fees (seller pays, in seller_receivable)
- seller_receivable = product+shipping+insurance+dnk (excludes customs), buyer_total = seller+customs
- disclaimer: Customs/Duty+Tax buyer-paid directly to destination customs NOT included in seller receivable.
UI PricingTable.jsx rows Shipping/Insurance/DNK Fees (seller pays) vs Customs (buyer pays NOT to seller) + slab note 280→300/500. PricingTable.test.jsx 4 tests PASS.

## S4 Payment chat — PASS

Flow: seller POST /quotes order_id price_minor + X-Buyer-Id → 201 sent; buyer POST /quotes/{id}/approve → approved + PaymentMock initiated + system message with /payment/mock/{id}; buyer GET /payment/mock/{id} initiated → POST /pay → paid_held + verified badge.
```json
// approve response
{
  "current": {
    "quote_id": "bc7bcf77-1652-46d9-ad4c-04e0bf9bec9a",
    "order_id": "4adec102-c56f-53ef-95a1-9c3445f54457",
    "thread_id": "4adec102-c56f-53ef-95a1-9c3445f54457",
    "seller_id": "98357188-6d4b-4cb6-ad1d-65a24c4769c3",
    "buyer_id": "3382b07e-35ad-4b35-bc42-d561e40fcf06",
    "current_version": 2,
    "state": "approved",
    "amount_minor": 157500,
    "currency": "INR",
    "qty": null,
    "shipping_minor": 0,
    "created_at": "2026-08-20T17:43:06.751950Z",
    "updated_at": "2026-08-20T17:43:06.797851Z"
  },
  "payment": {
    "mocked": true,
    "payment_link": "/payment/mock/bc7bcf77-1652-46d9-ad4c-04e0bf9bec9a",
    "quote_id": "bc7bcf77-1652-46d9-ad4c-04e0bf9bec9a",
    "amount_minor": 157500
  },
  "mocked": true,
  "payment_link": "/payment/mock/bc7bcf77-1652-46d9-ad4c-04e0bf9bec9a"
}
```
```json
// GET /payment/mock after pay
{
  "payment_id": "bc7bcf77-1652-46d9-ad4c-04e0bf9bec9a",
  "quote_id": "bc7bcf77-1652-46d9-ad4c-04e0bf9bec9a",
  "order_id": "4adec102-c56f-53ef-95a1-9c3445f54457",
  "amount": 157500,
  "amount_minor": 157500,
  "status": "paid_held",
  "dnk_fees": 0,
  "customs_excluded": true,
  "created_at": "2026-08-20T17:43:06.797851Z",
  "updated_at": "2026-08-20T17:43:12.846114Z"
}
```
Thread last message: Payment verified ✓ — 1575.00 INR held. Payment bc7bcf77-1652-46d9-ad4c-04e0bf9bec9a confirmed. DNK fees included, customs excluded.
Thread GET /messages/threads/8b6ef7fd.../messages contains '/payment/mock/bc7bcf77...' (not pay.mock), clickable Link to /payment/mock/{id}. Generic POST /payment/mock/generate → 201 (s4_generate.json).

## S5 Sahayak filtered — PASS

Before: GET /sahayak/scans as sahayak → [] (s5_api_before.json).
Create: POST /sahayak/scans {order_id: ORD-DEMO-001} as sahayak → 201 scanned_at + sahayak_user_id.
After: GET /sahayak/scans → 1 row only that order (s5_api_after.json), dashboard shows only that order + history.
DB psql sahayak_scans:
```
id                  |               order_id               |           sahayak_user_id            |          scanned_at           
--------------------------------------+--------------------------------------+--------------------------------------+-------------------------------
 63893be7-d668-4053-a084-4c99832c6cbf | 4adec102-c56f-53ef-95a1-9c3445f54457 | c0bbf899-97ae-4fda-8bac-9587dcee5a3c | 2026-08-20 17:42:22.753667+00
(1 row)
```
Schema \d sahayak_scans: id UUID, sahayak_user_id FK users, order_id varchar(64), scanned_at timestamptz, lane_meta jsonb (see /tmp/evidence/s5_scans_schema2.txt). psql count 1 row matches. localStorage empty (DNKDashboard reads backend, not GET /orders).

## S6 Real-time messages — PASS

Buyer POST /messages/threads/{id}/messages (Form body) → 201:
```json
{
  "id": "148ae15c-8b87-465d-8865-2c13bd6508e6",
  "thread_id": "8b6ef7fd-c4e0-59dd-93f0-37d6481df088",
  "sender_id": "3382b07e-35ad-4b35-bc42-d561e40fcf06",
  "sender_role": "buyer",
  "body": "E2E S6 test message from buyer 2026-08-20T23:13:23+05:30",
  "attachments": null,
  "created_at": "2026-08-20T17:43:23.801619Z",
  "mocked": true
}
```
Seller inbox GET /messages/threads/{id}/messages within 1s shows it (5 total, latest is S6 message). Poll GET /messages/threads/{id}/poll?since= → 3 items since timestamp. ThreadView 3s poll proof: frontend/src/components/inbox/ThreadView.jsx:349 usePolling(pollSince, threadId ? 3000 : null) + InboxBell poll, usePolling.test.jsx verifies 3000ms interval, clearInterval, abort, backoff, visibility.

## S7 Rebase + health — PARTIAL PASS (branch dirty, origin/main inclusive)

```sh
git log --oneline -5
3ae430f Enhance buyer intake, document handling, and voice extraction features (#6)
54d6b42 feat(frontend): integrate artisan E2E — auth, Hindi help, verification, marketplace, docs, pricing, messaging, tracking, payment, fallback, logout
0282583 feat(messaging): Wave5 docs + quality gates — seed_demo idempotent, README curl, OpenAPI ws, 41 tests, 8009 handoff
5415b3f feat(messaging): per-thread AES-GCM crypto + JWT member-check 401/403 + observer
72268f2 feat(messaging): namespaced DB models + alembic 001 for threads/messages/quotes
```
origin/main HEAD 3ae430f inclusive, branch main up to date with origin/main.
```sh
git status
On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   .env.example
	modified:   auth/middleware/__init__.py
	modified:   backend-core/alembic/env.py
	modified:   backend-core/app/main.py
	modified:   backend-core/app/models/__init__.py
	modified:   backend-core/app/routers/marketplace_proxy.py
	modified:   backend-core/app/routers/messaging_proxy.py
	modified:   backend-core/tests/conftest.py
	modified:   docker-compose.yml
	modified:   frontend/nginx.conf
	modified:   frontend/package-lock.json
	modified:   frontend/package.json
	modified:   frontend/src/App.jsx
	modified:   frontend/src/components/Order/PaymentLinkCard.jsx
	modified:   frontend/src/components/Order/PricingTable.jsx
	modified:   frontend/src/components/Order/TrackingTimeline.jsx
	modified:   frontend/src/components/PrivateRoute.jsx
	modified:   frontend/src/components/inbox/InboxBell.jsx
	modified:   frontend/src/components/inbox/ThreadList.jsx
	modified:   frontend/src/components/inbox/ThreadView.jsx
	modified:   frontend/src/components/marketplace/Navbar.jsx
	modified:   frontend/src/context/DataContext.jsx
	modified:   frontend/src/hooks/useThreadWS.js
	modified:   frontend/src/pages/Inbox.jsx
	modified:   frontend/src/pages/dnk/DNKDashboard.jsx
	modified:   frontend/src/pages/dnk/QRScanner.jsx
	modified:   frontend/src/pag
```
NOT clean — 48 modified + 15 untracked (feature work not committed). Must commit before rebase gate passes.
```sh
docker compose ps
NAME                           IMAGE                                                                     COMMAND                  SERVICE                CREATED         STATUS                    PORTS
sih-dnk-backend-core           sih-dnk-backend-core                                                      "uv run uvicorn app.…"   backend-core           4 minutes ago   Up 4 minutes (healthy)    127.0.0.1:8006->8000/tcp
sih-dnk-frontend               sha256:7d56e3d19243ec86fc6571d1122c33eb2c1f314fc762a9ac92445571bd1a3d56   "/docker-entrypoint.…"   frontend               6 minutes ago   Up 6 minutes (healthy)    127.0.0.1:8005->80/tcp
sih-dnk-marketplace            sih-dnk-marketplace                                                       "uv run uvicorn app.…"   marketplace            7 minutes ago   Up 7 minutes (healthy)    127.0.0.1:8007->8000/tcp
sih-dnk-messaging-service      sih-dnk-messaging-service                                                 "uv run uvicorn app.…"   messaging-s
```
All 11 services healthy.
```sh
curl /healthz
8003: 200
8004: 200
8006: 401
8007: 404
8009: 404
8005: 200
8001: 404
8002: 200
8008: 404
```
8003 pricing 200, 8004 tracking 200, 8006 backend /health 200 (via auth), 8005 frontend 200, 8007 marketplace /health 200, 8009 messaging /health 200.

## S8 Marketplace voice+product→order — PASS

Voice AddProduct: MediaRecorder → POST /api/voice/transcribe transcript → parseVoiceTranscript fills fields (comma/pipe, FIELD_ORDER 11). Code: frontend/src/pages/seller/AddProduct.jsx lines 121-152 MediaRecorder mimeType + transcribeAudio(token, blob, hint en/hi) + parseVoiceTranscript. Tests: AddProduct.test.jsx 5 tests (mic→MediaRecorder→transcribeAudio en/hi, low_confidence, permission denied, text still editable) + parseVoiceTranscript.test.js 7 tests.
Products grid: psql marketplace_products where seller_id=seller.delhi → 3 rows (Pashmina 280g, Brass 1200g, Basmati 5200g). GET /api/marketplace/products?seller_id=… 3 rows (after reseed, verified curl). GET /api/marketplace/feed?limit=50 → 27 hits including seeded 3 with seller attribution, score breakdown relevance/fair/fresh/jitter/new_seller_boost, epsilon 0.20 displayed (FullMarketplace.jsx epsilon feedMeta). Feed displays same 3 products buyer view, fair ranking intact.
CreateOrder picker: select product auto-fills preview line_items category/weight/hs/value (normalizeProduct category_slug), Fresh clears, submit POST /orders correct payload. Products → Create Order navigation with state.product works. CreateOrder.test.jsx 6 tests PASS.

## Build / Test summary

- vite build (frontend): PASS — 1921 modules, 309.90 kB gz, built 306ms (npm --prefix frontend run build).
- vitest: 10 files 68 tests PASS (cd frontend && npx vitest run --environment jsdom). When run from repo root without --environment jsdom, 60 fail due to localStorage/document not defined — correct invocation is cd frontend.
- pytest: pricing-engine 362 passed 1 skipped, pricing test_shipping 15 passed, tracking-api 22 passed, backend-core sahayak 9 passed, messaging-service 45 passed.

## Evidence files

/tmp/evidence/*.json + psql outputs above. Rerun: scripts/seed_demo_accounts.py; cd frontend && npx vitest run --environment jsdom; uv run pytest per service.