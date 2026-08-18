#!/usr/bin/env bash
# Optional: install the CTranslate2 ROCm wheel so faster-whisper runs on the
# AMD RX 7900 GRE (gfx1100).  Run from the voice-pipeline directory AFTER
# `uv sync`.  The wheel is a GitHub release asset (not on PyPI); CT2's HIP
# backend registers as device="cuda", so faster-whisper works unchanged.
#
# The wheels are built for CPython 3.12, so the venv MUST be pinned to 3.12
# (`uv python pin 3.12 && uv sync`) — on any other version the cp312 wheel
# fails to import and get_cuda_device_count() returns 0.
#
# Skip this on machines without ROCm — /transcribe falls back to CPU int8.
set -euo pipefail

CT2_VERSION="${CT2_VERSION:-4.8.1}"
CT2_URL="https://github.com/OpenNMT/CTranslate2/releases/download/v${CT2_VERSION}/rocm-python-wheels-Linux.zip"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

PY_VERSION="$(uv run python -c 'import sys; print(f"{sys.version_info.major}{sys.version_info.minor}")')"
if [[ "$PY_VERSION" != "312" ]]; then
    echo "error: ROCm wheels are cp312-only but the venv is Python ${PY_VERSION}; run: uv python pin 3.12 && uv sync" >&2
    exit 1
fi

echo "fetching CTranslate2 ${CT2_VERSION} ROCm wheels ..."
curl -L --fail --retry 3 -o "$TMP_DIR/rocm-wheels.zip" "$CT2_URL"
unzip -q "$TMP_DIR/rocm-wheels.zip" -d "$TMP_DIR"

WHEEL="$(find "$TMP_DIR" -name 'ctranslate2-*-cp312-*-manylinux*x86_64.whl' | sort -V | tail -1)"
if [[ -z "$WHEEL" ]]; then
    echo "error: no cp312 x86_64 ROCm wheel found in $CT2_URL" >&2
    exit 1
fi

echo "installing $WHEEL ..."
PYEXE="$(uv run --no-sync python -c 'import sys; print(sys.executable)')"
# uv pip install alone treats a same-version installed distribution as already
# satisfied and keeps the PyPI CPU wheel's files, and `uv run` auto-resync then
# restores them. Uninstall first, install with --reinstall, and always use
# --no-sync after this so the manual venv is not re-synced back to PyPI.
uv pip uninstall ctranslate2 --python "$PYEXE" >/dev/null
uv pip install --reinstall --python "$PYEXE" "$WHEEL"

uv run --no-sync python - <<'PY'
import ctranslate2
count = ctranslate2.get_cuda_device_count()
print("ctranslate2", ctranslate2.__version__)
print("cuda devices:", count)
# Some hosts (e.g. Raphael/AM5) also expose the integrated GPU to HIP, so the
# visible count can be 2 (iGPU + RX 7900 GRE). What matters is that the GPU is
# reachable at all — a pre-fix venv reported 0.
if count < 1:
    raise SystemExit("error: no CUDA-visible device after ROCm wheel install")
PY
echo "ROCm wheel installed and GPU detected. Run \`uv run --no-sync uvicorn main:app --port 8002\` for GPU STT."
