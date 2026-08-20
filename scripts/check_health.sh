#!/usr/bin/env bash
# check_health.sh — verify all 10 SIH-DNK compose services are healthy (9/9+frontend =10, 9 API + db/redis).
# Usage:  scripts/check_health.sh [--timeout 60]
#   Probes host ports with 60s retry loop; exits 0 if all healthy, non-zero if any fail.
set -euo pipefail

TIMEOUT="${1:-60}"
if [[ "${1:-}" == "--timeout" ]]; then
  TIMEOUT="${2:-60}"
fi

declare -A ENDPOINTS=(
  ["validation-engine"]="http://127.0.0.1:8001/health"
  ["pricing-engine"]="http://127.0.0.1:8003/healthz"
  ["tracking-api"]="http://127.0.0.1:8004/healthz"
  ["backend-core"]="http://127.0.0.1:8006/health"
  ["voice-pipeline"]="http://127.0.0.1:8002/healthz"
  ["marketplace"]="http://127.0.0.1:8007/health"
  ["verification-service"]="http://127.0.0.1:8008/health"
  ["frontend"]="http://127.0.0.1:8005/"
)

PASS=0
FAIL=0

echo "Waiting up to ${TIMEOUT}s for services to become healthy..."

elapsed=0
interval=3
all_ok=false
while (( elapsed < TIMEOUT )); do
  ok_count=0
  total=0
  for svc in "${!ENDPOINTS[@]}"; do
    total=$((total+1))
    url="${ENDPOINTS[$svc]}"
    if curl -fsS --max-time 3 "$url" >/dev/null 2>&1; then
      ok_count=$((ok_count+1))
    fi
  done
  if (( ok_count == total )); then
    all_ok=true
    break
  fi
  sleep "$interval"
  elapsed=$((elapsed+interval))
done

echo ""
echo "Health check results:"
for svc in $(echo "${!ENDPOINTS[@]}" | tr ' ' '\n' | sort); do
  url="${ENDPOINTS[$svc]}"
  if curl -fsS --max-time 3 "$url" >/dev/null 2>&1; then
    echo "  OK   $svc -> $url"
    PASS=$((PASS+1))
  else
    echo "  FAIL $svc -> $url"
    FAIL=$((FAIL+1))
  fi
done

if command -v docker >/dev/null 2>&1; then
  for svc in sih-dnk-postgres sih-dnk-redis; do
    if docker inspect --format='{{.State.Health.Status}}' "$svc" >/dev/null 2>&1; then
      status=$(docker inspect --format='{{.State.Health.Status}}' "$svc" 2>/dev/null || echo "unknown")
      if [[ "$status" == "healthy" ]]; then
        echo "  OK   $svc (docker health: $status)"
        PASS=$((PASS+1))
      else
        echo "  FAIL $svc (docker health: $status)"
        FAIL=$((FAIL+1))
      fi
    fi
  done
fi

echo ""
echo "Passed: $PASS  Failed: $FAIL"
if (( FAIL > 0 )); then
  echo "Some services are unhealthy."
  exit 1
fi
echo "All services healthy."
exit 0
