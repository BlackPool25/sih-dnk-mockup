# messaging-service — secure buyer-seller negotiations before Buy (mocked)

FastAPI service on the SIH-DNK monorepo, port **8009** host (8000 container). All auth is mocked JWT, all encryption is real AES-256-GCM per-thread via HKDF, and the DB is the offline queue (no Redis).

## Quick start

```bash
# from repo root
docker compose up -d db redis messaging-service
docker compose ps   # expect healthy

# local dev (without compose)
set -a && . ./.env && set +a
uv sync
uv run alembic upgrade head
uv run python scripts/seed_demo.py   # idempotent demo seed
uv run uvicorn app.main:app --host 0.0.0.0 --port 8009 --reload
```

Migrations live under `alembic/` with version table `messaging_alembic_version`. The seed script is idempotent: re-running never duplicates rows.

## Demo identities (mocked JWT, not auth DB)

All three users are identified by mocked JWT `sub` claims, never by a real auth table.

| Role | UUID | Email |
|------|------|-------|
| seller | `11111111-1111-1111-1111-111111111111` | `seller@demo.test` |
| buyer | `22222222-2222-2222-2222-222222222222` | `buyer@demo.test` |
| sahayak | `33333333-3333-3333-3333-333333333333` | `sahayak@demo.test` |

Generate tokens with the dev secret (`JWT_SECRET_KEY` from `.env`):

```bash
python -c "
import jwt, uuid, datetime
import os
secret = open('../.env').read().split('JWT_SECRET_KEY=')[1].split()[0]
now = datetime.datetime.now(datetime.timezone.utc)
for sub, role, email in [
  ('11111111-1111-1111-1111-111111111111','seller','seller@demo.test'),
  ('22222222-2222-2222-2222-222222222222','buyer','buyer@demo.test'),
  ('33333333-3333-3333-3333-333333333333','sahayak','sahayak@demo.test'),
]:
    tok = jwt.encode({'sub':sub,'role':role,'email':email,'iat':now,'exp':now+datetime.timedelta(hours=1),'jti':str(uuid.uuid4())}, secret, algorithm='HS256')
    print(f'{role}={tok[:40]}...')
"
```

## Health

```bash
curl -fsS http://127.0.0.1:8009/health | jq
```

```json
{"status":"ok","service":"messaging-service","mocked":true}
```

## OpenAPI

```bash
curl -fsS http://127.0.0.1:8009/openapi.json | jq .paths
curl -fsS http://127.0.0.1:8009/docs | head -20
```

Paths include `/messages/inbox`, `/messages/threads`, `/messages/threads/{thread_id}/messages`, `/messages/threads/{thread_id}/poll`, `/messages/ws/threads/{thread_id}`, `/quotes`, `/quotes/{quote_id}/reject`, `/quotes/{quote_id}/revise`, `/quotes/{quote_id}/approve`, `/quotes/{quote_id}/mock-pay`.

## Auth header

Every endpoint except `/health` requires a JWT via `Authorization: Bearer <token>` or `?token=<token>` (the latter is required for WebSocket).

```bash
TOKEN_SELLER=$(python -c "import jwt,datetime,uuid; print(jwt.encode({'sub':'11111111-1111-1111-1111-111111111111','role':'seller','email':'seller@demo.test','iat':datetime.datetime.now(datetime.timezone.utc),'exp':datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=1),'jti':str(uuid.uuid4())}, 'dev-secret-key-that-is-at-least-32-characters-long!!!', algorithm='HS256'))")
```

Set `JWT_SECRET_KEY=dev-secret-key-that-is-at-least-32-characters-long!!!` (matches `.env` default) when generating demo tokens for local curl.

## Curl blocks

Replace `<TOKEN_SELLER>` etc with real JWTs as above. `BASE=http://127.0.0.1:8009`.

### 1. GET /health

```bash
BASE=http://127.0.0.1:8009
curl -fsS $BASE/health | jq
```

### 2. POST /messages/threads — create or idempotently fetch thread for an order

```bash
BASE=http://127.0.0.1:8009
ORDER_ID=$(python -c "import uuid; print(uuid.uuid4())")
curl -fsS -X POST $BASE/messages/threads \
  -H "Authorization: Bearer $TOKEN_SELLER" \
  -H "Content-Type: application/json" \
  -d "{\"order_id\":\"$ORDER_ID\",\"seller_id\":\"11111111-1111-1111-1111-111111111111\",\"buyer_id\":\"22222222-2222-2222-2222-222222222222\"}" | jq
# idempotent: same order_id returns existing thread
echo "ORDER_ID=$ORDER_ID THREAD_ID=$(curl -fsS -X POST $BASE/messages/threads -H \"Authorization: Bearer $TOKEN_SELLER\" -H \"Content-Type: application/json\" -d \"{\\\"order_id\\\":\\\"$ORDER_ID\\\",\\\"seller_id\\\":\\\"11111111-1111-1111-1111-111111111111\\\",\\\"buyer_id\\\":\\\"22222222-2222-2222-2222-222222222222\\\"}\" | jq -r .id)"
```

Save the returned `id` as `THREAD_ID` for the blocks below.

### 3. POST /messages/threads/{id}/messages — send an encrypted message (multipart, with attachment)

```bash
BASE=http://127.0.0.1:8009
THREAD_ID=9c5e564e-21a9-4c55-880a-615e40fddff9  # from seed or create step
# text only
curl -fsS -X POST $BASE/messages/threads/$THREAD_ID/messages \
  -H "Authorization: Bearer $TOKEN_SELLER" \
  -F "body=Hello from seller, quote ready!" | jq

# with attachment (pdf or image/text allowed, 10 MB limit)
echo "sample attachment" > /tmp/sample.txt
curl -fsS -X POST $BASE/messages/threads/$THREAD_ID/messages \
  -H "Authorization: Bearer $TOKEN_SELLER" \
  -F "body=See attached spec" \
  -F "attachments=@/tmp/sample.txt;type=text/plain" | jq

# buyer reply
curl -fsS -X POST $BASE/messages/threads/$THREAD_ID/messages \
  -H "Authorization: Bearer $TOKEN_BUYER" \
  -F "body=Thanks, please revise shipping" | jq
```

Sahayak (`role=sahayak`) gets 403 on this endpoint (read-only observer).

### 4. GET /messages/inbox — paged inbox for caller (buyer/seller sees own, sahayak sees all)

```bash
BASE=http://127.0.0.1:8009
# seller inbox, first page
curl -fsS "$BASE/messages/inbox?limit=20&offset=0" \
  -H "Authorization: Bearer $TOKEN_SELLER" | jq

# buyer paged inbox, second page example
curl -fsS "$BASE/messages/inbox?limit=5&offset=5" \
  -H "Authorization: Bearer $TOKEN_BUYER" | jq

# sahayak sees all threads
curl -fsS "$BASE/messages/inbox?limit=50&offset=0" \
  -H "Authorization: Bearer $TOKEN_SAHAYAK" | jq
```

Response: `{items:[{id,order_id,seller_id,buyer_id,last_preview,...}], total, limit, offset, mocked:true}`.

### 5. GET /messages/threads/{id}/messages — paged, decrypted, chronological

```bash
BASE=http://127.0.0.1:8009
THREAD_ID=9c5e564e-21a9-4c55-880a-615e40fddff9
curl -fsS "$BASE/messages/threads/$THREAD_ID/messages?limit=20&offset=0" \
  -H "Authorization: Bearer $TOKEN_SELLER" | jq

# before filter (ISO8601, Z allowed)
curl -fsS "$BASE/messages/threads/$THREAD_ID/messages?limit=10&offset=0&before=2026-08-21T00:00:00Z" \
  -H "Authorization: Bearer $TOKEN_SELLER" | jq
```

### 6. GET /messages/threads/{id}/poll — offline queue polling via ?since=

```bash
BASE=http://127.0.0.1:8009
THREAD_ID=9c5e564e-21a9-4c55-880a-615e40fddff9
SINCE=$(date -u -d "1 hour ago" +%FT%TZ)
curl -fsS "$BASE/messages/threads/$THREAD_ID/poll?since=$SINCE&limit=20" \
  -H "Authorization: Bearer $TOKEN_SELLER" | jq

# without since returns all up to limit
curl -fsS "$BASE/messages/threads/$THREAD_ID/poll" \
  -H "Authorization: Bearer $TOKEN_SELLER" | jq
```

Works after WebSocket disconnect — DB is the offline queue, no Redis needed.

### 7. POST /quotes — seller creates quote (v1 sent)

```bash
BASE=http://127.0.0.1:8009
ORDER_ID=1a9e5632-bb48-506f-9fa4-78faac6ad41f
curl -fsS -X POST $BASE/quotes \
  -H "Authorization: Bearer $TOKEN_SELLER" \
  -H "Content-Type: application/json" \
  -H "X-Buyer-Id: 22222222-2222-2222-2222-222222222222" \
  -d "{\"order_id\":\"$ORDER_ID\",\"price_minor\":10000,\"qty\":2,\"shipping_minor\":500,\"notes\":\"initial quote\"}" | jq
# capture quote_id for next steps
QUOTE_ID=$(curl -fsS -X POST $BASE/quotes -H "Authorization: Bearer $TOKEN_SELLER" -H "Content-Type: application/json" -H "X-Buyer-Id: 22222222-2222-2222-2222-222222222222" -d "{\"order_id\":\"$ORDER_ID\",\"price_minor\":10000,\"qty\":2,\"shipping_minor\":500}" 2>/dev/null | jq -r .current.quote_id || echo "")
# if 409 already exists, fetch by order
if [ -z "$QUOTE_ID" ] || [ "$QUOTE_ID" = "null" ]; then
  QUOTE_ID=$(curl -fsS $BASE/quotes/by-order/$ORDER_ID -H "Authorization: Bearer $TOKEN_SELLER" 2>/dev/null | jq -r '.[0].quote_id' || echo "")
fi
echo "QUOTE_ID=$QUOTE_ID"
```

Requires seller role. `409` if quote already exists for that `order_id`. Buyer id is supplied via `X-Buyer-Id` header or `?buyer_id=` query.

### 8. POST /quotes/{id}/reject — buyer rejects to counter

```bash
BASE=http://127.0.0.1:8009
QUOTE_ID=b7967ee0-ccd9-487a-813f-31438c28482c
curl -fsS -X POST $BASE/quotes/$QUOTE_ID/reject \
  -H "Authorization: Bearer $TOKEN_BUYER" \
  -H "Content-Type: application/json" \
  -d '{"reason":"shipping too high, please revise"}' | jq
# state becomes counter, current_version increments
```

Requires buyer role and buyer must own the quote. Allowed only from `sent`.

### 9. POST /quotes/{id}/revise — seller revises after counter

```bash
BASE=http://127.0.0.1:8009
QUOTE_ID=b7967ee0-ccd9-487a-813f-31438c28482c
curl -fsS -X POST $BASE/quotes/$QUOTE_ID/revise \
  -H "Authorization: Bearer $TOKEN_SELLER" \
  -H "Content-Type: application/json" \
  -d '{"price_minor":9000,"qty":2,"shipping_minor":400}' | jq
# state returns to sent
```

Requires seller role and seller must own the quote. Allowed only from `counter`.

### 10. POST /quotes/{id}/approve — buyer approves

```bash
BASE=http://127.0.0.1:8009
QUOTE_ID=b7967ee0-ccd9-487a-813f-31438c28482c
curl -fsS -X POST $BASE/quotes/$QUOTE_ID/approve \
  -H "Authorization: Bearer $TOKEN_BUYER" | jq
# returns current state approved plus mocked payment_link
# {"current":{"state":"approved",...},"payment":{"payment_link":"https://pay.mock/quote/..."},...}
```

Requires buyer role, allowed from `sent` or `counter` (via revise->sent). Returns a mocked `https://pay.mock/quote/{quote_id}?amount=...` link.

### 11. POST /quotes/{id}/mock-pay — mock payment hold (paid_held)

```bash
BASE=http://127.0.0.1:8009
QUOTE_ID=b7967ee0-ccd9-487a-813f-31438c28482c
curl -fsS -X POST $BASE/quotes/$QUOTE_ID/mock-pay \
  -H "Authorization: Bearer $TOKEN_BUYER" | jq
# state becomes paid_held, terminal

# webhook alias does the same
curl -fsS -X POST $BASE/quotes/$QUOTE_ID/webhook \
  -H "Authorization: Bearer $TOKEN_BUYER" | jq
```

Any member (buyer, seller, sahayak) may invoke. Allowed only from `approved`. After `paid_held`, no further transitions (422).

### 12. WebSocket — wss example with ?token=

```bash
# Browser / wscat example (WS, mocked, no Redis)
# token passed via ?token= query param or Authorization header
TOKEN_SELLER=eyJ...  # JWT with sub=111..., role=seller
THREAD_ID=9c5e564e-21a9-4c55-880a-615e40fddff9

# wscat (npm)
npx wscat -c "ws://127.0.0.1:8009/messages/ws/threads/$THREAD_ID?token=$TOKEN_SELLER"
# After connect you receive: {"type":"connected","thread_id":"<THREAD_ID>"}
# Send:
{"type":"send","body":"hello ws"}
# Receive echo: {"type":"message","data":{"id":"...","body":"hello ws","mocked":true}}

# Python websockets example
python - << 'PY'
import asyncio, json, websockets, os
import jwt, datetime, uuid
secret = os.environ.get("JWT_SECRET_KEY","dev-secret-key-that-is-at-least-32-characters-long!!!")
tok = jwt.encode({"sub":"11111111-1111-1111-1111-111111111111","role":"seller","email":"seller@demo.test","iat":datetime.datetime.now(datetime.timezone.utc),"exp":datetime.datetime.now(datetime.timezone.utc)+datetime.timedelta(hours=1),"jti":str(uuid.uuid4())}, secret, algorithm="HS256")
url = f"ws://127.0.0.1:8009/messages/ws/threads/9c5e564e-21a9-4c55-880a-615e40fddff9?token={tok}"
async def run():
    async with websockets.connect(url) as ws:
        print(await ws.recv())
        await ws.send(json.dumps({"type":"send","body":"hello ws"}))
        print(await ws.recv())
asyncio.run(run())
PY
```

Invalid token closes with 1008. Non-member closes with 1008. Sahayak may connect but `send` returns `Sahayak observer cannot send messages`.

## Demo seed

```bash
uv run python scripts/seed_demo.py
uv run python scripts/seed_demo.py   # second run prints same ids, no duplicates

# verify DB state
PGPASSWORD=$DB_PASSWORD psql -h 127.0.0.1 -p 5433 -U sih_dnk -d sih_dnk \
  -c "SELECT id, order_id, seller_id, buyer_id FROM messaging_threads;
      SELECT thread_id, sender_role, created_at FROM messaging_messages ORDER BY created_at;
      SELECT quote_id, state, current_version FROM quote_states;
      SELECT quote_id, version, status FROM quote_versions ORDER BY version;"
```

Seeded flow is seller `v1 sent` → buyer `reject` `counter` → seller `revise` `sent` → buyer `approve` `approved` → `mock-pay` `paid_held`.

## Running tests

```bash
uv run ruff check .
uv run basedpyright
uv run pytest -q                      # ≥30 tests, 0 failures
uv run pytest --cov=app --cov-report=term-missing  # if pytest-cov installed
```

## Ports and health gates

| Binding | URL |
|---------|-----|
| Host | `127.0.0.1:8009` |
| Container | `8000` |
| Health | `GET /health` → `{"status":"ok","service":"messaging-service","mocked":true}` |
| OpenAPI | `GET /openapi.json`, `GET /docs` |

`scripts/check_health.sh` now covers 11 services (9 original plus verification-service 8008 and messaging-service 8009) plus db and redis docker health.

## Architecture notes

- Threads are one per order (`id` primary, `order_id` unique). Create is idempotent via order_id check plus ON CONFLICT fallback.
- Messages are encrypted per-thread: `HKDF-SHA256(salt=sha256(thread_id), info=dnk-msg-v1-{thread_id})` → AES-256-GCM with random 12-byte nonce per message. Preview is encrypted the same way.
- Quote lifecycle is a checked state machine: `draft→sent→counter→approved→paid_held`, with immutable `quote_versions` rows per transition.
- Sahayak is a read-only observer: may read inbox, threads, messages, poll, and WS connect, but any POST to messages or quote-mutating buyer/seller checks returns 403.
- Polling (`/poll?since=`) and WebSocket share the same DB store; disconnect does not lose messages.
