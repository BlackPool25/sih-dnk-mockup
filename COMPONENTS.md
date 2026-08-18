# SIH-DNK Mockup — Component Map

Monorepo layout, port allocations, and team ownership for the SIH-DNK mockup at
`/home/shreyas/projects/sih-dnk-mockup`. Source of truth for scaffolding —
authoritative port table from `.omo/plans/project-scaffolding.md`.

## Layout

| Directory | Component |
|---|---|
| `validation-engine/` | Export validation & document generation (FastAPI) — owns the unified `orders`/`documents`/`line_items` tables |
| `voice-pipeline/` | Voice pipeline — STT (faster-whisper) + TTS (Piper) with a Sarvam AI toggle |
| `pricing-engine/` | Pricing engine (placeholder) |
| `tracking-api/` | Tracking API (placeholder) |
| `frontend/` | Frontend (React + Vite, nginx:alpine) |
| `docker/` | Shared Docker assets (`Dockerfile.python`) |

## Port allocation table (locked)

All app services bind to `127.0.0.1` only.

| Service | Host port | Container port | Notes |
|---|---|---|---|
| sih-dnk-postgres | 5433 | 5432 | Existing — DO NOT CHANGE (5432 occupied by another local Postgres) |
| sih-dnk-redis | 6379 | 6379 | New — free on host (ss verified) |
| validation-engine | 8001 | 8000 | FastAPI dev server; orders/docs/validation unified here |
| voice-pipeline | 8002 | 8000 | STT (faster-whisper) + TTS (Piper), local/Sarvam toggle |
| pricing-engine | 8003 | 8000 | Placeholder |
| tracking-api | 8004 | 8000 | Placeholder |
| frontend | 8005 | 80 | Placeholder (nginx:alpine) |

## Team member assignments

Owners per component. Real name assigned where known from the plan; otherwise
TBD — assign before component work starts.

| Component | Owner | Notes |
|---|---|---|
| frontend | **Nabiha** | Chooses framework/toolchain (plan §OUT) |
| validation-engine | TBD — validation-engine owner | Existing codebase (post-migration); unified orders/docs |
| voice-pipeline | TBD — voice-pipeline owner | STT/TTS implemented; faster-whisper + Piper + Sarvam toggle |
| pricing-engine | TBD — pricing-engine owner | Placeholder |
| tracking-api | TBD — tracking-api owner | Placeholder |
| postgres / redis infra | TBD — platform owner | Shared compose infra |
| docker/ shared base image | TBD — platform owner | `sih-dnk-python-base` |

## Locked compose artifacts (MUST NOT change)

| Name | Value | Why |
|---|---|---|
| Compose project name | `sih-dnk-mockup` | `name:` in `docker-compose.yml` |
| Postgres volume | `sih_dnk_pgdata` | Contains the seeded DB |
| Postgres network | `dbnet` | `bin/psql` hardcodes `sih-dnk-mockup_dbnet` |
| Postgres container name | `sih-dnk-postgres` | Referenced by `verify.py` / `bin/psql` |
