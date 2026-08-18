# tracking-api

Shipment tracking API for the SIH DNK mockup monorepo. Built on the monorepo's
Python pattern (FastAPI + uvicorn + uv), mirroring the other services so the
whole stack shares one base image (`sih-dnk-python-base`) and one dependency
manager.

## Endpoints

| Method | Path | Description |
| ------ | ---- | ----------- |
| `GET`  | `/healthz` | Liveness probe → `{"status": "ok"}` |
| `POST` | `/shipments` | Register a shipment `{tracking_number, carrier}` (also registers with the active tracking provider) |
| `GET`  | `/shipments/{tracking_number}` | Shipment details (Redis-cached for 30s) |
| `POST` | `/shipments/{tracking_number}/events` | Manually append a tracking event |
| `GET`  | `/shipments/{tracking_number}/events` | Event history for a shipment |

## Tracking providers

Provider selection via `TRACKING_PROVIDER` env var (default `mock`):

- **`mock`** — `MockProvider`: a local simulator auto-advances every registered
  shipment through `Booked → Picked Up → In Transit → Out for Delivery →
  Delivered` on a 15s scheduler, picking locations from a fixed hub list. No
  external calls; used for local dev / demo / tests.
- **`live`** — `RealProvider`: talks to the real 17TRACK API v2.4
  (`register` + `gettrackinfo`). Requires `TRACK17_API_KEY`. Carrier codes
  currently mapped: `IndiaPost`.

## Ports

| Binding | Port |
| ------- | ---- |
| Host (docker-compose mapping) | **8004** |
| Container (uvicorn) | **8000** |

## Upstream dependencies

Consumed via `docker-compose.yml` (see repo root):

- **PostgreSQL** — `DATABASE_URL` (e.g. `postgresql+psycopg://...`)
- **Redis** — `REDIS_URL` (e.g. `redis://redis:6379/0`)

## Run

**Container (primary):**

```sh
docker compose up tracking-api
```

**Local dev:**

```sh
uv run uvicorn main:app --host 0.0.0.0 --port 8000
```

Health check: `GET /healthz` → `{"status": "ok"}`.
