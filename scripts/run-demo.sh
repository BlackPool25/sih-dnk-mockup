#!/usr/bin/env bash
# Start all demo services for testing (validation-engine, voice-pipeline, backend-core)
# Run: bash scripts/run-demo.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "→ ensuring DB + Redis are up"
docker compose up -d db redis 2>&1 | tail -1

echo "→ starting validation-engine on :8001"
cd "$ROOT/validation-engine"
setsid nohup /tmp/opencode/ve-venv/bin/python -m uvicorn app.api:app --host 127.0.0.1 --port 8001 > /tmp/opencode/ve-8001.log 2>&1 < /dev/null &
disown

echo "→ starting voice-pipeline on :8002 (Sarvam cloud STT + TTS)"
cd "$ROOT/voice-pipeline"
set -a && . ../validation-engine/.env && set +a
setsid nohup uv run --no-sync uvicorn main:app --host 127.0.0.1 --port 8002 > /tmp/opencode/vp-8002.log 2>&1 < /dev/null &
disown

echo "→ starting backend-core on :8006"
cd "$ROOT/backend-core"
set -a && . ../validation-engine/.env && set +a
export VALIDATION_ENGINE_URL=http://127.0.0.1:8001
export VOICE_PIPELINE_URL=http://127.0.0.1:8002
export REDIS_URL=redis://127.0.0.1:6379/0
export PYTHONPATH="$ROOT"
setsid nohup /tmp/opencode/be-venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8006 > /tmp/opencode/be-8006.log 2>&1 < /dev/null &
disown

echo "→ starting tracking-api on :8004 (mock 17TRACK simulator)"
cd "$ROOT/tracking-api"
export TRACKING_PROVIDER=mock
setsid nohup /tmp/opencode/ta-venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port 8004 > /tmp/opencode/ta-8004.log 2>&1 < /dev/null &
disown

sleep 6
echo ""
echo "=== health check ==="
curl -s -o /dev/null -w "validation-engine :8001  → HTTP %{http_code}\n" -m 3 http://127.0.0.1:8001/ || true
curl -s -o /dev/null -w "voice-pipeline    :8002  → HTTP %{http_code}\n" -m 3 http://127.0.0.1:8002/healthz || true
curl -s -o /dev/null -w "tracking-api      :8004  → HTTP %{http_code}\n" -m 3 http://127.0.0.1:8004/healthz || true
curl -s -o /dev/null -w "backend-core      :8006  → HTTP %{http_code}\n" -m 3 http://127.0.0.1:8006/health || true
echo ""
echo "All services started. Logs: /tmp/opencode/{ve-8001,vp-8002,ta-8004,be-8006}.log"
echo "Stop with: pkill -f 'uvicorn app.api:app'; pkill -f 'uvicorn main:app'; pkill -f 'uvicorn app.main:app'"
