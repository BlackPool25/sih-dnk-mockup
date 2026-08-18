# frontend — SIH-DNK Voice-First Export Assistant (React + Vite)

Hindi/English voice-first export intake for Indian artisans. Large mic button
(MediaRecorder) → `/api/voice/transcribe` → chat flow against backend-core
`/api/llm/chat` → live shipment-progress panel, customs/duty guidance, order
creation and official-document PDF download.

## Stack

- React 19 + Vite 8, `lucide-react` icons, oxlint for linting
- `src/services/api.js` — auth, chat, orders, transcribe, TTS against backend-core

## Backend contract (frozen)

All calls go through one backend (FastAPI `backend-core`):

- `POST /auth/login` → `{access_token, user}`
- `POST /api/llm/chat` (Bearer) → ChatResponse with `history`, `filled_fields`,
  `pending_fields`, `db_info`, `document_ready`, `reply_text`, `tts_hint`
- `POST /api/voice/transcribe` (Bearer, multipart `file` + `language_hint`)
- `POST /api/voice/tts` (Bearer, JSON `{text, language}`) → audio/wav
- `GET/POST /orders`, `GET /orders/{id}/pdf`

Languages: `en` and `hi` only (defaults to Hindi). Hindi gets assistant voice
replies (TTS) with a mute toggle; English stays text-only for the demo.

## Running the full demo

The frontend is only the last mile — the demo needs the three backend services
running first.  All steps below were verified on this machine.

### 0. Voice models (one-time)

```sh
cd voice-pipeline
bash scripts/download_voices.sh                          # Piper voices → models/
uv run python -c "from faster_whisper import WhisperModel; WhisperModel('collabora/faster-whisper-medium-hindi', device='cpu', compute_type='int8', cpu_threads=4)"
```

### 1. Backend services (three terminals, or tmux sessions `ve`/`be`/`vp`)

validation-engine (port 8001):

```sh
cd validation-engine
UV_PROJECT_ENVIRONMENT=/tmp/opencode/ve-venv uv run uvicorn app.api:app --host 127.0.0.1 --port 8001
```

voice-pipeline (port 8002):

```sh
cd voice-pipeline
uv run uvicorn main:app --host 127.0.0.1 --port 8002
```

backend-core (port 8006) — uses a healthy venv at `/tmp/opencode/be-venv`; the
repo's `.venv` is root-owned from a docker build and must NOT be used:

```sh
cd backend-core
set -a && . ../validation-engine/.env && set +a
export VALIDATION_ENGINE_URL=http://127.0.0.1:8001
export VOICE_PIPELINE_URL=http://127.0.0.1:8002   # REQUIRED — docker default won't resolve
export REDIS_URL=redis://127.0.0.1:6379/0
export PYTHONPATH=/home/shreyas/projects/sih-dnk-mockup
exec /tmp/opencode/be-venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8006
```

Note: `VOICE_PIPELINE_URL` is not in `.env` — if it is left at the docker
default (`http://voice-pipeline:8000`) the `/api/voice/*` proxy will 503.

### 2. Frontend (port 5173)

```sh
cd frontend
npm install
npm run dev        # http://localhost:5173 — proxies /api /auth /orders to :8006
npm run lint       # oxlint
npm run build      # vite build → dist/
```

### 3. Demo credentials

```
email:    sunita@handicrafts.in
password: seller-secret-456
```

### 4. The 8-step demo script

With the stack running, the full acceptance journey can be re-run at any time:

```sh
scripts/demo_e2e.sh     # from the repo root — prints PASS/FAIL per step
```

It performs: 1) login → 2) real WAV STT → 3) Hindi chat turn → 4) drive fields
until `document_ready` → 5) create order → 6) generate 4 docs (CI/PL/CN/PBE) →
7) download PDF → 8) TTS reply WAV.  Artifacts land in `/tmp/demo_e2e_<ts>/`.

## Run (docker)

The `Dockerfile` builds with node:20 then serves `dist/` via nginx. `nginx.conf`
proxies `/api/`, `/auth/`, `/orders`, `/docs` to the `backend-core` compose
service (`http://backend-core:8000`).

```sh
docker build -t sih-dnk-frontend .
# or from the repo root:
docker compose up -d   # frontend at http://localhost:8005
```

## Files

- `src/App.jsx` — single-screen app (login, chat, voice, progress, orders)
- `src/services/api.js` — backend client (Bearer-authed)
- `src/index.css` — design tokens & component styles
- `nginx.conf` — prod nginx proxy config
