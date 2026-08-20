#!/usr/bin/env bash
# scripts/e2e.sh — helper to bring up clean DB, seed, run full flow via backend-core only
# and capture trace for docs/e2e-proof.md
#
# Usage:  scripts/e2e.sh [--no-docker] [--seed-only]
#   --no-docker: skip docker compose up, assume stack already healthy
#   --seed-only: only run DB seed/migrations, no flow
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

BE_URL="${BE_URL:-http://127.0.0.1:8006}"
VAL_URL="${VAL_URL:-http://127.0.0.1:8001}"
PRICING_URL="${PRICING_URL:-http://127.0.0.1:8003}"
TRACKING_URL="${TRACKING_URL:-http://127.0.0.1:8004}"

ART_DIR="${ARTIFACT_DIR:-/tmp/e2e-$(date +%H%M%S)}"
mkdir -p "$ART_DIR"
echo "Artifact dir: $ART_DIR"

need() { command -v "$1" >/dev/null 2>&1 || { echo "missing: $1"; exit 2; }; }
need curl; need python3; need psql || echo "psql not found, will use bin/psql shim"

if [[ "${1:-}" != "--no-docker" ]]; then
  echo "== docker compose up -d =="
  docker compose up -d
  echo "Waiting for healthy..."
  scripts/check_health.sh --timeout 90 || { echo "Health failed"; docker compose ps; exit 1; }
else
  echo "Skipping docker compose up (--no-docker)"
  scripts/check_health.sh --timeout 30 || true
fi

# ensure env loaded
set -a; [ -f .env ] && . ./.env; set +a
export PGPASSWORD="${DB_PASSWORD:-changeme}"
DB_HOST="${POSTGRES_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5433}"
DB_USER="${POSTGRES_USER:-sih_dnk}"
DB_NAME="${POSTGRES_DB:-sih_dnk}"

echo "== Alembic heads =="
uv run --project validation-engine alembic current 2>&1 | tee "$ART_DIR/alembic-validation.txt" || true
uv run --project tracking-api alembic current 2>&1 | tee "$ART_DIR/alembic-tracking.txt" || true
# auth and backend-core have separate version tables
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version_num FROM alembic_version;" | tee "$ART_DIR/alembic-version.txt" || true
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version_num FROM auth_alembic_version;" | tee "$ART_DIR/auth-alembic.txt" || true
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT version_num FROM core_alembic_version;" | tee "$ART_DIR/core-alembic.txt" || true

echo "== DB schema checks =="
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\d orders" | tee "$ART_DIR/d-orders.txt" || true
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\d documents" | tee "$ART_DIR/d-documents.txt" || true
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "\d shipments" | tee "$ART_DIR/d-shipments.txt" || true
python3 scripts/verify_db_consistency.py 2>&1 | tee "$ART_DIR/verify_db.txt" || true

if [[ "${1:-}" == "--seed-only" ]]; then
  echo "Seed only, no flow"
  exit 0
fi

echo "== E2E flow via backend-core (curl + psql) =="

# Login or register seller
SELLER_EMAIL="e2e-$(date +%s)@example.com"
SELLER_PASS="TestPass123!"
echo "Register seller $SELLER_EMAIL"
REG=$(curl -s -X POST "$BE_URL/auth/register" -H 'content-type: application/json' -d "{\"email\":\"$SELLER_EMAIL\",\"password\":\"$SELLER_PASS\",\"role\":\"seller\"}" || true)
echo "$REG" | tee "$ART_DIR/register.json"
TOKEN=$(echo "$REG" | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token','') or json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")
if [ -z "$TOKEN" ]; then
  echo "Trying login..."
  LOGIN=$(curl -s -X POST "$BE_URL/auth/login" -H 'content-type: application/json' -d "{\"email\":\"$SELLER_EMAIL\",\"password\":\"$SELLER_PASS\"}")
  echo "$LOGIN" | tee "$ART_DIR/login.json"
  TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")
fi
if [ -z "$TOKEN" ]; then
  echo "Auth failed, trying demo seller"
  LOGIN=$(curl -s -X POST "$BE_URL/auth/login" -H 'content-type: application/json' -d '{"email":"seller@example.com","password":"devpassword"}')
  echo "$LOGIN" | tee "$ART_DIR/login-demo.json"
  TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")
fi
if [ -z "$TOKEN" ]; then
  LOGIN=$(curl -s -X POST "$BE_URL/auth/login" -H 'content-type: application/json' -d '{"email":"sunita@handicrafts.in","password":"seller-secret-456"}')
  echo "$LOGIN" | tee "$ART_DIR/login-sunita.json"
  TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json;print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null || echo "")
fi
echo "TOKEN len=${#TOKEN}"
[ -n "$TOKEN" ] || { echo "No token, abort"; exit 1; }
AUTH=(-H "Authorization: Bearer $TOKEN")

# Profile creation (required for order auto-fill)
echo "Create profile"
PROFILE=$(curl -s -X POST "$BE_URL/profile" "${AUTH[@]}" -H 'content-type: application/json' -d '{"firm_name":"E2E Test Exports","owner_name":"Test Owner","pan":"ABCDE1234F","bank_name":"State Bank","bank_account":"12345678901","ifsc":"SBIN0001234","bank_branch":"MG Road","iec":"0123456789","ad_code":"9876543","gstin":"29ABCDE1234F1Z5","address_line1":"42 MG Road","address_line2":"Bengaluru","city":"Bengaluru","state":"Karnataka","pincode":"560001","phone":"9876543210"}' || true)
echo "$PROFILE" | tee "$ART_DIR/profile.json"

# Single-parcel order UK 500g
echo "== S1 single parcel GB 500g =="
ORDER1=$(curl -s -X POST "$BE_URL/orders" "${AUTH[@]}" -H 'content-type: application/json' -d '{"destination_country":"GB","value_minor":150000,"currency":"INR","consignee":"John Smith, 10 Downing St, London","net_weight_g":500,"gross_weight_g":500,"article_id":"E2E-S1-'"$(date +%s)"'","line_items":[{"category_slug":"imitation-artisan-jewellery","quantity":1,"weight_g":500,"hs_code":"7117","value_minor":150000}]}')
echo "$ORDER1" | python3 -m json.tool | tee "$ART_DIR/order1.json"
OID1=$(echo "$ORDER1" | python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))" 2>/dev/null || echo "")
echo "OID1=$OID1" | tee -a "$ART_DIR/trace.txt"

if [ -n "$OID1" ]; then
  echo "Pricing trigger S1"
  PRICING1=$(curl -s -X POST "$BE_URL/orders/$OID1/pricing" "${AUTH[@]}" || true)
  echo "$PRICING1" | python3 -m json.tool | tee "$ART_DIR/pricing1.json" || echo "$PRICING1" | tee "$ART_DIR/pricing1.json"
  echo "Pricing GET S1"
  PRICING1_GET=$(curl -s "$BE_URL/orders/$OID1/pricing" "${AUTH[@]}" || true)
  echo "$PRICING1_GET" | python3 -m json.tool | tee "$ART_DIR/pricing1_get.json" || echo "$PRICING1_GET" | tee "$ART_DIR/pricing1_get.json"
  # byte-identical check
  python3 -c "
import json
a=json.load(open('$ART_DIR/pricing1.json'))
b=json.load(open('$ART_DIR/pricing1_get.json'))
print('pricing byte-identical' if json.dumps(a,sort_keys=True)==json.dumps(b,sort_keys=True) else 'MISMATCH')
" | tee -a "$ART_DIR/trace.txt" || true

  echo "Docs generate S1"
  DOCS1=$(curl -s -X POST "$BE_URL/orders/$OID1/generate-docs" "${AUTH[@]}" || true)
  echo "$DOCS1" | python3 -m json.tool | tee "$ART_DIR/docs1.json" || echo "$DOCS1" | tee "$ART_DIR/docs1.json"

  # parcel-aware docs via validation-engine direct
  echo "Docs parcel filter S1 (via validation-engine)"
  curl -s "$VAL_URL/orders/$OID1/documents?parcel_id=parcel-1" | python3 -m json.tool | tee "$ART_DIR/docs1-parcel1.json" || true
  curl -s "$VAL_URL/orders/$OID1/pdf?doc_type=INVOICE&parcel_id=parcel-1" -o "$ART_DIR/invoice1.pdf" && echo "PDF S1 size $(wc -c < "$ART_DIR/invoice1.pdf")" | tee -a "$ART_DIR/trace.txt" || true

  echo "QR token S1"
  curl -s -X POST "$VAL_URL/orders/$OID1/qr-token" -H 'content-type: application/json' -d '{"jti":"jti-s1-parcel1","parcel_id":"parcel-1"}' | tee "$ART_DIR/qr1.json" || true

  echo "Payment order S1"
  PAY_ORDER1=$(curl -s -X POST "$BE_URL/payments/order" "${AUTH[@]}" -H 'content-type: application/json' -d '{"amount_minor":150000,"currency":"INR","receipt":"e2e-s1-'"$(date +%s)"'","order_id":"'"$OID1"'"}' || true)
  echo "$PAY_ORDER1" | tee "$ART_DIR/pay-order1.json"
  echo "Payment link S1"
  PAY_LINK1=$(curl -s -X POST "$BE_URL/payments/link" "${AUTH[@]}" -H 'content-type: application/json' -d '{"amount_minor":150000,"currency":"INR","reference_id":"'"$OID1"'","description":"E2E S1 payment","order_id":"'"$OID1"'"}' || true)
  echo "$PAY_LINK1" | tee "$ART_DIR/pay-link1.json"

  # Webhook HMAC simulation (use validation-engine paid_held directly if Razorpay not configured)
  echo "Webhook paid_held S1"
  curl -s -X POST "$VAL_URL/orders/$OID1/paid_held" -H 'content-type: application/json' -d '{"payment_id":"pay_s1","payment_link_id":"plink_s1","event":"payment.captured","event_id":"evt_s1"}' | tee "$ART_DIR/webhook1.json" || true
  curl -s -X POST "$VAL_URL/orders/$OID1/paid_held" -H 'content-type: application/json' -d '{"payment_id":"pay_s1","payment_link_id":"plink_s1","event":"payment.captured","event_id":"evt_s1"}' | tee "$ART_DIR/webhook1-dup.json" || true

  echo "Tracking S1"
  curl -s -X POST "$TRACKING_URL/shipments" -H 'content-type: application/json' -d '{"tracking_number":"E2E-S1-'"$(date +%s)"'","carrier":"IndiaPost","order_id":"'"$OID1"'","parcel_id":"parcel-1"}' | tee "$ART_DIR/tracking1.json" || true
  curl -s "$TRACKING_URL/shipments?order_id=$OID1" | tee "$ART_DIR/tracking1-list.json" || true
fi

# Split order USA 2.8kg
echo "== S2 split USA 2.8kg =="
ORDER2=$(curl -s -X POST "$BE_URL/orders" "${AUTH[@]}" -H 'content-type: application/json' -d '{"destination_country":"US","value_minor":280000,"currency":"INR","consignee":"Weber Inc, 123 Main St, NY 10001","net_weight_g":2800,"gross_weight_g":2800,"article_id":"E2E-S2-'"$(date +%s)"'","line_items":[{"category_slug":"jute-products","quantity":2,"weight_g":900,"hs_code":"5310","value_minor":90000},{"category_slug":"small-woodware","quantity":1,"weight_g":900,"hs_code":"4421","value_minor":90000},{"category_slug":"embroidered-home-textiles","quantity":3,"weight_g":1000,"hs_code":"6304","value_minor":100000}]}')
echo "$ORDER2" | python3 -m json.tool | tee "$ART_DIR/order2.json"
OID2=$(echo "$ORDER2" | python3 -c "import sys,json;print(json.load(sys.stdin).get('id',''))" 2>/dev/null || echo "")
echo "OID2=$OID2" | tee -a "$ART_DIR/trace.txt"
if [ -n "$OID2" ]; then
  PRICING2=$(curl -s -X POST "$BE_URL/orders/$OID2/pricing" "${AUTH[@]}" || true)
  echo "$PRICING2" | tee "$ART_DIR/pricing2.json"
  PRICING2_GET=$(curl -s "$BE_URL/orders/$OID2/pricing" "${AUTH[@]}" || true)
  echo "$PRICING2_GET" | tee "$ART_DIR/pricing2_get.json"
  DOCS2=$(curl -s -X POST "$BE_URL/orders/$OID2/generate-docs" "${AUTH[@]}" || true)
  echo "$DOCS2" | tee "$ART_DIR/docs2.json"
  curl -s "$VAL_URL/orders/$OID2/documents?parcel_id=parcel-1" | tee "$ART_DIR/docs2-parcel1.json" || true
  curl -s "$VAL_URL/orders/$OID2/documents?parcel_id=parcel-2" | tee "$ART_DIR/docs2-parcel2.json" || true
  curl -s "$VAL_URL/orders/$OID2/pdf?doc_type=INVOICE&parcel_id=parcel-1" -o "$ART_DIR/invoice2-p1.pdf" || true
  curl -s "$VAL_URL/orders/$OID2/pdf?doc_type=INVOICE&parcel_id=parcel-2" -o "$ART_DIR/invoice2-p2.pdf" || true
  curl -s -X POST "$VAL_URL/orders/$OID2/qr-token" -H 'content-type: application/json' -d '{"jti":"jti-s2-p1","parcel_id":"parcel-1"}' | tee "$ART_DIR/qr2-p1.json" || true
  curl -s -X POST "$VAL_URL/orders/$OID2/qr-token" -H 'content-type: application/json' -d '{"jti":"jti-s2-p2","parcel_id":"parcel-2"}' | tee "$ART_DIR/qr2-p2.json" || true
  curl -s -X POST "$VAL_URL/orders/$OID2/paid_held" -H 'content-type: application/json' -d '{"payment_id":"pay_s2","payment_link_id":"plink_s2","event":"payment.captured","event_id":"evt_s2"}' | tee "$ART_DIR/webhook2.json" || true
  curl -s -X POST "$TRACKING_URL/shipments" -H 'content-type: application/json' -d '{"tracking_number":"E2E-S2-P1-'"$(date +%s)"'","carrier":"IndiaPost","order_id":"'"$OID2"'","parcel_id":"parcel-1"}' | tee "$ART_DIR/tracking2-p1.json" || true
  curl -s -X POST "$TRACKING_URL/shipments" -H 'content-type: application/json' -d '{"tracking_number":"E2E-S2-P2-'"$(date +%s)"'","carrier":"EMS","order_id":"'"$OID2"'","parcel_id":"parcel-2"}' | tee "$ART_DIR/tracking2-p2.json" || true
  curl -s "$TRACKING_URL/orders/$OID2/shipments" | tee "$ART_DIR/tracking2-list.json" || true
fi

echo "== DB orphan checks =="
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT count(*) AS orphan_docs FROM documents d LEFT JOIN orders o ON d.order_id=o.id WHERE d.order_id IS NOT NULL AND o.id IS NULL;" | tee "$ART_DIR/db-orphan-docs.txt" || true
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT count(*) AS orphan_events FROM tracking_events e LEFT JOIN shipments s ON e.shipment_id=s.id WHERE s.id IS NULL;" | tee "$ART_DIR/db-orphan-events.txt" || true
psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT count(*) FROM shipments WHERE order_id IS NOT NULL AND parcel_id IS NOT NULL;" | tee "$ART_DIR/db-parcel-shipments.txt" || true

echo "== Done, artifacts in $ART_DIR =="
ls -lh "$ART_DIR"
echo "Trace:"
cat "$ART_DIR/trace.txt" 2>/dev/null || true
